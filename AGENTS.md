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
  `NO_NATIVE_EXT=1`). Resolve `dev` to a SHA before installation and record it
  with the test artifacts.
- Autumn's optional backend service script uses Compose and io_uring; its
  containers need `seccomp:unconfined`. Native Linux clients must reach every
  advertised Docker bridge IP, not just a published manager port. Other plugins
  own their backend lifecycle and need not use Docker or Compose.
- The CPU server bench defaults to engine-driven transfers. Start its server
  with `--supported-transfer-mode engine_driven` (or `auto`); the server default
  enables only `lmcache_driven` and rejects the client's registration RPC.
- Keep importlib mode enabled for e2e collection: multiple plugins may use the
  same test filename. Backend test folders need `__init__.py` so their module
  names stay under `e2e.<plugin>` rather than shadowing installed SDKs.
  UT verification discovers plugin declarations and isolates each environment.
  E2e discovery uses the same inventory, with complete `e2e/<plugin>` folders
  opting into CI; do not introduce a second hardcoded plugin list.
- This repository has no `.pre-commit-config.yaml`. Until hooks are added,
  validate packaging changes with Ruff, isort, `actionlint`, `bash -n`, and
  `.github/tests`, then run the Linux package installation checks documented in
  `docs/publishing.md`. Do not report an unavailable pre-commit run as passing.
- Setuptools' isolated PEP 517 hooks do not guarantee the checkout is on
  `sys.path`. `setup.py` loads only the build helper via `runpy`; keep that
  helper and plugin declarations in `MANIFEST.in`. Validate with `python -m
  build` (sdist followed by wheel-from-sdist), not only a direct wheel build.

## Documentation deployment

- Plugin READMEs are included in the Sphinx build with warnings treated as
  errors. Link to e2e guides outside `docs/source` using GitHub URLs; relative
  Markdown links produce MyST `xref_missing` warnings in the included page.
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
