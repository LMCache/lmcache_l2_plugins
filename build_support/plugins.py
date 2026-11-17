# SPDX-License-Identifier: Apache-2.0
"""Discover plugin-local declarations shared by packaging and verification."""

# Standard
from dataclasses import dataclass
from pathlib import Path
import re
import tomllib


@dataclass(frozen=True)
class Plugin:
    name: str
    dependencies: list[str]
    imports: list[str]
    test_dependencies: list[str]

    @property
    def tests(self) -> Path:
        return Path("tests") / self.name


def strings(data: dict, key: str, *, default=None) -> list[str]:
    value = data.get(key, default)
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise ValueError(f"{key} must be a list of nonempty strings")
    return value


def load_plugins(root: Path) -> list[Plugin]:
    plugins = []
    extra_names = set()
    for directory in sorted((root / "lmcache_l2_plugins").iterdir()):
        if not directory.is_dir() or directory.name.startswith("_"):
            continue
        if not (directory / "__init__.py").is_file():
            continue
        name = directory.name
        if not re.fullmatch(r"[a-z][a-z0-9_]*", name) or name == "test":
            raise ValueError(f"Invalid or reserved plugin name: {name}")
        extra = re.sub(r"[-_.]+", "-", name)
        if extra in extra_names:
            raise ValueError(f"Duplicate normalized extra name: {extra}")
        extra_names.add(extra)
        manifest = directory / "plugin.toml"
        if not manifest.is_file():
            raise ValueError(f"Missing plugin declaration: {manifest}")
        with manifest.open("rb") as file:
            data = tomllib.load(file)
        verification = data.get("verification", {})
        if not isinstance(verification, dict):
            raise ValueError(f"{manifest}: verification must be a TOML table")
        if set(data) - {"dependencies", "verification"} or set(verification) - {
            "imports",
            "dependencies",
        }:
            raise ValueError(f"Unknown declaration fields in {manifest}")
        imports = strings(verification, "imports")
        if not imports or any(
            module != f"lmcache_l2_plugins.{name}"
            and not module.startswith(f"lmcache_l2_plugins.{name}.")
            for module in imports
        ):
            raise ValueError(f"{manifest}: imports must belong to this plugin")
        plugins.append(
            Plugin(
                name,
                strings(data, "dependencies"),
                imports,
                strings(verification, "dependencies", default=[]),
            )
        )
    if not plugins:
        raise ValueError("No plugin declarations found")
    return plugins


def optional_dependencies(root: Path) -> dict[str, list[str]]:
    return {
        "test": ["pytest"],
        **{plugin.name: plugin.dependencies for plugin in load_plugins(root)},
    }
