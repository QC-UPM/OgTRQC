# Notebook integration and provenance

`paper_workflow.ipynb` is a short client of the native package API, suitable for interactive exploration.

`reference/` contains the four user-supplied notebooks without source or output modifications. `reference/manifest.json` records their SHA-256 digests. The package extracts experimental data into `octa_gtrqc_sim/proton/data/` and provides reusable object-oriented implementations of the main models and revision studies.

```bash
poetry run proton-reference --output reference_results
poetry run proton-reference --notebook proton_R3_full_generator_audit.ipynb
```

Run from the repository root, with `poetry install` completed. The runner checks the source hash, uses the Poetry Python interpreter, fails on notebook errors, and writes each executed notebook to its own directory. The original 80-gate audit remains in the full v3.1 replay. A final export cell is appended to the **executed copy only** to serialize its completed summary and all pandas tables. `execution.json` records success, runtime, interpreter, and source hash.

The R3 plotting cell redraws evidence embedded in that notebook; it does not refit the experimental data. The R2.5 notebook profiles a fixed residual-scale objective. The review addendum contains retrospective fits that are separate from the strict 533 kV/cm evaluation. Retain these distinctions when using generated figures or tables.

The native `proton-study` command is the preferred reusable interface. See the root README for the explicit mapping between native studies and the parts retained only in full notebook replay.
