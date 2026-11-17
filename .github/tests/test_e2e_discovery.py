# SPDX-License-Identifier: Apache-2.0
"""New plugins opt into e2e using files, without a second central list."""

# Standard
from pathlib import Path

# Third Party
import pytest

# First Party
from build_support.e2e import e2e_plugins


def add_plugin(root: Path, name: str, *, live: bool) -> None:
    package = root / "lmcache_l2_plugins" / name
    package.mkdir(parents=True)
    (package / "__init__.py").touch()
    (package / "plugin.toml").write_text(
        f'dependencies = []\n[verification]\nimports = ["lmcache_l2_plugins.{name}"]\n'
    )
    if live:
        backend = root / "e2e" / name
        backend.mkdir(parents=True)
        (backend.parent / "__init__.py").touch()
        (backend / "__init__.py").touch()
        (backend / "service.sh").write_text("#!/bin/bash\nexit 0\n")
        (backend / "test_server_roundtrip.py").write_text("def test_backend(): pass\n")


def test_new_backend_is_discovered_without_compose_or_registry_edits(tmp_path):
    add_plugin(tmp_path, "alpha", live=True)
    add_plugin(tmp_path, "beta", live=True)
    add_plugin(tmp_path, "unit_only", live=False)
    assert e2e_plugins(tmp_path) == ["alpha", "beta"]


def test_partial_backend_is_an_error_instead_of_silently_skipping(tmp_path):
    add_plugin(tmp_path, "alpha", live=True)
    (tmp_path / "e2e/alpha/service.sh").unlink()
    with pytest.raises(ValueError, match="service.sh"):
        e2e_plugins(tmp_path)


def test_unit_only_plugin_does_not_create_an_empty_matrix_job(tmp_path):
    add_plugin(tmp_path, "unit_only", live=False)
    assert e2e_plugins(tmp_path) == []


def test_undeclared_backend_is_an_error(tmp_path):
    add_plugin(tmp_path, "alpha", live=True)
    (tmp_path / "e2e/typo").mkdir()
    with pytest.raises(ValueError, match="typo"):
        e2e_plugins(tmp_path)
