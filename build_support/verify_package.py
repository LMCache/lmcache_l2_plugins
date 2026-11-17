# SPDX-License-Identifier: Apache-2.0
"""Verify every declared plugin against a distribution in isolated environments."""

# Standard
from pathlib import Path
from tempfile import TemporaryDirectory
import argparse
import os
import shutil
import subprocess
import sys
import tomllib

# First Party
from build_support.plugins import load_plugins


def verify(distribution: Path, project: str, version: str, root: Path) -> None:
    plugins = load_plugins(root)
    # Check the complete inventory before installing anything. A new plugin
    # must never silently miss the common validation gate.
    for plugin in plugins:
        if not list((root / plugin.tests).rglob("test_*.py")):
            raise ValueError(f"No tests found for plugin {plugin.name}: {plugin.tests}")
    for plugin in plugins:
        print(f"Verifying {plugin.name}: {distribution.name}", flush=True)
        with TemporaryDirectory(prefix=f"verify-{plugin.name}-") as directory:
            scratch = Path(directory)
            subprocess.run(
                [sys.executable, "-m", "venv", str(scratch / "venv")], check=True
            )
            python = str(scratch / "venv/bin/python")
            subprocess.run(
                [python, "-m", "pip", "install", "--quiet", "--upgrade", "pip", "uv"],
                check=True,
            )
            uv = [str(scratch / "venv/bin/uv"), "pip", "install", "--python", python]
            subprocess.run(
                [*uv, "torch", "--index-url", "https://download.pytorch.org/whl/cpu"],
                check=True,
            )
            subprocess.run(
                [
                    *uv,
                    f"{project}[{plugin.name},test] @ {distribution.as_uri()}",
                    *plugin.test_dependencies,
                ],
                env={**os.environ, "NO_GPU_EXT": "1"},
                check=True,
            )
            subprocess.run([python, "-m", "pip", "check"], check=True)
            shutil.copytree(root / plugin.tests, scratch / "tests" / plugin.name)
            subprocess.run(
                [
                    python,
                    "-I",
                    str(root / "build_support/check_installed.py"),
                    project,
                    version,
                    str(root),
                    plugin.name,
                    *plugin.imports,
                ],
                cwd=scratch,
                check=True,
            )
            subprocess.run(
                [
                    python,
                    "-I",
                    "-m",
                    "pytest",
                    "--import-mode=importlib",
                    "-q",
                    "-rs",
                    "tests",
                ],
                cwd=scratch,
                check=True,
            )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "distribution",
        type=Path,
        help="wheel, source distribution, or source directory",
    )
    parser.add_argument("project", nargs="?", default="lmcache-l2-plugins")
    parser.add_argument("version", nargs="?")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    version = args.version
    if version is None:
        if args.distribution.resolve() != root:
            parser.error("expected version is required for built distributions")
        version = tomllib.loads((root / "pyproject.toml").read_text())["project"][
            "version"
        ]
    verify(args.distribution.resolve(), args.project, version, root)


if __name__ == "__main__":
    main()
