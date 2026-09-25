# Numeric evidence and verification

`native/` contains the reviewed native CSV/JSON/NPZ results and diagnostic figures. `reference/` contains compact review, identifiability and frozen-generator exports from the external computational record. Neither directory contains notebook sources or the paper.

```bash
poetry run proton-study --study all --output generated/native
poetry run python scripts/verify_results.py --native generated/native
```

The current checker compares the recalculated results with retained numeric references and writes `generated/verification.json`. It does not execute source notebooks. Tolerances account for optimizer and eigensolver roundoff. Input hashes and numerical agreement are different checks.

`migration.json` is the historical 22-check migration record, which included original notebook execution and the original 80-gate audit. It is preserved as a dated source-comparison record, not presented as a new execution by this repository. Current package tests and current numeric comparisons report their own results and counts.
