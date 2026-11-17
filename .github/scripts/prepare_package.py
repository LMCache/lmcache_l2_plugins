# SPDX-License-Identifier: Apache-2.0
"""Validate release tags or stamp a development distribution."""

# Standard
from pathlib import Path
import argparse
import re
import tomllib

# Third Party
from packaging.version import Version

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--tag")
parser.add_argument("--run-id", type=int)
parser.add_argument("--run-attempt", type=int)
args = parser.parse_args()
path = Path("pyproject.toml")
source = path.read_text()
project = tomllib.loads(source)["project"]
if project["name"] != "lmcache-l2-plugins":
    parser.error("unexpected distribution name")
if args.tag:
    if any(x is not None for x in (args.run_id, args.run_attempt)):
        parser.error("release and development arguments are mutually exclusive")
    if not re.fullmatch(r"v\d+\.\d+\.\d+(?:(?:a|b|rc)\d+)?", args.tag):
        parser.error("expected vMAJOR.MINOR.PATCH, optionally with a/b/rc suffix")
    if args.tag[1:] != project["version"]:
        parser.error("release tag must exactly match project.version")
    version = project["version"]
else:
    if not all(x is not None and x > 0 for x in (args.run_id, args.run_attempt)):
        parser.error("positive run ID and run attempt are required")
    if args.run_attempt >= 1000:
        parser.error("run attempt must be below 1000")
    base = Version(project["version"])
    if base.is_devrelease or base.local or base.is_postrelease:
        parser.error("project.version must be a stable or prerelease version")
    version = f"{base}.dev{args.run_id}{args.run_attempt:03d}"
    source, count = re.subn(
        r'^version = "[^"]+"$',
        f'version = "{version}"',
        source,
        flags=re.MULTILINE,
    )
    if count != 1:
        parser.error("expected exactly one static project version")
    path.write_text(source)
assert str(Version(version)) == version
print(version)
