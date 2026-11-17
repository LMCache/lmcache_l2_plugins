# Shared L2 server e2e

LMCache and pytest run as ordinary Python processes in the current environment.
The shared case starts a real `lmcache server` and uses CPU KV buffers through
LMCache dev's `ServerBenchClient`, without an inference engine or GPU. Shared
cases and the test runner do not invoke Docker or Compose.

## Layers

```text
tests/                         Ordinary UT and adapter tests
e2e/common_scripts/
  cases.py                     L2Backend contract and correctness assertions
  server.py                    LMCache process lifecycle and readiness
  run.sh                       Native pytest command and artifact locations
e2e/<plugin>/
  test_server_roundtrip.py      Backend fixture and shared case invocation
  service.sh                   Backend-specific start/logs/stop commands
  README.md                    Backend setup and prerequisites
```

Default `pytest` collects only `tests/`; e2e uses `e2e/pytest.ini`.

`L2Backend` supplies `adapter_config` (the server's `--l2-adapter` JSON),
`status_type` (its reported adapter type), and `exists(keys)` (an independent
backend probe returning one boolean per LMCache `ObjectKey`, in input order).
Vendor fixtures own SDK clients, credentials and storage-key encoding.

The shared case stores four chunks of deterministic two-layer KV, independently
confirms they reached L2, waits for asynchronous writes, clears L1 through HTTP
and checks its object count is zero, then retrieves into zeroed CPU buffers
and compares every chunk checksum.

## Prepare a native Python environment

Use Linux, Python 3.12, git and a C++ compiler, with enough memory to build
LMCache's CPU extensions. From the repository root (Autumn is the example
plugin; substitute the chosen plugin's extra):

```bash
python3.12 -m venv .venv-e2e
source .venv-e2e/bin/activate
python -m pip install uv
uv pip install torch --index-url https://download.pytorch.org/whl/cpu
LMCACHE_SRC=$(mktemp -d)
git clone https://github.com/LMCache/LMCache.git "$LMCACHE_SRC"
LMCACHE_REF=${LMCACHE_REF:-$(git ls-remote https://github.com/LMCache/LMCache.git refs/heads/dev | cut -f1)}
git -C "$LMCACHE_SRC" checkout "$LMCACHE_REF"
uv pip install -r "$LMCACHE_SRC/requirements/build.txt"
NO_GPU_EXT=1 MAX_JOBS=1 uv pip install --no-build-isolation "$LMCACHE_SRC"
uv pip install ".[autumn,test]" pytest-timeout
```

Start or configure the chosen backend as its README describes, then run:

```bash
bash e2e/common_scripts/run.sh e2e/<plugin>
```

With an existing backend, set the fixture's connection variables and run that
command directly; backend provisioning scripts are not part of the case.

## Add an L2 plugin

1. Provide an `L2Backend` fixture and invoke `assert_store_clear_retrieve` in
   `e2e/<plugin>/test_server_roundtrip.py`.
2. For CI, implement `e2e/<plugin>/service.sh` with `start`, `logs`, and `stop`.
   `start` waits for readiness and may write Bash `export` statements to
   `$E2E_ARTIFACTS/backend.env`; CI sources this file before running pytest.
   `logs` writes backend diagnostics to `$E2E_ARTIFACTS`; `stop` releases only
   test-owned resources and tolerates a partially failed startup.
3. Add the plugin name to the e2e job's `matrix.plugin` list. CI installs the
   matching package extra and runs all scripts on the GitHub runner.

Backend startup is entirely vendor-owned: native processes, Compose, or an
existing remote service can all be used. No Compose file or container image is
required by the shared interface. Only [Autumn's service script](../autumn/README.md)
currently uses Compose, exclusively for its storage cluster.

## CI and evidence

GitHub-hosted Ubuntu runners execute LMCache and pytest directly for all PRs
(including drafts), nightly at 02:17 Asia/Shanghai, published releases and
prereleases, and manual dispatch. Release runs test their tag. Each run records
exact plugin and LMCache dev revisions and installed package versions.

Artifacts include JUnit XML, LMCache logs and backend diagnostics as
`l2-server-e2e-<plugin>`. Local output defaults to `e2e-artifacts`;
`E2E_ARTIFACTS` overrides it. Cleanup and log collection run after test failure.

`lmcache bench l2` directly exercises an adapter; this case covers the real
server protocol, asynchronous store, L1 clear, L2 prefetch and retrieval.
