Contributing an Integration
===========================

Plugins can be maintained in this repository or in a vendor-owned repository
with an integration guide here. Both models need an identified maintainer,
license, supported LMCache versions, configuration examples, and validation
instructions.

Read the upstream
`external L2 adapter guide <https://github.com/LMCache/LMCache/blob/dev/docs/source/developer_guide/extending_lmcache/storage_plugins.rst#mp-mode-l2-adapter-plugins-plugin>`_
for the adapter interface. Keep the implementation contract in LMCache core;
use this repository for backend-specific installation and operational details.

Repository layout
-----------------

* ``lmcache_l2_plugins/<name>/``: plugin implementation and backend README.
* ``tests/<name>/``: plugin tests.
* ``lmcache_l2_plugins/<name>/plugin.toml``: backend dependencies and verification
  declarations; packaging automatically generates the extra named after the plugin.
* ``docs/source/plugins/``: integration pages included in the Sphinx site.
* ``docs/design/<name>/``: design documents matching the plugin package path.

A plugin guide should cover prerequisites, installation, server configuration,
credentials, capacity and transport limitations, troubleshooting, and tests.
State the versions and infrastructure used for any validation results.

Building the docs
-----------------

From the repository root, with Python 3.12:

.. code-block:: bash

   python3.12 -m venv .venv-docs
   . .venv-docs/bin/activate
   python -m pip install -r requirements/docs.txt
   make -C docs html SPHINXOPTS="-W --keep-going -n"

Open ``docs/build/html/index.html`` in a browser. On Windows, activate the
virtual environment with ``.venv-docs\Scripts\activate`` and use
``docs\make.bat html`` from the repository root.

The docs build installs only documentation dependencies. It does not import the
plugin package and needs no LMCache installation, CUDA, or storage client.
Existing Markdown guides are included with MyST so the site and GitHub views
share the same content.

To add a plugin page, include its README from a Markdown page in
``docs/source/plugins/`` and add that page to ``plugins/index.rst``. Check links
and images in both GitHub and the built site. Run the warning-as-error build
above before opening a pull request.
