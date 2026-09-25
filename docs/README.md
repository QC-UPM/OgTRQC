# Documentation

Build the English Sphinx site with:

```bash
poetry run sphinx-build -b html -W --keep-going docs/source docs/_build/html
```

The source is `docs/source/`; generated HTML is in `docs/_build/html/`. The site describes supplement generation, numeric inputs, native recalculation and interpretation limits. Historical generated HTML and prototype documentation are no longer part of the working tree.
