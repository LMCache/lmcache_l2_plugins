# SPDX-License-Identifier: Apache-2.0
"""Shared lifecycle helpers for a real LMCache server subprocess."""

# Standard
from collections.abc import Iterator
from pathlib import Path
import json
import signal
import socket
import subprocess

# Third Party
from e2e.common_scripts.cases import L2Backend, wait_until
import httpx
import pytest


@pytest.fixture
def lmcache_server(tmp_path: Path, l2_backend: L2Backend) -> Iterator[tuple[str, str]]:
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
        json.dumps(l2_backend.adapter_config),
    ]
    log_path = tmp_path / "lmcache-server.log"
    print(f"Server command: {command}")
    with log_path.open("w") as log:
        process = subprocess.Popen(
            command, cwd=tmp_path, stdout=log, stderr=subprocess.STDOUT
        )
    try:

        def ready() -> bool:
            assert process.poll() is None, log_path.read_text()
            try:
                return httpx.get(f"{http_url}/healthcheck", timeout=1).is_success
            except httpx.TransportError:
                return False

        wait_until(ready, "LMCache server readiness")
        yield f"grpc://127.0.0.1:{rpc_port}", http_url
    finally:
        if process.poll() is None:
            process.send_signal(signal.SIGINT)
        try:
            process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)
        print(f"LMCache server log ({log_path.name}):\n{log_path.read_text()}")
