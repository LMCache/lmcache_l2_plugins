# Documentation

Like [LMCache](https://github.com/LMCache/LMCache/tree/dev/docs), this project
uses Sphinx with `sphinxawesome_theme`. User-facing sources live in
`docs/source/`; design documents live in [`docs/design/`](design/README.md).

## Build locally

From the repository root, using Python 3.12:

```bash
python3.12 -m venv .venv-docs
. .venv-docs/bin/activate
python -m pip install -r requirements/docs.txt
make -C docs html SPHINXOPTS="-W --keep-going -n"
```

Open `docs/build/html/index.html` in a browser. On Windows, activate with
`.venv-docs\Scripts\activate` and run `docs\make.bat html` from the repository
root. The Windows and Make entry points both write to `docs/build/`.

Only documentation dependencies are needed. Do not install the project or its
backend extras just to build the docs.

## Content and layout

- `source/getting_started/`: installation and integration.
- `source/plugins/`: plugin-specific guides.
- `source/developer_guide/`: contribution and documentation guidance.
- `design/`: Markdown design documents mirroring `lmcache_l2_plugins/`.

The installation page includes `docs/installation-and-integration.md`, and the
Autumn page includes `lmcache_l2_plugins/autumn/README.md` through MyST. Edit
those original files to update both their GitHub views and the site. Add new
site pages to the appropriate `index.rst` toctree.

## CI

The `Documentation` workflow builds with warnings treated as errors on pull
requests and pushes to `main`, and can also be run manually. Download its
`documentation-html` artifact and open `index.html` to preview the site.
The artifact contains a static site suitable for hosting; this workflow does
not configure a public documentation domain or deploy the site.
