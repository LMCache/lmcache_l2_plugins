# Adding a plugin

Each L2 owns its implementation, declaration, documentation, and tests. Shared
build and CI code discovers plugins from the directory tree; there is no central
plugin list to update.

```text
lmcache_l2_plugins/
  __init__.py                   # Does not import individual backends
  <name>/
    __init__.py
    adapter.py                 # Backend implementation
    plugin.toml                # Backend dependencies and verification
    README.md                  # Configuration, support, hardware requirements
tests/
  <name>/
    test_adapter.py            # CPU unit tests; mock external services
build_support/                 # Shared discovery, packaging, isolation
```

Use a lowercase Python package name (`[a-z][a-z0-9_]*`); `test` is reserved for
the shared pytest extra. Directories beginning with `_` are reserved for internal
helpers and are not plugins. Every other direct Python subpackage must have a
`plugin.toml`; missing declarations fail the build instead of silently bypassing
verification. A plugin must also have at least one `tests/<name>/test_*.py` file.

## Plugin declaration

Create `lmcache_l2_plugins/<name>/plugin.toml`:

```toml
dependencies = ["lmcache>=0.5.7", "vendor-client>=1.0"]

[verification]
imports = ["lmcache_l2_plugins.<name>"]
dependencies = [] # Test-only requirements, e.g. pytest-asyncio
```

Replace `<name>` with the package name. Import checks may list multiple modules
inside that plugin. Declare the LMCache version range your implementation uses,
runtime client dependencies, and any additional test dependencies here.
The generated wheel and source distribution expose the runtime requirements as
the extra of the same name, so users install `lmcache-l2-plugins[<name>]`.
The public installation interface remains one distribution with one extra per
plugin. Test-only requirements do not become runtime requirements.

Add CPU tests that exercise the LMCache plugin loader, configuration, and adapter
behavior. Keep shared fixtures within `tests/<name>/`; verification copies only
that plugin's test directory outside the checkout. Tests for real services or
hardware should be explicitly opt-in, with prerequisites documented in the
plugin's README. The default package gate needs neither credentials nor a
running backend. It checks CPU compatibility; hardware integration remains a
separate backend-specific responsibility.

## Automatic participation

Adding those files is enough for:

- setuptools to generate the new extra, including when rebuilding a wheel from
  the source distribution;
- nightly, manual, and PR tests to install and verify the new plugin;
- wheel and source-distribution checks before publication;
- installed-wheel verification after publication to TestPyPI or PyPI.

Each plugin is installed in its own fresh virtual environment with CPU PyTorch,
its own extra, pytest, and its declared test dependencies. Dependency conflicts
between different plugins cannot be masked by a combined installation. Imports,
dependency consistency, and unit tests run against the installed package outside
the source checkout. No changes to `pyproject.toml`, `setup.py`, shared scripts,
or workflow YAML are needed when adding an ordinary plugin.

The regression test adds two synthetic plugins using only new files, builds a
source distribution, and rebuilds a wheel from it to check generated extras.

See [publishing.md](publishing.md) for the common release process and commands.

## Optional real-server e2e

To opt a declared plugin into real-server CI, add `.github/e2e/<name>/__init__.py`,
`test_server_roundtrip.py` and `service.sh`. The test fixture provides the shared
`L2Backend` contract; the script implements backend-specific `start`, `logs` and
`stop` actions. See [the e2e guide](e2e/index.md).

E2e discovery reuses the plugin inventory, validates the complete folder and
creates the CI matrix automatically. A normal UT-only plugin needs no e2e
folder. Backend startup may use native processes, an existing service, or
containers; Compose is not required. LMCache and pytest always run directly
in the runner's Python environment. Test modules live under `e2e.<name>` to
avoid filename collisions and shadowing the installed SDK.
