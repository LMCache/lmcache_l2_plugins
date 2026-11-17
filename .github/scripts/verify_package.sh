#!/usr/bin/env bash
# Install a wheel or sdist in a fresh environment, outside the source tree.
set -euo pipefail
distribution=$(realpath "$1")
project=$2
version=$3
repo=$(pwd)
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT
python -m venv "$scratch/venv"
python_bin="$scratch/venv/bin/python"
"$python_bin" -m pip install --quiet --upgrade pip
"$python_bin" -m pip install --quiet torch --index-url https://download.pytorch.org/whl/cpu
NO_GPU_EXT=1 "$python_bin" -m pip install --quiet "${project}[autumn,test] @ file://${distribution}"
"$python_bin" -m pip check
cp -R tests "$scratch/tests"
cd "$scratch"
"$python_bin" -I - "$project" "$version" "$repo" <<'PY'
from importlib.metadata import version
from pathlib import Path
import sys

import lmcache_l2_plugins
from lmcache_l2_plugins.autumn import AutumnL2Adapter, AutumnL2AdapterConfig

assert version(sys.argv[1]) == sys.argv[2]
assert not Path(lmcache_l2_plugins.__file__).is_relative_to(Path(sys.argv[3]))
assert AutumnL2Adapter and AutumnL2AdapterConfig
PY
"$python_bin" -I -m pytest --import-mode=importlib -q -rs tests
