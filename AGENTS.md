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

- Verify the public Pages URL over HTTP before documenting it. The organization
  site's `CNAME` can redirect project sites: at setup on 2026-11-17,
  `lmcache.github.io/lmcache_l2_plugins/` redirected to `blog.lmcache.ai`,
  whose DNS served WordPress rather than GitHub Pages. A successful Pages build
  alone does not verify that the public domain serves the documentation.
