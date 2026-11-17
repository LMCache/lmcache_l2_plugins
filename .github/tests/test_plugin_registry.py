# SPDX-License-Identifier: Apache-2.0
"""New plugin files must participate without edits to shared configuration."""

# Standard
from email.parser import BytesParser
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import zipfile

# Third Party
import pytest

# First Party
from build_support.plugins import load_plugins, optional_dependencies
from build_support.verify_package import verify

ROOT = Path(__file__).resolve().parents[2]


def add_plugin(root, name, *, dependency="", test_dependency=""):
    directory = root / "lmcache_l2_plugins" / name
    directory.mkdir(parents=True)
    (directory / "__init__.py").write_text("")
    dependencies = [dependency] if dependency else []
    test_dependencies = [test_dependency] if test_dependency else []
    (directory / "plugin.toml").write_text(
        f"dependencies = {dependencies!r}\n[verification]\n"
        f'imports = ["lmcache_l2_plugins.{name}"]\n'
        f"dependencies = {test_dependencies!r}\n"
    )
    tests = root / "tests" / name
    tests.mkdir(parents=True)
    (tests / "test_import.py").write_text(f"import lmcache_l2_plugins.{name}\n")


def test_new_plugin_is_discovered_without_registry_edits(tmp_path):
    add_plugin(tmp_path, "alpha", dependency="client-a>=1")
    add_plugin(
        tmp_path, "beta", dependency="client-b>=2", test_dependency="pytest-asyncio"
    )
    assert optional_dependencies(tmp_path) == {
        "test": ["pytest"],
        "alpha": ["client-a>=1"],
        "beta": ["client-b>=2"],
    }
    plugins = load_plugins(tmp_path)
    assert [plugin.name for plugin in plugins] == ["alpha", "beta"]
    assert plugins[1].test_dependencies == ["pytest-asyncio"]


def test_undeclared_plugin_cannot_be_silently_skipped(tmp_path):
    add_plugin(tmp_path, "alpha")
    (tmp_path / "lmcache_l2_plugins/alpha/plugin.toml").unlink()
    with pytest.raises(ValueError, match="Missing plugin declaration"):
        load_plugins(tmp_path)


def test_missing_tests_fail_before_installation(tmp_path):
    add_plugin(tmp_path, "alpha")
    shutil.rmtree(tmp_path / "tests")
    with pytest.raises(ValueError, match="No tests found for plugin alpha"):
        verify(tmp_path, "lmcache-l2-plugins", "0.1.0", tmp_path)


def test_normalized_extra_collisions_are_rejected(tmp_path):
    add_plugin(tmp_path, "alpha_beta")
    add_plugin(tmp_path, "alpha__beta")
    with pytest.raises(ValueError, match="Duplicate normalized extra name"):
        load_plugins(tmp_path)


def test_new_plugins_survive_sdist_and_generate_wheel_extras(tmp_path):
    # Only new plugin/test files distinguish the two-plugin project from a
    # clean project. Rebuild its sdist to exercise the release build path.
    for name in ("setup.py", "pyproject.toml", "MANIFEST.in", "README.md", "LICENSE"):
        shutil.copy(ROOT / name, tmp_path / name)
    shutil.copytree(ROOT / "build_support", tmp_path / "build_support")
    (tmp_path / "lmcache_l2_plugins").mkdir()
    (tmp_path / "lmcache_l2_plugins/__init__.py").write_text("")
    add_plugin(tmp_path, "alpha", dependency="client-a>=1")
    add_plugin(tmp_path, "beta", dependency="client-b>=2")
    result = subprocess.run(
        [sys.executable, "-m", "build", "--no-isolation"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    (sdist,) = (tmp_path / "dist").glob("*.tar.gz")
    with tarfile.open(sdist) as archive:
        names = archive.getnames()
    assert any(name.endswith("/build_support/plugins.py") for name in names)
    assert sum(name.endswith("/plugin.toml") for name in names) == 2
    (wheel,) = (tmp_path / "dist").glob("*.whl")
    with zipfile.ZipFile(wheel) as archive:
        (metadata,) = [
            name for name in archive.namelist() if name.endswith(".dist-info/METADATA")
        ]
        data = BytesParser().parsebytes(archive.read(metadata))
    assert set(data.get_all("Provides-Extra")) == {"test", "alpha", "beta"}
    assert any(
        'client-a>=1; extra == "alpha"' == value
        for value in data.get_all("Requires-Dist")
    )
    assert any(
        'client-b>=2; extra == "beta"' == value
        for value in data.get_all("Requires-Dist")
    )
