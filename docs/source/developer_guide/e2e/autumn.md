# Autumn server e2e

LMCache and pytest run directly in the native Python environment described in
[the shared guide](index.md). Compose is used only to start
Autumn's storage backend: etcd, one manager, three extent nodes and one
partition server. There is no LMCache or test-runner service in the Compose file.

## Run

Use a native Linux host with Docker Compose v2, GNU `timeout` (coreutils),
a kernel >=5.15 with io_uring, and Docker access for the current user.
The containers need `seccomp:unconfined` for io_uring. The native Linux client
connects to Docker bridge IPs advertised by the backend; publishing only the
manager port is insufficient. Docker Desktop on macOS does not provide this
native-host routing, and autumn-rs Python wheels require Linux.

After preparing the Python environment, run from the repository root:

```bash
export E2E_ARTIFACTS="$PWD/e2e-artifacts"
bash .github/e2e/autumn/service.sh start
source "$E2E_ARTIFACTS/backend.env"
bash .github/e2e/common_scripts/run.sh .github/e2e/autumn
# Collect logs and stop the backend even if pytest fails.
bash .github/e2e/autumn/service.sh logs
bash .github/e2e/autumn/service.sh stop
```

`start` waits for bootstrap and namespace creation, then writes the manager
address to `backend.env`. `AUTUMN_COMPOSE_PROJECT` optionally selects an isolated
project name. All server data volumes are removed by `stop`.

For an existing reachable Autumn TCP cluster with namespace `kvc`, skip the
service script and set `AUTUMN_MANAGER=ip:port` before running the shared command.
`AUTUMN_NAMESPACE` can select another prepared namespace. Without the manager,
the live test skips when explicitly selected.

The fixture owns the adapter JSON and `BatchClient.exists` probe, translating
LMCache object keys to Autumn's bucketed storage keys. All correctness
assertions and LMCache process management remain in the shared Python code.

The backend image is pinned by digest. The deployment is adapted from
[autumn-rs deploy/compose at 6ab4f0a](https://github.com/journeymidnight/autumn-rs/tree/6ab4f0a304bb28a7fa3ef0beebf2456b7a673be2/deploy/compose).
