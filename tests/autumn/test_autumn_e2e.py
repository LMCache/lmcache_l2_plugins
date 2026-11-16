# SPDX-License-Identifier: Apache-2.0
"""
End-to-end test: an LMCache server with the autumn L2 adapter, driven by the
``lmcache bench server`` client.

KV chunks are stored, L1 is cleared, and the same requests are looked up and
retrieved again. They can only come back from autumn, so the test checks
them chunk by chunk against what was stored, and checks the server's own
counters that every hit came from L2 and none from L1. It prints the L2 read
throughput; it does not judge it.

The cluster comes from one of:

* ``AUTUMN_COMPOSE_FILE``: autumn-rs's ``deploy/compose/docker-compose.yml``.
  The test starts the cluster, runs against it and removes it with its
  volumes. The host must reach the containers' addresses (Linux bridge).
* ``AUTUMN_MANAGER`` (``ip:port``): a running cluster whose namespace
  (``AUTUMN_NAMESPACE``, default ``kvc``) exists, with
  ``AUTUMN_CREDENTIAL_FILE`` if authz is on. Each run leaves its chunks there
  (512 MiB by default, no TTL).

``AUTUMN_TRANSPORT`` (``tcp``/``ucx``) and ``AUTUMN_E2E_SEQUENCES`` (8, each
64 MiB of KV; keep the total under the 2 GiB L1) apply to both.

Without either, the test is skipped. The LMCache server and the bench client
run on CPU; no GPU is needed.

    AUTUMN_COMPOSE_FILE=~/autumn-rs/deploy/compose/docker-compose.yml \\
        pytest -s tests/autumn/test_autumn_e2e.py
"""

# Standard
import json
import os
import random
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.request

# Third Party
import pytest

COMPOSE_FILE = os.environ.get("AUTUMN_COMPOSE_FILE", "")
MANAGER = os.environ.get("AUTUMN_MANAGER", "")

pytestmark = pytest.mark.skipif(
    not (COMPOSE_FILE or MANAGER),
    reason="set AUTUMN_COMPOSE_FILE or AUTUMN_MANAGER to run the e2e test",
)

NUM_SEQUENCES = int(os.environ.get("AUTUMN_E2E_SEQUENCES", "8"))
NUM_TOKENS = 512
# The bench's default KV layout: 32 layers of [K/V, blocks, block, heads, dim].
SHAPE_SPEC = "(2,1024,16,8,128):float16:32"
# Its own project, so the test never adopts or wipes another stack of the
# same compose file.
PROJECT = "autumn-l2-e2e-%d" % os.getpid()
COUNTERS = (
    "l2_store_completed_objects_chunks_total",
    "lookup_hit_l1_tokens_total",
    "lookup_hit_l2_tokens_total",
    "l2_prefetch_load_completed_chunks_total",
)


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_until(check, timeout: float, what: str) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if check():
            return
        time.sleep(1)
    raise TimeoutError(what)


