# Package publishing

Like LMCache, this repository builds PR packages as GitHub Actions artifacts,
publishes development builds to TestPyPI after merge, and publishes GitHub
releases to PyPI. All distributions use the name `lmcache-l2-plugins`.

| Event | Destination | Version |
| --- | --- | --- |
| Every PR, including drafts | Actions artifact `distributions` | `<project.version>.dev<run_id><attempt padded to 3 digits>` |
| Push to `main` | [TestPyPI](https://test.pypi.org/project/lmcache-l2-plugins/) and Actions artifacts | Same development version format |
| GitHub Release published | [PyPI](https://pypi.org/project/lmcache-l2-plugins/) and Actions artifacts | Exact `project.version`, validated against the release tag |
| Nightly or manual workflow run | Actions artifacts only | Development version |

The Package workflow builds a wheel and source distribution, runs
`twine check --strict`, and installs each in a separate fresh virtual environment.
Verification automatically discovers each plugin's `plugin.toml` and installs
CPU PyTorch, that plugin's extra, and its test dependencies in a fresh environment
per plugin. It checks dependencies and declared imports outside the checkout,
then runs only that plugin's tests against the installed package. Default tests
require no GPUs or external services. See [adding a plugin](adding-a-plugin.md)
for the directory and declaration contract.

After publishing, a separate job downloads the exact wheel from the destination
index with a bounded retry, compares its SHA-256 with the built wheel, and repeats
installation and unit tests. Dependencies always come from PyPI (CPU PyTorch
comes from its official index), even when the wheel is downloaded from TestPyPI.
The source distribution is installation-tested before upload; post-publish
verification tests the wheel. A failed verification fails the workflow; it does
not remove the already published version.

## One-time maintainer setup

Create GitHub environments `testpypi` and `pypi`. Restrict `testpypi` to `main`
and `pypi` to release tags matching `v*`. Add required reviewers to `pypi` if
release publication should require approval.

Configure a [Trusted Publisher](https://docs.pypi.org/trusted-publishers/)
on each index (use a pending publisher if the project does not exist yet):

| Setting | TestPyPI | PyPI |
| --- | --- | --- |
| Project | `lmcache-l2-plugins` | `lmcache-l2-plugins` |
| Owner | `LMCache` | `LMCache` |
| Repository | `lmcache_l2_plugins` | `lmcache_l2_plugins` |
| Workflow filename | `package.yml` | `package.yml` |
| Environment | `testpypi` | `pypi` |

No long-lived PyPI token is needed. Publishing permissions are limited to the
separate publishing jobs; PR and manual runs cannot enter these jobs. Fork PRs
build with read-only permissions and may need the usual GitHub Actions approval.
These index-side publisher registrations must be completed by a PyPI maintainer;
adding this workflow alone does not grant publishing rights.

## Release

1. Update `project.version` in `pyproject.toml` through a PR and merge it.
2. Create a tag on the intended merged commit, for example `v0.1.0`, and publish
   a GitHub Release for that tag. Tag pushes alone do not publish packages.
3. Check all Package jobs, including `Verify published package`. Tags must match the
   static version exactly. Prereleases such as `v0.2.0rc1` are supported.

Development versions include the Actions run ID and attempt to avoid index
collisions on reruns. Publishing skips existing files so a failed post-publish
verification can be rerun; the downloaded wheel must still match the artifact.
Never reuse a release version for changed package contents.

## Install a PR artifact

Download `distributions` from the PR's Package workflow run and unzip it:

```bash
python -m pip install './lmcache_l2_plugins-<version>-py3-none-any.whl[autumn]'
```

For TestPyPI, download just the exact project wheel first, then install its
dependencies from PyPI to avoid mixing indexes:

```bash
python -m pip download --no-deps --only-binary=:all: \
  --index-url https://test.pypi.org/simple --dest downloaded \
  'lmcache-l2-plugins==<exact development version from the workflow>'
python -m pip install './downloaded/lmcache_l2_plugins-<version>-py3-none-any.whl[autumn]'
```

## Reproduce package checks

Use Linux with Python 3.12, `venv`, and network access to PyPI and the CPU
PyTorch index. `autumn-rs` does not publish macOS wheels. From a clean checkout
of the revision being tested:

```bash
python -m pip install build twine packaging pytest "setuptools>=77.0.3" wheel
python -m pytest -q .github/tests
python .github/scripts/prepare_package.py --run-id 12345 --run-attempt 1
python -m build
python -m twine check --strict dist/*
python -m build_support.verify_package dist/*.whl lmcache-l2-plugins 0.1.0.dev12345001
python -m build_support.verify_package dist/*.tar.gz lmcache-l2-plugins 0.1.0.dev12345001
```

Replace `0.1.0` with the checkout's `project.version`. Version stamping modifies
the working copy of `pyproject.toml` for the build only; do not commit that stamp.

Real-server e2e jobs reuse the verified wheel from this same workflow run; see
[the e2e guide](e2e/index.md). They run on PR, nightly, release and manual events.
