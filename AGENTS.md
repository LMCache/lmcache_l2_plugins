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
- This repository has no `.pre-commit-config.yaml`. Until hooks are added,
  validate packaging changes with Ruff, isort, `actionlint`, `bash -n`, and
  `.github/tests`, then run the Linux package installation checks documented in
  `docs/publishing.md`. Do not report an unavailable pre-commit run as passing.
- Setuptools' isolated PEP 517 hooks do not guarantee the checkout is on
  `sys.path`. `setup.py` loads only the build helper via `runpy`; keep that
  helper and plugin declarations in `MANIFEST.in`. Validate with `python -m
  build` (sdist followed by wheel-from-sdist), not only a direct wheel build.
