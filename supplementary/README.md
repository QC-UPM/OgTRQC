# Supplementary material

`supplementary.tex` is the only maintained LaTeX document. It presents experimental data, methods, additional results, interpretation limits and concise reproduction instructions. It does not contain the paper or historical software-architecture documentation.

Generate everything from the repository root:

```bash
poetry run python scripts/build_supplement.py
```

Outputs are `supplementary.pdf`, seven figure stems in `figures/` (PDF/SVG/PNG), and a delivery manifest. The root README maps each figure to its numeric inputs. The build reads reviewed numeric exports without requiring or executing the original notebooks.

For Overleaf, import `dist/supplementary-overleaf.zip`, choose **supplementary.tex** as the main document and **pdfLaTeX** as compiler. The figures directory is required. `dist/supplementary-reproducibility.zip` additionally contains the numeric inputs, code, tests and lock file.

Edit narrative directly in `supplementary.tex`. Named `BEGIN GENERATED` blocks are refreshed from recorded data; edits inside them will be overwritten. `--no-refresh` preserves those blocks and existing figures during compilation.

Figures for transfer and hidden twins redraw recorded synthetic results; the build does not rerun the full synthetic experiments. Papers and source notebooks remain external, identified by hashes only.
