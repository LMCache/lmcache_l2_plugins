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

## CI and deployment

The documentation URL is [LMCache L2 Plugins documentation](https://docs.lmcache.ai/lmcache-l2-plugins/).
The site follows the [LMCache documentation publishing workflow](https://github.com/LMCache/LMCache/blob/dev/.github/workflows/build_doc.yml),
using a dedicated publishing repository:
[LM-Cache-Website/lmcache-l2-plugins](https://github.com/LM-Cache-Website/lmcache-l2-plugins).
This workflow writes only to that repository.

GitHub Pages project sites inherit their organization's existing custom domain.
With the publishing repository owned by `LM-Cache-Website`, its site is served
under `docs.lmcache.ai/lmcache-l2-plugins/`. The main LMCache documentation and
this site have separate publishing repositories and build histories.

The `Documentation` workflow builds with warnings treated as errors on pull
requests. Download its `documentation-html` artifact and open `index.html` to
preview the site.

After a PR merges into `main`, changes to `docs/source/**` or `docs/Makefile`
automatically rebuild and deploy the site. Changes to the included installation
guide, plugin READMEs, assets, documentation requirements, Windows build script,
or workflow also trigger a rebuild. A manual run on `main` can redeploy without
a new commit. PR builds never publish to the live site.

### One-time administrator setup

1. Create the public repository `LM-Cache-Website/lmcache-l2-plugins`, initialized
   with a README on its `main` branch.
2. In that repository's **Settings → Pages**, choose **Deploy from a branch**,
   branch **main**, folder **/(root)**. Leave the custom-domain field empty so
   the project site uses the organization's existing domain.
3. In `LMCache/lmcache_l2_plugins`, add the Actions secret `LMCACHE_L2_DOC` with
   a publishing token authorized to write to the dedicated publishing repository.
   A fine-grained token needs **Contents: Read and write** for that repository.
   This workflow does not need write access to the main LMCache website repository.

The workflow synchronizes generated HTML to the publishing repository's root,
preserves its `.git` and `.github` directories, and pushes without force.
The URL becomes available after setup and the first successful publication.
