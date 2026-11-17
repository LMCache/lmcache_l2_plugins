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

## Documentation deployment

- Follow LMCache's `.github/workflows/build_doc.yml`: publish to
  `LM-Cache-Website/lm-cache-website.github.io` using `LMCACHE_DOC`. This project's
  output belongs only in `l2-plugins/`, served at `docs.lmcache.ai/l2-plugins/`.
- Verify that `LMCACHE_DOC` is available to this repository before treating a
  successful docs build as a successful deployment. A secret configured only on
  the LMCache core repository is not inherited by companion repositories.
