#!/usr/bin/env bash
# Shared in-container runner; each vendor overlay selects its own test directory.
set -euo pipefail
exec python -m pytest -c e2e/pytest.ini -v -s --timeout=180 \
  --junitxml=/artifacts/junit.xml --basetemp=/artifacts/pytest \
  "${E2E_TEST_PATH:?Set the vendor e2e test directory}" "$@"
