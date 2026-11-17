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
  `LMCache-website/lmcache-l2-plugins` and the `LMCACHE_L2_DOC_DEPLOY_KEY` Actions
  secret. The secret is an SSH deploy key scoped to this publishing repository;
  pass it to `actions/checkout` through `ssh-key`, not `token`.
- Publish generated HTML to the target repository's root. Pages serves `main`
  at `/`, with URL `https://lmcache-website.github.io/lmcache-l2-plugins/`.
  Do not write to `LM-Cache-Website/lm-cache-website.github.io`.
- New GitHub organizations disable deploy keys by default. An organization
  owner must enable **Settings → Member privileges → Deploy keys** before the
  publishing key can be registered.
- Verify target repository access and secret availability before treating a
  successful docs build as a successful deployment. Organization names
  `LMCache-website` and `LM-Cache-Website` identify different organizations.
