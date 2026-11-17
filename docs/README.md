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

The installation guide lives at `docs/source/getting_started/installation.md`, and the
Autumn page includes `lmcache_l2_plugins/autumn/README.md` through MyST. Edit
those original files to update both their GitHub views and the site. Add new
site pages to the appropriate `index.rst` toctree.

## CI and deployment

The documentation site is [LMCache L2 Plugins documentation](https://lmcache-website.github.io/lmcache-l2-plugins/).
It follows the [LMCache documentation publishing workflow](https://github.com/LMCache/LMCache/blob/dev/.github/workflows/build_doc.yml),
using the dedicated publishing repository
[LMCache-website/lmcache-l2-plugins](https://github.com/LMCache-website/lmcache-l2-plugins).
The publishing repository and GitHub Pages site are independent of the main
LMCache documentation site. The site uses GitHub's default HTTPS domain.

The `Documentation` workflow builds with warnings treated as errors on pull
requests. Download its `documentation-html` artifact and open `index.html` to
preview the site.

After a PR merges into `main`, changes to `docs/source/**` or `docs/Makefile`
automatically rebuild and deploy the site. Changes to the included installation
guide, plugin READMEs, assets, documentation requirements, Windows build script,
or workflow also trigger a rebuild. A manual run on `main` can redeploy without
a new commit. PR builds never publish to the live site.

### Publishing configuration

- Target repository: `LMCache-website/lmcache-l2-plugins`, branch `main`.
- GitHub Pages source: **Deploy from a branch → main → /(root)**.
- Source repository Actions secret: `LMCACHE_L2_DOC_DEPLOY_KEY`, containing the
  SSH private key for a write-enabled deploy key registered only on the target
  repository. `actions/checkout` configures the key for publishing and removes
  it during post-job cleanup.

The repository and Pages source are configured. Before installing the deploy
key, an organization owner must allow **Settings → Member privileges → Deploy
keys**. Automatic publishing requires the registered key and source Actions
secret described above. No personal access token or DNS configuration is
required. If the deploy key is
rotated, update its public key in the target repository's **Settings → Deploy
keys** and its private key in the source repository's Actions secret.

The workflow synchronizes generated HTML to the publishing repository's root,
preserves its `.git` and `.github` directories, and pushes without force.
