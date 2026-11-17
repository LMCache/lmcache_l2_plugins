# SPDX-License-Identifier: Apache-2.0
"""Backend-independent correctness cases using the LMCache request protocol."""

# Future
from __future__ import annotations

# Standard
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING
import uuid

# Third Party
import httpx

# Local
from .server import server, wait_until

if TYPE_CHECKING:
    # Third Party
    from lmcache.v1.distributed.api import ObjectKey


@dataclass(frozen=True)
class L2Backend:
    """Vendor inputs for shared cases; probes receive LMCache object keys.

    ``exists`` must query the real backend independently of LMCache's L1.
    It returns one boolean per key, preserving input order.
    """

    adapter_config: dict[str, object]
    status_type: str
    exists: Callable[[list[ObjectKey]], list[bool]]


def assert_store_clear_retrieve(backend: L2Backend, tmp_path: Path) -> None:
    """Verify L2 writes and identical KV after clearing the real server's L1."""
    # Imported only when the case runs: unit jobs may use stable LMCache.
    # Third Party
    from lmcache.cli.commands.bench.server_bench.client import ServerBenchClient
    from lmcache.cli.commands.bench.server_bench.config import BenchConfig
    from lmcache.v1.common.token_hasher import TokenHasher
    from lmcache.v1.distributed.api import ObjectKey

    # Random token prefix prevents hits left by another run on an existing cluster.
    tokens = [uuid.uuid4().int % (2**31)] + list(range(1, 64))
    hashes = TokenHasher(chunk_size=16, hash_algorithm="blake3").compute_chunk_hashes(
        tokens
    )
    rank = ObjectKey.ComputeKVRank(1, 0, 1, 0)
    keys = [
        ObjectKey(chunk_hash=h, model_name="test-model", kv_rank=rank) for h in hashes
    ]
    assert backend.exists(keys) == [False] * 4

    with (
        server(tmp_path, backend.adapter_config) as (rpc_url, http_url),
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
                lambda: backend.exists(keys) == [True] * 4,
                "all four chunks to exist in L2",
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
            assert before["l2_adapters"][0]["type"] == backend.status_type
            print("Verified: all four chunks reached the real L2 backend")
            response = http.post("/cache/clear", json={"tier": "l1", "force": False})
            response.raise_for_status()
            assert response.json()["status"] == "ok"
            assert storage_status()["l1_manager"]["total_object_count"] == 0
            assert backend.exists(keys) == [True] * 4

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
            print("Verified: empty L1 -> L2 -> CPU KV; all chunk checksums match")
        finally:
            client.close()
