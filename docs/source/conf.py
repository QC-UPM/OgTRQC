from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

project = 'Hx–NdNiO3 Reduced Models'
copyright = '2026, Universidad Politécnica de Madrid (UPM)'
author = 'Quantum Computing & Smart Materials Group (UPM)'
release = '0.2.0'

# Sphinx Extensions
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.mathjax',
    'sphinx.ext.viewcode',
    'sphinx.ext.githubpages',
    'sphinxcontrib.mermaid',  # Renders the embedded structural diagrams
]

templates_path = ['_templates']
exclude_patterns = []

# Localization
language = 'en'

# UPM Light-Blue Style Configuration
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_paper_static']
html_css_files = [
    'custom_upm.css',  # Forces the institutional blue palette
]

# Ensure MathJax works over CDN on GitHub Pages
mathjax_path = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js'

napoleon_google_docstring = True
napoleon_numpy_docstring = False
autodoc_typehints = "description"
html_title = "Hx–NdNiO3: models and reproducibility"
