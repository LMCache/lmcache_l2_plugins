# autumn-rs L2 adapter

An LMCache L2 adapter backed by an [autumn-rs](https://github.com/journeymidnight/autumn-rs)
cluster: a distributed storage engine whose replicated, ordered KV layer holds
the chunks. The cluster is shared, durable and large, so it serves as a warm
tier that survives restarts and is shared across LMCache instances. The client
reads and writes straight into the L1 buffers with the GIL released; there is
no C++ extension to build.

| | |
| --- | --- |
| Maintainer | dongmao zhang ([@thesues](https://github.com/thesues)) |
| License | Apache-2.0 |
| LMCache | >= 0.5.7 (tested with 0.5.7.post1) |
| autumn-rs client | >= 0.1.2 |
| Python | >= 3.11, Linux x86_64 / aarch64 |
| Support | [autumn-rs issues](https://github.com/journeymidnight/autumn-rs/issues) |

## Install

```bash
pip install "lmcache>=0.5.7"
pip install "git+https://github.com/LMCache/lmcache_l2_plugins#subdirectory=autumn"
```

This pulls in the autumn-rs client (`pip install autumn-rs`). It speaks TCP
everywhere. With `"transport": "ucx"` it moves chunks over RDMA through the
host's UCX (>= 1.17, `libucp.so.0` on the loader path), which it loads only
then.

Over UCX the adapter registers its L1 arena when it is created, so chunks in
the arena move straight between L1 and the cluster without a copy. This pins
the whole arena up front, so the memlock limit must cover it.

The transport is process-wide: every autumn adapter in one LMCache server
process must use the same transport.

## Prepare the cluster

Keys are stored under a namespace, `kvc` by default, which must exist before
the adapter starts. Create it cut into 16 partitions so chunks spread over all
of them from the start:

```bash
autumn-op namespace-create --name kvc --parts 16
```

Keys are `{namespace}/{h}/lmcache/{storage key}`, where `h` is the chunk
hash's first hex digit, the digit the namespace is cut on when it is created
with `--parts 16`.

## Start the LMCache server

```bash
lmcache server --l1-size-gb 40 --eviction-policy LRU \
  --l2-adapter '{
    "type": "plugin",
    "module_path": "lmcache_autumn",
    "class_name": "AutumnL2Adapter",
    "adapter_params": {"manager": "10.0.0.1:9001", "transport": "ucx"}
  }'
```

LMCache finds the config class `AutumnL2AdapterConfig` by its name; no
`config_class_name` is needed. LMCache's own L2 keys (`shared`, `eviction`,
`serde`, `persist_enabled`) go at the top level of the JSON, beside `type`;
inside `adapter_params` they are ignored. LMCache's logs and metrics label the
adapter `plugin`; its status reports `"type": "autumn"`.

`adapter_params` fields:

| Field | Default | Meaning |
| --- | --- | --- |
| `manager` | required | Comma-separated `ip:port` list of autumn managers. The client dials addresses, so resolve host names first. |
| `namespace` | `"kvc"` | autumn namespace for the keys. |
| `credential_file` | `""` | An autumn principal credential file, as `autumn-op principal-create` writes it. Required when authorization protects the namespace. |
| `num_workers` | `4` | Batches queued or in flight (> 0). The client runs gets and puts one batch at a time. |
| `transport` | `"tcp"` | `"tcp"` or `"ucx"`. |
| `direct` | `false` | Read large values straight from the storage nodes instead of through the partition servers. Needs the client to reach the storage nodes. |
| `ttl_secs` | `0` | Expiry of each stored chunk in seconds; `0` keeps chunks until they are evicted. |
| `max_capacity_gb` | `0` | Max L2 capacity in GB for usage tracking / aggregate eviction. `0` disables tracking. |

Authorization on, chunks expire after a day, a capacity cap:

```bash
--l2-adapter '{"type": "plugin", "module_path": "lmcache_autumn", "class_name": "AutumnL2Adapter", "adapter_params": {"manager": "10.0.0.1:9001,10.0.0.2:9001", "credential_file": "/etc/autumn/kvc.cred", "ttl_secs": 86400, "max_capacity_gb": 500}}'
```

## Partition-server memory tier

Partition servers started with `--mem-tier-bytes <budget> --mem-tier-prefix kvc/`
acknowledge a chunk from DRAM and append it to the replicated log right after,
and serve reads from memory. A partition-server crash loses only chunks whose
append had not landed yet, which a cache can afford.

## Tests

```bash
pip install -e "autumn[test]"
pytest autumn/tests
```

The unit tests replace the `autumn` client with an in-memory fake and need no
cluster. Every adapter in them is built from an `--l2-adapter` JSON of type
`plugin`, the way `lmcache server` builds it. One test runs against a live
cluster when `AUTUMN_MANAGER` (`ip:port`) is set; add
`AUTUMN_TRANSPORT=ucx` to run it over UCX through a registered arena, and
`AUTUMN_CREDENTIAL_FILE` for a protected namespace.

Validation status, with LMCache 0.5.7.post1 and autumn-rs 0.1.2 on one host:

| Check | Result |
| --- | --- |
| Unit tests | 29 passed, 1 skipped (the live test) |
| Live test against a 3-node cluster, TCP | passed |
| Live test against a 3-node cluster, UCX over RoCE | passed |
| `lmcache server` with the plugin JSON above, UCX | adapter created, L1 arena registered, clean shutdown |

The same adapter code, built in-tree, was run end to end with vLLM 0.28 and
LMCache's MP connector: Qwen3-VL-32B, 6 documents of ~17K tokens, written by
one instance and loaded by a fresh lmcache server and vLLM. All answers were
correct, 99.1% of prefix tokens came from L2, and TTFT was 0.30 s over UCX,
1.34 s over TCP, against 2.78 s recomputing. Cross-host runs are not measured.
