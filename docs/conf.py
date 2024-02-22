"""Sphinx configuration."""
project = "django-prodserver"
author = "Andrew Miller"
copyright = "2024, Andrew Miller"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_click",
    "myst_parser",
]
autodoc_typehints = "description"
html_theme = "furo"
