# SPDX-License-Identifier: Apache-2.0
"""Discover opt-in e2e coverage from the existing plugin inventory."""

# Standard
from pathlib import Path
import json

# First Party
from build_support.plugins import load_plugins


def e2e_plugins(root: Path) -> list[str]:
    """Return declared plugins with complete e2e entry points; reject partial ones."""
    declared = {plugin.name for plugin in load_plugins(root)}
    directory = root / ".github" / "e2e"
    if not directory.is_dir():
        return []
    backends = {
        path.name
        for path in directory.iterdir()
        if path.is_dir()
        and not path.name.startswith(("_", "."))
        and path.name != "common_scripts"
    }
    if unknown := backends - declared:
        raise ValueError(
            f"E2e directories have no plugin declaration: {sorted(unknown)}"
        )
    for name in sorted(backends):
        for path in (
            directory / "__init__.py",
            directory / name / "__init__.py",
            directory / name / "service.sh",
        ):
            if not path.is_file():
                raise ValueError(f"Missing e2e entry point: {path}")
        if not list((directory / name).rglob("test_*.py")):
            raise ValueError(f"No e2e cases found for {name}")
    return sorted(backends)


if __name__ == "__main__":
    print(json.dumps(e2e_plugins(Path.cwd())))
