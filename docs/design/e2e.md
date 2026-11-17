# Real-server L2 e2e

The package needs to verify real L2 persistence through LMCache without an
inference engine. Adapter benchmarks alone bypass the server and cannot prove
that clearing L1 causes retrieval from L2.

## Ownership and entry points

```mermaid
flowchart TD
    Event[PR / nightly / release / manual] --> Package[Package workflow]
    Package --> Build[build: wheel + sdist + installed-package verification]
    Build --> Artifact[distributions artifact]
    Package --> Discover[discover-e2e: build_support.e2e]
    Discover --> Matrix[l2-e2e: one job per declared backend with e2e]
    Artifact --> Matrix
    Matrix --> Install[Install LMCache dev + built plugin wheel]
    Install --> Start[e2e/plugin/service.sh start]
    Start --> Stage[Copy only e2e outside checkout]
    Stage --> Runner[e2e/common_scripts/run.sh]
    Runner --> Pytest[pytest: e2e/plugin/test_server_roundtrip.py]
    Pytest --> Backend[Backend fixture: adapter JSON + independent exists probe]
    Backend --> Fixture[e2e/conftest.py: lmcache_server fixture]
    Fixture --> Server[Real lmcache server subprocess + healthcheck]
    Server --> Case[common_scripts/cases.py: assert_store_clear_retrieve]
    Case --> Store[Initial miss / deterministic CPU KV / store RPC]
    Store --> Probe[Independent L2 existence check / drain asynchronous stores]
    Probe --> Clear[HTTP clear L1 / assert zero L1 objects / L2 intact]
    Clear --> Load[New zeroed buffer / full hit / retrieve RPC / checksum equality]
    Load --> Cleanup[Close client / stop server]
    Cleanup --> Finish[Always: backend logs + stop + upload evidence]
```

The public developer instructions live in
[the e2e guide](../source/developer_guide/e2e.md).

## Boundaries and tradeoffs

The existing plugin declaration registry supplies both package verification and
e2e discovery. Complete backend e2e folders opt in; partial folders fail early.
Each matrix job installs only its selected plugin extra and test dependencies.
The wheel comes from the same workflow run, with no cross-workflow artifact
lookup or revision matching. Running copied tests outside the checkout prevents
imports of the source package from hiding wheel defects.

The shared pytest fixture owns LMCache ports, command, readiness, logs and
process cleanup. It starts the real installed CLI and passes RPC/HTTP addresses
to the shared case. CLI and status API changes in LMCache may still require a
compatibility update here; the fixture does not hide that dependency. A separate
server wrapper module adds no useful boundary for this single caller.

Backend fixtures own configuration, SDK usage and independent persistence probes.
Backend lifecycle scripts own provisioning and cleanup; Compose is an Autumn
implementation choice, not a framework prerequisite. LMCache and pytest run
natively on the runner. Default UT remains under `tests/` and needs no services.

## Failure handling and validation

The fixture bounds readiness and shutdown and prints server logs even after
failure. CI collects backend diagnostics and attempts cleanup with `always()`;
JUnit, logs, source revisions, versions and the wheel checksum are artifacts.
The correctness case waits for asynchronous L2 stores before clearing L1 so that
in-flight buffers cannot be invalidated by the test itself. A backend probe
confirms actual persistence independently of the LMCache lookup result.

Validate discovery with `.github/tests`, build the documentation with warnings
as errors, and run the native e2e job against a real backend. A passing Autumn
case validates that adapter; each future backend needs its own real service run.
