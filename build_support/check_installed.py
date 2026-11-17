# SPDX-License-Identifier: Apache-2.0
"""Check distribution identity and plugin imports outside the source checkout."""

# Standard
from importlib.metadata import distribution
from pathlib import Path
import importlib
import re
import sys

project, expected_version, checkout, plugin, *modules = sys.argv[1:]
installed = distribution(project)
assert installed.version == expected_version
assert re.sub(r"[-_.]+", "-", plugin) in installed.metadata.get_all(
    "Provides-Extra", []
)
for name in ["lmcache_l2_plugins", *modules]:
    module = importlib.import_module(name)
    assert not Path(module.__file__).resolve().is_relative_to(Path(checkout))
