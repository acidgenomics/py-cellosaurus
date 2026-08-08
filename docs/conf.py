"""Sphinx configuration for py-cellosaurus."""

project = "cellosaurus"
author = "Michael Steinbaugh"
copyright = "Acid Genomics"
extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "numpydoc",
]
autosummary_generate = True
autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
}
napoleon_numpy_docstring = True
napoleon_google_docstring = False
numpydoc_show_class_members = False
html_theme = "pydata_sphinx_theme"
html_theme_options = {
    "github_url": "https://github.com/acidgenomics/py-cellosaurus",
    "logo": {"text": "cellosaurus"},
}
html_css_files = ["https://python.acidgenomics.com/css/sphinx.css"]
html_show_sourcelink = False
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pandas": ("https://pandas.pydata.org/docs", None),
}
