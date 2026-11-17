# SPDX-License-Identifier: Apache-2.0
"""Autumn-specific inputs for the shared LMCache server round-trip case."""

# Future
from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
import os
import socket

# Third Party
from e2e.common_scripts.cases import L2Backend, assert_store_clear_retrieve
import pytest

if TYPE_CHECKING:
    # Third Party
    from lmcache.v1.distributed.api import ObjectKey


@pytest.fixture
def l2_backend() -> L2Backend:
    """Configure the Autumn plugin and an independent key-existence probe."""
    manager = os.environ.get("AUTUMN_MANAGER")
    if not manager:
        pytest.skip("Set AUTUMN_MANAGER; see docs/source/developer_guide/e2e/autumn.md")

    # Third Party
    from lmcache.v1.distributed.key_codec import encode_storage_key
    import autumn

    host, port = manager.rsplit(":", 1)
    manager = f"{socket.gethostbyname(host)}:{port}"
    namespace = os.environ.get("AUTUMN_NAMESPACE", "kvc")
    client = autumn.BatchClient(manager, scope=namespace)

    def exists(keys: list[ObjectKey]) -> list[bool]:
        storage_keys = [
            f"{key.chunk_hash.hex()[0]}/lmcache/{encode_storage_key(key)}".encode()
            for key in keys
        ]
        return client.exists(storage_keys)

    return L2Backend(
        adapter_config={
            "type": "plugin",
            "module_path": "lmcache_l2_plugins.autumn",
            "class_name": "AutumnL2Adapter",
            "adapter_params": {
                "manager": manager,
                "namespace": namespace,
                "transport": "tcp",
            },
        },
        status_type="autumn",
        exists=exists,
    )


def test_server_roundtrip(
    l2_backend: L2Backend, lmcache_server: tuple[str, str]
) -> None:
    """Run the shared store/clear/retrieve case against real Autumn storage."""
    assert_store_clear_retrieve(l2_backend, lmcache_server)
