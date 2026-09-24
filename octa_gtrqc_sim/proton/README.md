# Paper-aligned implementation

This namespace implements the classical reduced-model framework of the supplied proton-transport paper. `structure.py` and `transport.py` provide physical models; `relaxation.py` fits the independent polarization readout; `diagnostics.py` evaluates information loss without feeding it back into dynamics.

`studies.py`, `identifiability.py`, and `audits.py` compose reproducible protocols. `presentation.py` and `cli.py` implement Model–View–Presenter orchestration. `reference.py` replays the full original computational record independently of the native models. `dataset.py` verifies and loads the packaged experimental matrix in `data/`.

See the root README and `VARIANTS.md` for execution commands, the boundary with historical modules, and the analyses retained only in full notebook replay.
