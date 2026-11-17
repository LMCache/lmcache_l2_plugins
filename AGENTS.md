# Repository guidance

## CI verification

- Install `.[autumn,test]` for the Autumn test suite. Installing only `.[test]`
  leaves `lmcache` unconstrained and can resolve an old release that tries to
  build CUDA extensions.
- `autumn-rs` publishes Linux wheels, but not macOS wheels. Reproduce the
  nightly job in a Linux environment; for CPU-only tests, install torch from
  `https://download.pytorch.org/whl/cpu` and set `NO_GPU_EXT=1` while installing
  the project.
- If GitHub Actions warns that an action still targets deprecated Node.js 20,
  update its pinned SHA to a release whose `action.yml` declares Node.js 24.
- The server e2e needs LMCache's CPU native extensions: install CPU torch first,
  then build LMCache with `NO_GPU_EXT=1` and `--no-build-isolation` (not
  `NO_NATIVE_EXT=1`). Resolve `dev` to a SHA before Docker builds so its cache
  cannot hide upstream changes.
- Autumn uses io_uring; its containers need `seccomp:unconfined` on Linux.
  Bootstrap waits for the partition server before creating namespaces, so the
  e2e service must start both `ps` and `bootstrap`, waiting for bootstrap to
  complete. Run clients in the same Compose network as advertised node IPs.
- The CPU server bench defaults to engine-driven transfers. Start its server
  with `--supported-transfer-mode engine_driven` (or `auto`); the server default
  enables only `lmcache_driven` and rejects the client's registration RPC.
- Keep `e2e/common_scripts/compose.yaml` first when layering a vendor's Compose file:
  relative build contexts and artifact volumes resolve against the first file.
