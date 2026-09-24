# Sphinx documentation

The publication source is `source/`. Build with the locked Poetry environment:

```bash
poetry install
poetry run sphinx-build -b html -W --keep-going docs/source docs/_build/html
```

Open `docs/_build/html/index.html`. Google docstrings are rendered by `sphinx.ext.napoleon` and `sphinx.ext.autodoc`; Mermaid diagrams use `sphinxcontrib.mermaid`.

The GitHub Pages workflow builds and deploys this output directory. Old generated HTML files at the top of `docs/` are historical artifacts and are not the workflow's deployment source. `legacy/README.md` preserves the superseded quantum-geometric narrative for provenance.

See `source/publishing.rst` for Pages setup and `source/reproduction.rst` for scientific execution. Scientific figures are exported as PDF and SVG so they can later be included in a LaTeX supplementary document.
