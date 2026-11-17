# SPDX-License-Identifier: Apache-2.0
"""Derive extras from plugin declarations without importing plugin code."""

# Standard
from pathlib import Path
import runpy

# Third Party
from setuptools import setup

# setuptools executes setup.py without guaranteeing the source root is on
# sys.path. Load only the build helper, never the runtime plugin package.
root = Path(__file__).resolve().parent
declarations = runpy.run_path(str(root / "build_support/plugins.py"))
setup(extras_require=declarations["optional_dependencies"](root))
