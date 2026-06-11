import os
import sys
sys.path.insert(0, os.path.abspath('../../'))

project = 'Octahedral gTRQC Simulation Suite'
copyright = '2026, Universidad Politécnica de Madrid (UPM)'
author = 'Quantum Computing & Smart Materials Group (UPM)'
release = '1.0.0'

# Sphinx Extensions
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.mathjax',
    'sphinxcontrib.mermaid',  # Renders the embedded structural diagrams
]

templates_path = ['_templates']
exclude_patterns = []

# Localization
language = 'en'

# UPM Light-Blue Style Configuration
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_css_files = [
    'custom_upm.css',  # Forces the institutional blue palette
]

# Ensure MathJax works over CDN on GitHub Pages
mathjax_path = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js'