def _run(*cmd: str) -> str:
    out = subprocess.run(cmd, capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError("%s failed:\n%s" % (" ".join(cmd), out.stderr))
    return out.stdout


def _compose(*args: str) -> str:
    return _run("docker", "compose", "-p", PROJECT, "-f", COMPOSE_FILE, *args)


def _bootstrap_done() -> bool:
    state = _compose("ps", "-a", "--format", "{{.Service}} {{.State}} {{.ExitCode}}")
    # A failed bootstrap restarts (restart: on-failure); only a clean exit
    # means it is done.
    return "bootstrap exited 0" in state.splitlines()


@pytest.fixture(scope="module")
def manager():
    if not COMPOSE_FILE:
        yield MANAGER
        return
    try:
        _compose("up", "-d")
        # Bootstrap exits once the PS serves and the namespaces exist.
        _wait_until(_bootstrap_done, 300, "the compose cluster did not bootstrap")
        container = _compose("ps", "-q", "manager").strip()
        ips = _run(
            "docker",
            "inspect",
            "-f",
            "{{range .NetworkSettings.Networks}}{{.IPAddress}} {{end}}",
            container,
        ).split()
        yield "%s:9001" % ips[0]
    finally:
        _compose("down", "-v")


@pytest.fixture(scope="module")
def lmcache_server(manager, tmp_path_factory):
    rpc_port, http_port = _free_port(), _free_port()
    adapter = {
        "type": "plugin",
        "module_path": "lmcache_l2_plugins.autumn",
        "class_name": "AutumnL2Adapter",
        "adapter_params": {
            "manager": manager,
            "namespace": os.environ.get("AUTUMN_NAMESPACE", "kvc"),
            "credential_file": os.environ.get("AUTUMN_CREDENTIAL_FILE", ""),
            "transport": os.environ.get("AUTUMN_TRANSPORT", "tcp"),
        },
    }
    log = tmp_path_factory.mktemp("lmcache") / "server.log"
    # Without a visible GPU the server takes the CPU transfer path.
    env = dict(os.environ, CUDA_VISIBLE_DEVICES="")
    with open(log, "w") as out:
        proc = subprocess.Popen(
            [
                shutil.which("lmcache")
                or os.path.join(os.path.dirname(sys.executable), "lmcache"),
                "server",
                "--port",
                str(rpc_port),
                "--http-host",
                "127.0.0.1",
                "--http-port",
                str(http_port),
                "--l1-size-gb",
                "2",
                "--eviction-policy",
                "LRU",
                "--l2-adapter",
                json.dumps(adapter),
            ],
            stdout=out,
            stderr=subprocess.STDOUT,
            env=env,
        )
    http_url = "http://127.0.0.1:%d" % http_port

    def healthy() -> bool:
        if proc.poll() is not None:
            raise RuntimeError("lmcache server exited:\n" + log.read_text())
        try:
            urllib.request.urlopen(http_url + "/healthcheck", timeout=2)
            return True
        except OSError:
            return False

    try:
        _wait_until(healthy, 120, "lmcache server did not come up")
        yield "tcp://127.0.0.1:%d" % rpc_port, http_url
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()


def _counter(metrics: str, name: str, required: bool) -> float:
    """Sum of every series of ``name``, whatever its labels."""
    pattern = re.compile(r"^%s(?:\{[^}]*\})? (\S+)$" % re.escape(name), re.M)
    values = pattern.findall(metrics)
    # A counter appears once first used; after the run every one must be
    # there, or a renamed metric would read as a passing 0.
    assert values or not required, "no %s in /metrics" % name
    return sum(float(v) for v in values)


def _counters(http_url: str, required: bool = False) -> dict[str, float]:
    metrics = urllib.request.urlopen(http_url + "/metrics").read().decode()
    return {
        name: _counter(metrics, "lmcache_mp_" + name, required) for name in COUNTERS
    }


def _token_ids(seq: int) -> list[int]:
    # The sequence number first, so every sequence has its own chunk keys.
    return [seq] + [7] * NUM_TOKENS


def _bytes_per_token(spec: str) -> int:
    """KV bytes per token of a ``(2,NB,BS,NH,HS):dtype:layers[;...]`` spec."""
    # Third Party
    import torch

    total = 0
    for group in spec.split(";"):
        dims, dtype, layers = group.rsplit(":", 2)
        shape = [int(d) for d in dims.strip("()").split(",")]
        per_layer = shape[0] * shape[3] * shape[4] * getattr(torch, dtype).itemsize
        total += per_layer * int(layers)
    return total


def _clear_l1(http_url: str) -> None:
    req = urllib.request.Request(
        http_url + "/cache/clear",
        data=json.dumps({"tier": "l1", "force": True}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    urllib.request.urlopen(req)


def test_chunks_cleared_from_l1_are_read_back_from_autumn(lmcache_server):
    assert NUM_SEQUENCES > 0
    # Third Party
    from lmcache.cli.commands.bench.server_bench.client import ServerBenchClient
    from lmcache.cli.commands.bench.server_bench.config import BenchConfig

    rpc_url, http_url = lmcache_server
    config = BenchConfig(
        rpc_url=rpc_url,
        http_url=http_url,
        mode="cpu",
        transfer_mode="lmcache_driven",
        tp_size=1,
        use_mla=False,
        num_tokens=NUM_TOKENS,
        kvcache_shape_spec=SHAPE_SPEC,
        num_blocks=1024,
        block_size=16,
    )
    client = ServerBenchClient(config, lambda msg: None, client_index=0)
    client.start()
    try:
        # Fresh token ids per run, so chunks left in L2 by an earlier run
        # cannot answer a lookup.
        first = random.randrange(1 << 30)
        sequences = range(first, first + NUM_SEQUENCES)

        start = _counters(http_url)
        stored = {}
        store_ms = 0.0
        for seq in sequences:
            req = client.create_request(
                seq,
                request_id="store-%d" % seq,
                request_kind="cold",
                token_ids=_token_ids(seq),
            )
            lookup = client.lookup(req)
            assert lookup.succeeded and lookup.is_full_miss, seq
            client.fill_deterministic_kv(req)
            stored[seq] = client.compute_checksums(
                req, start_token=0, token_count=req.num_full_tokens, operation="store"
            )
            result = client.store(req, start_token=0, token_count=req.num_full_tokens)
            assert result.succeeded, seq
            assert stored[seq], "no checksums to compare against"
            store_ms += result.latency_ms
            tokens = req.num_full_tokens
            chunks_per_seq = tokens // req.chunk_size
            client.release_request(req)

        # A store returns once L1 holds the chunks; the write to L2 follows.
        # Clearing L1 before it lands would drop chunks L2 never got.
        def in_l2() -> bool:
            done = _counters(http_url)["l2_store_completed_objects_chunks_total"]
            return done - start["l2_store_completed_objects_chunks_total"] >= (
                NUM_SEQUENCES * chunks_per_seq
            )

        _wait_until(in_l2, 120, "stored chunks did not all reach L2")
        _clear_l1(http_url)
        before = _counters(http_url)

        read_ms = 0.0
        for seq in sequences:
            req = client.create_request(
                seq,
                request_id="read-%d" % seq,
                request_kind="warm",
                token_ids=_token_ids(seq),
            )
            lookup = client.lookup(req)
            assert lookup.succeeded and lookup.is_full_hit, seq
            client.zero_destination(req, start_token=0, token_count=tokens)
            result = client.retrieve(req, start_token=0, token_count=tokens)
            assert result.succeeded, seq
            read_ms += lookup.latency_ms + result.latency_ms
            got = client.compute_checksums(
                req, start_token=0, token_count=tokens, operation="retrieve"
            )
            assert got == stored[seq], "seq %d read back different bytes" % seq
            client.release_request(req)
    finally:
        client.close()

    after = _counters(http_url, required=True)
    delta = {k: after[k] - before[k] for k in after}
    assert delta["lookup_hit_l1_tokens_total"] == 0, delta
    assert delta["lookup_hit_l2_tokens_total"] == NUM_SEQUENCES * tokens, delta
    assert (
        delta["l2_prefetch_load_completed_chunks_total"]
        == NUM_SEQUENCES * chunks_per_seq
    ), delta

    # Reported, not asserted: it depends on the cluster and the host.
    mib = NUM_SEQUENCES * tokens * _bytes_per_token(SHAPE_SPEC) / 2**20
    print(
        "\nautumn L2 e2e: %d sequences, %.0f MiB of KV; store into L1 %.0f ms "
        "(%.0f MiB/s), lookup+retrieve from L2 %.0f ms (%.0f MiB/s)"
        % (
            NUM_SEQUENCES,
            mib,
            store_ms,
            mib / store_ms * 1000,
            read_ms,
            mib / read_ms * 1000,
        )
    )
