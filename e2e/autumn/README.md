# Autumn server e2e

This backend runs a disposable Autumn TCP cluster: etcd, one manager, three
extent nodes and one partition server. Its fixture supplies the plugin JSON
and an Autumn `BatchClient.exists` probe that converts LMCache object keys to
Autumn's bucketed key format. The complete correctness case, server lifecycle,
CPU image and test runner live in [the shared e2e layer](../common_scripts/README.md).

## Run

Prerequisites: Docker Compose v2, a Linux kernel >=5.15 with io_uring enabled,
internet access and enough memory to build LMCache's CPU extensions (8 GiB
recommended). Docker Desktop uses its Linux VM. Autumn containers require
`seccomp:unconfined` for io_uring. No host service ports are published; clients
run inside the Compose network to reach advertised backend node addresses.

From the repository root:

```bash
export COMPOSE_FILE=e2e/common_scripts/compose.yaml:e2e/autumn/compose.yaml
export COMPOSE_PROJECT_NAME=autumn-e2e
export LMCACHE_REF=$(git ls-remote https://github.com/LMCache/LMCache.git refs/heads/dev | cut -f1)
docker compose build test
docker compose run --rm test
docker compose logs --no-color > e2e-artifacts/autumn.log
docker compose down --volumes --remove-orphans
```

Set `LMCACHE_REF` to a commit SHA to reproduce a prior run. The common Dockerfile
installs the `autumn` package extra selected by this overlay, with CPU Torch
and LMCache dev. Tests use `AUTUMN_MANAGER` and optionally `AUTUMN_NAMESPACE`
(default `kvc`); without the manager they skip when the e2e suite is selected. The
Compose overlay always sets it and waits for cluster bootstrap, so its live
case must run. Every runtime wait and pytest execution has a timeout.

The Autumn image is pinned by digest. Its deployment is adapted from
[autumn-rs deploy/compose at 6ab4f0a](https://github.com/journeymidnight/autumn-rs/tree/6ab4f0a304bb28a7fa3ef0beebf2456b7a673be2/deploy/compose).
