# Shared L2 server e2e

The shared case starts a real `lmcache server` and uses CPU KV buffers through
LMCache dev's `ServerBenchClient`. It needs no inference engine, model, CUDA,
or GPU. Backend implementations supply their differences under
`e2e/<plugin>/`.

## Layers

Ordinary tests live in `tests/` and end-to-end scenarios live in `e2e/`.
GitHub Actions runs both suites on `ubuntu-24.04` runners. Default `pytest`
collects only `tests/`; the e2e runner selects its own `pytest.ini`.

```text
e2e/common_scripts/
  cases.py       L2Backend contract and store/clear/retrieve assertions
  server.py      LMCache server lifecycle, readiness and bounded shutdown
  Dockerfile     CPU LMCache build and selected plugin extra installation
  compose.yaml   Shared runner service, build context and artifact volume
  run.sh         Shared pytest command and report locations

e2e/<plugin>/
  test_server_roundtrip.py   Backend fixture and shared case invocation
  compose.yaml              Backend services and runner overrides
  README.md                 Backend prerequisites and run commands
```

`L2Backend` has three fields: `adapter_config` (the server's `--l2-adapter`
JSON), `status_type` (the adapter's reported type), and `exists(keys)` (an
independent real-backend probe). The probe accepts LMCache `ObjectKey` values
and returns one boolean per key in input order. Vendor fixtures own backend
clients, credentials, key encoding, and cleanup. Shared cases never import a
vendor SDK or construct its storage key format.

The shared store/clear/retrieve case checks that four fresh keys are absent,
stores deterministic two-layer KV, confirms all four objects reached L2,
and waits for asynchronous stores to drain. It clears only L1 via HTTP,
asserts zero L1 objects and intact L2 keys, then retrieves into zeroed CPU
buffers and compares every chunk checksum.

## Add an L2 plugin

1. Add `e2e/<plugin>/test_server_roundtrip.py`. Its fixture
   returns an `L2Backend`; its test calls `assert_store_clear_retrieve(backend, tmp_path)`.
   Keep optional SDK imports inside the fixture, after checking whether its
   live backend is configured, so e2e collection can skip an unconfigured backend.
2. Add `e2e/<plugin>/compose.yaml`. Define the backend services
   and extend the shared `test` service with `build.args.L2_PLUGIN: <plugin>`, its backend
   environment, `E2E_TEST_PATH: e2e/<plugin>`, and readiness
   dependencies.
   The matching package extra installs that plugin's dependencies.
3. Add `<plugin>` to the e2e job's `matrix.plugin` list. The common job handles
   build, runtime manifest, case execution, logs, cleanup, and artifact upload.

Use [Autumn](../autumn/README.md) as the first concrete implementation.
Compose files must be ordered with the shared file first: relative build and
volume paths in every overlay resolve against that first file's directory.
Do not copy the common case, server lifecycle, Dockerfile or pytest command.

## CI and evidence

CI runs for all PR target branches (including drafts), nightly at 02:17
Asia/Shanghai, published releases and prereleases, and manual dispatch. PRs
check out their merge revision; nightly uses the default branch; release uses
the released tag; manual dispatch uses the selected ref. Every run resolves
LMCache dev to an exact SHA. Concurrency is isolated by event, and matrix
entries have independent Compose projects and artifact directories.

The image records `/opt/lmcache-revision.txt` and `/opt/runtime-versions.txt`.
CI uploads those versions, both source revisions, JUnit XML, server logs and
cluster logs as `l2-server-e2e-<plugin>`. Local artifacts default to
`e2e-artifacts`; `E2E_ARTIFACTS` can set an absolute destination.

`lmcache bench l2` directly exercises an adapter in its own process. These
shared cases cover the real server request protocol, asynchronous store
controller, HTTP L1 clear, and L2 prefetch/retrieve instead.
