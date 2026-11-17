#!/usr/bin/env bash
# Run shared correctness cases using the current Python environment.
set -euo pipefail
if (( $# == 0 )); then
  echo "Usage: $0 .github/e2e/<plugin> [pytest options]" >&2
  exit 2
fi
artifact_dir="${E2E_ARTIFACTS:-e2e-artifacts}"
mkdir -p "$artifact_dir"
export LMCACHE_TRACK_USAGE=false DO_NOT_TRACK=1
exec python -m pytest -c .github/e2e/pytest.ini -v -s --timeout=180 \
  --junitxml="$artifact_dir/junit.xml" --basetemp="$artifact_dir/pytest" "$@"
