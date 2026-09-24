# Recorded integration verification

This directory records a complete native campaign and fresh executions of all four supplied notebooks in the locked Poetry environment. These are computational regression records, not independent experiments.

- All **24 automated tests** passed at integration, including holdout separation, analytic-Jacobian checks, physical invariants, and direct comparison with the original generator function.
- All four archived notebooks executed successfully. The original v3.1 audit passed **80/80** gates.
- All **22 migration comparisons** passed; see [migration.json](migration.json) for residuals and explicit tolerances.
- All **100 calibration-residual bootstrap refits** converged.
- The five R2.5 additional profile endpoints agree within approximately **7.2e-12** in this run.
- Primary holdout RMSE is **0.0263372453**, R² is **0.9908061998**.
- Constant-D observed order is **2.02908**. R3 full-generator orders are **2.00309** for the symmetric background and **1.00164** for the ramp.

`native/` contains portable CSV, JSON, NPZ, PDF/SVG and artifact manifests. `reference/` contains execution-status records, the complete original summary and audit table, and compact review/R2.5/R3 outputs. Full executed notebooks can be regenerated; their original source copies are in `notebooks/reference/`.

## Regenerate and compare

```bash
poetry run proton-study --study all --output paper_results
poetry run proton-reference --output reference_results
poetry run python scripts/verify_migration.py \
  --native paper_results --reference reference_results \
  --output validation/migration.json
```

Numerical tolerances account for BLAS, eigensolver, and optimizer roundoff. Notebook hashes and the data matrix hash validate source identity; PDF/NPZ container bytes need not be identical across executions. A difference in output hashes alone is not a numerical failure.

The original notebook's stronger historical wording in `reference/summary.json` is retained for provenance. Use the manuscript-aligned model boundaries in the current documentation when interpreting those values.
