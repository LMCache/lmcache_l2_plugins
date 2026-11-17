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

The published site is [LMCache L2 Plugins documentation](https://l2-plugins.lmcache.ai/).
GitHub Pages hosts the site on this repository's custom domain. The site becomes
available after DNS is configured and the first deployment from `main` completes.

The `Documentation` workflow builds with warnings treated as errors on pull
requests. Download its `documentation-html` artifact and open `index.html` to
preview the site.

After a PR merges into `main`, changes to `docs/source/**` or `docs/Makefile`
automatically rebuild and deploy the site. Changes to the included installation
guide, plugin READMEs, assets, documentation requirements, Windows build script,
or workflow also trigger a rebuild. A manual run on `main` can redeploy without
a new commit. PR builds never publish to the live site.

Deployment uses GitHub Pages artifacts and the `github-pages` environment, with
`pages: write` and `id-token: write` permissions limited to the deployment job.
The deployment environment and workflow summary show the published site URL.
No personal access token or separate hosting repository is needed.

Repository administrators must select **Settings → Pages → Build and deployment
→ Source: GitHub Actions** once. This has been enabled for this repository.

The custom domain is `l2-plugins.lmcache.ai`. The domain administrator must add a
DNS record with type **CNAME**, name **l2-plugins**, and target
**lmcache.github.io** (no path). Once DNS resolves and GitHub provisions the TLS
certificate, enable **Enforce HTTPS** in the repository's Pages settings.
GitHub Actions deployments use the Pages settings for the custom domain;
no generated `CNAME` file is required.
