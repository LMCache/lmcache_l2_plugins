# SPDX-License-Identifier: Apache-2.0
"""Exercise release guards and development version uniqueness without a build."""

# Standard
from pathlib import Path
import subprocess
import sys
import tomllib

# Third Party
import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "prepare_package.py"


def prepare(tmp_path, *args, version="0.1.0"):
    metadata = tmp_path / "pyproject.toml"
    metadata.write_text(
        f'[project]\nname = "lmcache-l2-plugins"\nversion = "{version}"\n'
    )
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    return result, tomllib.loads(metadata.read_text())["project"]


@pytest.mark.parametrize("version", ["0.1.0", "0.2.0rc1"])
def test_release_preserves_matching_version(tmp_path, version):
    result, project = prepare(tmp_path, "--tag", f"v{version}", version=version)
    assert result.returncode == 0, result.stderr
    assert project["version"] == version


@pytest.mark.parametrize("tag", ["v0.2.0", "0.1.0", "v0.1.0.dev1"])
def test_bad_release_tag_does_not_change_metadata(tmp_path, tag):
    result, project = prepare(tmp_path, "--tag", tag)
    assert result.returncode != 0
    assert project["version"] == "0.1.0"


def test_reruns_have_distinct_development_versions(tmp_path):
    versions = []
    for attempt in (1, 2):
        result, project = prepare(
            tmp_path, "--run-id", "12345", "--run-attempt", str(attempt)
        )
        assert result.returncode == 0, result.stderr
        assert project["name"] == "lmcache-l2-plugins"
        versions.append(project["version"])
    assert versions == ["0.1.0.dev12345001", "0.1.0.dev12345002"]
