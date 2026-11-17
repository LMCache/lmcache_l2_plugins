# Autumn server e2e

This test runs a real `lmcache server` subprocess and a disposable Autumn TCP
cluster (etcd, manager, three extent nodes, partition server). It uses the CPU
`ServerBenchClient` from LMCache dev, without vLLM, a model, CUDA, or a GPU.
The plugin is installed as a package with its `autumn` extra inside the test
image; LMCache loads it through `--l2-adapter` with `type=plugin`.

CI runs on every PR's opening, update, reopening, or ready-for-review event,
including draft PRs and PRs to any target branch; every night at 02:17
Asia/Shanghai; and publication of a release or prerelease. PR runs check out
the merge revision, nightly runs use the default branch, and release runs use
the released tag. Manual dispatch uses the selected branch or tag. Every run
resolves LMCache `dev` to an exact SHA before building. Separate concurrency
groups keep nightly, release, PR, and manual runs from cancelling one another.

## Run

Prerequisites: Docker Engine with Compose v2, a Linux kernel >= 5.15 with
io_uring enabled, internet access, and enough memory to compile LMCache's CPU
extensions (8 GiB is recommended). Docker Desktop uses its Linux VM. The
Autumn containers need `seccomp:unconfined` for io_uring. No host service ports
are published; the client and backend share the Compose network.

From the repository root:

```bash
export COMPOSE_FILE=tests/e2e/compose.yaml
export COMPOSE_PROJECT_NAME=autumn-e2e
# Resolve dev to an immutable revision so Docker does not reuse an older build.
export LMCACHE_REF=$(git ls-remote https://github.com/LMCache/LMCache.git refs/heads/dev | cut -f1)
docker compose build test
docker compose run --rm test
# Inspect evidence before cleanup, including when the test fails.
docker compose logs --no-color > tests/e2e/artifacts/autumn.log
docker compose down --volumes --remove-orphans
```

Set `LMCACHE_REF` to a commit SHA to reproduce an earlier run. The image records
the resolved LMCache SHA in `/opt/lmcache-revision.txt`; CI also uploads the
LMCache and plugin revisions, installed package versions, JUnit XML,
LMCache server log, and cluster logs
in the `autumn-server-e2e` artifact. The default artifact directory is
`tests/e2e/artifacts`; `E2E_ARTIFACTS` can set an absolute destination.
The Autumn image is pinned by digest in `compose.yaml`. Its cluster setup is
adapted from [autumn-rs deploy/compose](https://github.com/journeymidnight/autumn-rs/tree/main/deploy/compose).

## Assertions

1. Four unique chunk keys are initially absent in Autumn, and server LOOKUP
   reports a full miss.
2. A CPU worker fills deterministic KV data for two layers and stores four
   chunks through the LMCache request protocol.
3. The real Autumn client sees all four stored keys. The test waits until the
   server's asynchronous L2 stores have drained.
4. `POST /cache/clear` with `{"tier":"l1","force":false}` empties L1; the
   test checks its object count is zero and the Autumn keys still exist.
5. A new request zeros its destination buffers, LOOKUP hits all four chunks
   through L2, and RETRIEVE restores the original per-chunk KV checksums.

All waits and subprocess shutdowns are bounded. The container's pytest timeout
also catches hung backend calls. Without `AUTUMN_MANAGER`, this live test skips
in the ordinary unit test job. The Compose test always sets it, so CI must run
the round trip instead of silently skipping it.

`lmcache bench l2` (`l2_adapter_bench`) directly creates and exercises an adapter
in its own process. It is useful for adapter throughput measurements, but does
not start an LMCache server or cover its request protocol, asynchronous store
controller, L1 clear, and L2 prefetch path. This e2e reuses the server bench's
public client operations to cover those paths with assertions.
