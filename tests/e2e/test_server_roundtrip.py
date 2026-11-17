# SPDX-License-Identifier: Apache-2.0
"""Real LMCache server -> Autumn -> empty L1 -> CPU worker round trip."""

# Standard
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
import json
import os
import signal
import socket
import subprocess
import time
import uuid

# Third Party
import httpx
import pytest


def wait_until(check: Callable[[], bool], description: str) -> None:
    """Poll a bounded condition, preserving assertion failures as diagnostics."""
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        if check():
            return
        time.sleep(0.1)
    raise AssertionError(f"Timed out waiting for {description}")


@contextmanager
def server(tmp_path: Path, adapter: dict) -> Iterator[tuple[str, str]]:
    """Run the installed CLI and stop its owned process before returning."""
    with socket.socket() as rpc, socket.socket() as http:
        rpc.bind(("127.0.0.1", 0))
        http.bind(("127.0.0.1", 0))
        rpc_port = rpc.getsockname()[1]
        http_port = http.getsockname()[1]
    http_url = f"http://127.0.0.1:{http_port}"
    command = [
        "lmcache",
        "server",
        "--host",
        "127.0.0.1",
        "--port",
        str(rpc_port),
        "--http-port",
        str(http_port),
        "--supported-transfer-mode",
        "engine_driven",
        "--chunk-size",
        "16",
        "--hash-algorithm",
        "blake3",
        "--l1-size-gb",
        "0.0625",
        "--eviction-policy",
        "LRU",
        "--l2-adapter",
        json.dumps(adapter),
    ]
    log_path = tmp_path / "lmcache-server.log"
    print(f"Server command: {command}")
    with log_path.open("w") as log:
        process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
    try:

        def ready() -> bool:
            assert process.poll() is None, log_path.read_text()
            try:
                return httpx.get(f"{http_url}/healthcheck", timeout=1).is_success
            except httpx.TransportError:
                return False

        wait_until(ready, "LMCache server readiness")
        yield f"tcp://127.0.0.1:{rpc_port}", http_url
    finally:
        if process.poll() is None:
            process.send_signal(signal.SIGINT)
        try:
            process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)
        print(f"LMCache server log ({log_path.name}):\n{log_path.read_text()}")


def test_server_autumn_roundtrip(tmp_path: Path) -> None:
    """Require actual L2 persistence and identical KV after clearing L1."""
    manager = os.environ.get("AUTUMN_MANAGER")
    if not manager:
        pytest.skip("Use tests/e2e/compose.yaml or set AUTUMN_MANAGER")

    # Imported only for the live test: ordinary unit jobs may use stable LMCache.
    # Third Party
    from lmcache.cli.commands.bench.server_bench.client import ServerBenchClient
    from lmcache.cli.commands.bench.server_bench.config import BenchConfig
    from lmcache.v1.common.token_hasher import TokenHasher
    from lmcache.v1.distributed.api import ObjectKey
    from lmcache.v1.distributed.key_codec import encode_storage_key
    import autumn

    host, port = manager.rsplit(":", 1)
    manager = f"{socket.gethostbyname(host)}:{port}"
    namespace = os.environ.get("AUTUMN_NAMESPACE", "kvc")
    params = {"manager": manager, "namespace": namespace, "transport": "tcp"}
    adapter = {
        "type": "plugin",
        "module_path": "lmcache_l2_plugins.autumn",
        "class_name": "AutumnL2Adapter",
        "adapter_params": params,
    }
    # Random token prefix prevents hits left by another run on an existing cluster.
    tokens = [uuid.uuid4().int % (2**31)] + list(range(1, 64))
    hashes = TokenHasher(chunk_size=16, hash_algorithm="blake3").compute_chunk_hashes(
        tokens
    )
    rank = ObjectKey.ComputeKVRank(1, 0, 1, 0)
    keys = [
        ObjectKey(chunk_hash=h, model_name="test-model", kv_rank=rank) for h in hashes
    ]
    backend_keys = [
        f"{key.chunk_hash.hex()[0]}/lmcache/{encode_storage_key(key)}".encode()
        for key in keys
    ]
    backend = autumn.BatchClient(manager, scope=namespace)
    assert backend.exists(backend_keys) == [False] * 4

    with (
        server(tmp_path, adapter) as (rpc_url, http_url),
        httpx.Client(base_url=http_url, timeout=10) as http,
    ):

        def storage_status() -> dict:
            response = http.get("/status")
            response.raise_for_status()
            return response.json()["storage_manager"]

        config = BenchConfig(
            rpc_url=rpc_url,
            http_url=http_url,
            mode="cpu",
            transfer_mode="engine_driven",
            tp_size=1,
            use_mla=False,
            num_tokens=64,
            kvcache_shape_spec="(2,16,16,1,8):float16:2",
            num_blocks=16,
            block_size=16,
        )
        client = ServerBenchClient(config, print)
        client.start()
        try:
            request = client.create_request(
                0, uuid.uuid4().hex, "store", token_ids=tokens
            )
            assert request is not None
            assert client.lookup(request).is_full_miss
            client.fill_deterministic_kv(request)
            expected = client.compute_checksums(request, 0, 64, operation="store")
            assert expected is not None
            result = client.store(request, 0, 64)
            assert result is not None and result.succeeded
            client.release_request(request)

            # STORE acknowledges L1 first. Probe the real backend, then wait for
            # controller completion before clearing buffers used by async writes.
            wait_until(
                lambda: backend.exists(backend_keys) == [True] * 4,
                "all four chunks to exist in Autumn",
            )

            def stores_finished() -> bool:
                state = storage_status()["store_controller"]
                return (
                    state["pending_keys_count"] == 0
                    and state["in_flight_task_count"] == 0
                )

            wait_until(stores_finished, "L2 stores to drain")
            before = storage_status()
            assert before["l1_manager"]["total_object_count"] == 4
            assert before["l2_adapters"][0]["type"] == "autumn"
            print("Verified: all four chunks reached the real Autumn backend")
            response = http.post("/cache/clear", json={"tier": "l1", "force": False})
            response.raise_for_status()
            assert response.json()["status"] == "ok"
            assert storage_status()["l1_manager"]["total_object_count"] == 0
            assert backend.exists(backend_keys) == [True] * 4

            request = client.create_request(
                1, uuid.uuid4().hex, "load", token_ids=tokens
            )
            assert request is not None
            client.zero_destination(request, 0, 64)
            assert (
                client.compute_checksums(request, 0, 64, operation="retrieve")
                != expected
            )
            assert client.lookup(request).is_full_hit
            result = client.retrieve(request, 0, 64)
            assert result is not None and result.succeeded
            actual = client.compute_checksums(request, 0, 64, operation="retrieve")
            assert actual == expected
            client.release_request(request)
            print("Verified: empty L1 -> Autumn -> CPU KV; all chunk checksums match")
        finally:
            client.close()
