# Native supplement calculations

`structure.py` and `transport.py` implement the reduced physical models. `relaxation.py` fits the independent polarization readout. `diagnostics.py` evaluates recoverability without feeding it into dynamics.

`studies.py`, `identifiability.py` and `audits.py` implement numerical protocols. `presentation.py` and `cli.py` export their tables and diagnostic figures. `dataset.py` verifies the packaged experimental matrix. No notebook runner is required.

Use `poetry run proton-study --study all --output generated/native` for independent recalculation. The publication figure redraw is separate: see `scripts/export_publication_figures.py` and the root README.
