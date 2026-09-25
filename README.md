# Supplementary material and publication figures

This repository generates the supplementary material and figures for **Proton Transport and Polarization Relaxation in Hx–NdNiO3: Literature-Constrained Reduced Models and a Recoverability Diagnostic**. Documentation, tables and figure labels are in English.

The paper, response letter and original notebooks are external sources. They are not stored or executed here. Their SHA-256 identities are retained in `data/provenance.json`. Historical quantum-geometric prototypes and their reports are outside the current working tree; Git history is not rewritten.

## Generate the complete delivery

```bash
poetry install
poetry run python scripts/build_supplement.py
```

Python dependencies are locked in `poetry.lock`. Local PDF compilation also requires pdfLaTeX with TikZ/PGFPlots. No paper, notebook, bibliography download or network connection is needed after installing dependencies.

| Generated artifact | Location | Purpose |
| --- | --- | --- |
| Editable supplement | `supplementary/supplementary.tex` | Scientific narrative, automatically refreshed tables and profile coordinates |
| Compiled supplement | `supplementary/supplementary.pdf` | Reader-facing supplementary material |
| Seven publication figures | `supplementary/figures/` | Each figure in PDF, SVG and PNG |
| Figure manifest | `supplementary/figures/manifest.json` | Hashes of rendered graphics |
| Delivery manifest | `supplementary/manifest.json` | Source/evidence/output identities and base commit |
| Overleaf ZIP | `dist/supplementary-overleaf.zip` | `supplementary.tex`, README and required PDF figures; choose supplementary.tex as the main file |
| Reproducibility ZIP | `dist/supplementary-reproducibility.zip` | Current source, numeric inputs, tests, locked environment and outputs; excludes external manuscripts and notebooks |

## How generation works

1. `scripts/evidence.py` verifies `data/manifest.json` and the recorded native artifact manifests.
2. `scripts/export_publication_figures.py` reads `data/figure_inputs.json` and compact refinement results. It redraws the seven reviewed figures without refitting.
3. `scripts/render_supplement.py` reads `validation/native/` to refresh named generated blocks in `supplementary.tex`. Narrative outside those blocks remains editable.
4. `scripts/build_supplement.py` compiles the source and delivered figures in an otherwise empty directory, checks cross-references and writes the PDF.
5. `scripts/package_supplement.py` writes the delivery manifest and the two ZIPs.

Use `--no-refresh` to compile edited source and existing figures without regenerating them. Use `--no-package` to skip ZIP creation. Standalone figure export is available with `poetry run python scripts/export_publication_figures.py`.

## Figure map

| Figure stem | Input and logic | Interpretation |
| --- | --- | --- |
| `proton_holdout` | Time, observations, four recorded predictions and calibration-only pointwise interval in `data/figure_inputs.json` | 533 kV/cm holdout; biexponential is retrospective |
| `proton_full_convergence` | `validation/reference/refinement/full_generator_refinement.csv` | Relative spatial error for symmetric and gradient frozen backgrounds |
| `proton_full_gaps` | Same CSV plus its `summary.json` lower bound | Frozen-generator spectral gaps; not nonlinear stability |
| `supp_polarization_residuals` | Recorded prediction minus observation | Distributed-relaxation and biexponential residuals |
| `supp_structural_curvature` | Recorded [001]/[111] curvature inputs and separate log-linear fits | Scalar interpolation, not transferable full-Hessian validation |
| `supp_recoverability_transfer` | Recorded synthetic ROC-AUC values | Redraw of protocol-transfer results; no ensemble rerun |
| `supp_hidden_twins` | Recorded separation arrays; empirical cumulative distributions | Synthetic sensor-design record; not experimental detection |

The six parameter profiles and numerical comparison tables are embedded directly in the LaTeX source from `validation/native/identifiability/` and `validation/native/review/`. Their complete numeric values, nuisance optima and correlation matrix remain accessible in those directories.

## Optional independent recalculation

```bash
poetry run proton-study --study all --output generated/native
poetry run python scripts/verify_results.py --native generated/native
poetry run pytest -q
poetry run sphinx-build -b html -W --keep-going docs/source docs/_build/html
```

Recalculation writes `generated/native/` and comparisons write `generated/verification.json`; it does not silently replace reviewed inputs. The reference comparison uses retained numeric exports, not notebook execution. The native `hidden_state` example illustrates reflected profiles and does not reproduce the original full AUC, distribution-shift or sensor-selection campaigns.

The current tests, historical 80-gate source audit and historical 22 migration checks are distinct verification layers. The old migration record remains at `validation/migration.json`; current `verify_results.py` reports its own count and scope. Removing the external-source execution checks does not turn them into current tests.

## Scientific boundaries

- The 47.3% improvement applies only to 533 kV/cm against stretched exponential. Pooled four-field reductions are 13.12% against stretched exponential and 9.22% against biexponential; the biexponential wins at 133 kV/cm.
- Relaxation is phenomenological and independently fitted. It neither identifies a microscopic mechanism nor independently calibrates transport.
- Recoverability is diagnostic and does not enter force or hopping rates.
- The transport sweep preserves detailed balance but changes the homogeneous characteristic time by about 56.78. It is not an experimental confidence interval or a revalidation of synthetic protocols.
- Constant-D order 2.029 is separate from full frozen-generator orders 2.003 and 1.002. Positive gaps do not repair mesh parity or prove nonlinear stability.
- The reference Hessian is unstrained [001]; [111] is interpolated separately. Sampled strain is not a universal stability domain.

See [numeric input documentation](data/README.md), [supplement instructions](supplementary/README.md), and [validation scope](validation/README.md).

## Delivery verification

The current delivery passed 22 package tests and 20 numeric comparisons after a complete native recalculation in a clean ZIP extraction. The supplement and all seven figures rebuilt without the paper or source notebooks. Sphinx also built with warnings treated as errors. See `validation/delivery_check.json`.

```bash
poetry run python scripts/verify_delivery.py --recalculate
```

This uses the installed Poetry interpreter; it does not claim a fresh dependency installation. The historical migration counts remain separately identified above.
