#!/usr/bin/env bash
# Wait for the exact wheel on PyPI and check it matches the built artifact.
set -euo pipefail
project=$1
version=$2
index_url=${3:-https://pypi.org/simple}
mkdir -p published
for attempt in {1..12}; do
  if python -m pip download --no-cache-dir --no-deps --only-binary=:all: \
    --index-url "$index_url" --dest published "${project}==${version}"; then
    python - <<'PY'
from hashlib import sha256
from pathlib import Path

built, = Path('dist').glob('*.whl')
downloaded, = Path('published').glob('*.whl')
assert built.name == downloaded.name
assert sha256(built.read_bytes()).digest() == sha256(downloaded.read_bytes()).digest()
PY
    exit 0
  fi
  if [[ "$attempt" -lt 12 ]]; then sleep 15; fi
done
echo "::error::Published wheel did not become available on $index_url"
exit 1
