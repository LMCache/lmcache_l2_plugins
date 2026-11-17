# SPDX-License-Identifier: Apache-2.0
# Configuration for the Sphinx documentation builder.

# Standard
from dataclasses import asdict

# Third Party
from sphinxawesome_theme import ThemeOptions

project = "LMCache L2 Plugins"
author = "The LMCache Team"
copyright = "2026, The LMCache Team"

extensions = [
    "sphinx.ext.githubpages",
    "sphinx.ext.autosectionlabel",
    "myst_parser",
    "sphinx_design",
    "sphinxcontrib.mermaid",
]
autosectionlabel_prefix_document = True
myst_enable_extensions = ["colon_fence", "fieldlist"]
language = "en"
exclude_patterns = []

html_title = project
html_theme = "sphinxawesome_theme"
html_logo = "../../asset/logo.png"
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_permalinks_icon = "<span>#</span>"
pygments_style = "sphinx"
pygments_style_dark = "fruity"
html_theme_options = asdict(
    ThemeOptions(
        main_nav_links={
            "GitHub": "https://github.com/LMCache/lmcache_l2_plugins",
            "LMCache docs": "https://docs.lmcache.ai/",
        },
    )
)
