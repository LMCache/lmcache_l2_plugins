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

- Follow LMCache's publishing pattern, using the independent repository
  `LM-Cache-Website/lmcache-l2-plugins` and the `LMCACHE_L2_DOC` Actions secret.
  Publish generated HTML to its root. Do not write to the main LMCache website
  repository `LM-Cache-Website/lm-cache-website.github.io`.
- A GitHub Pages project site inherits the organization's custom domain. With
  Pages publishing from `main` at `/`, this site's URL is
  `https://docs.lmcache.ai/lmcache-l2-plugins/`; no new DNS record is needed.
- Verify publishing-repository access and secret availability before treating
  a successful docs build as a successful deployment. Companion repositories
  do not inherit repository secrets from LMCache core.
