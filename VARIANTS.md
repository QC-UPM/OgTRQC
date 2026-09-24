# Repository variants and relation to the paper

The repository contains one current paper implementation, its original computational reference, and historical prototypes. These categories must remain distinct when reporting scientific results.

| Category | Location | Entry point | Relation to the paper |
| --- | --- | --- | --- |
| Current reusable models | `octa_gtrqc_sim/proton/` | `poetry run proton-study` | Native object-oriented implementation of the declared structural model, frozen transport, independent relaxation, and diagnostics |
| Original computational record | `notebooks/reference/` | `poetry run proton-reference` | Four original notebooks; complete original audit, risk/transfer ensembles and hidden-twin sensor design remain executable here |
| Interactive client | `notebooks/paper_workflow.ipynb` | Poetry Jupyter kernel | Small example using the current API; does not replace the full reference record |
| Native verification outputs | `validation/native/` | Native campaign plus comparison script | Recorded outputs of the migrated models, with artifact manifests |
| Reference verification outputs | `validation/reference/` | Original notebook replay | Compact original outputs and execution records |
| Historical prototype code | Python modules directly under `octa_gtrqc_sim/`, outside `proton/` | `poetry run python -m octa_gtrqc_sim.main` | Earlier quantum-geometric models with different physical assumptions; excluded from paper validation |
| Historical prototype results | `reports_*/`, `robustness_reports/` | Historical CLI | Delay/Hilbert-dimension studies; not the paper's transport or polarization results |
| Current documentation | `docs/source/`, root `README.md` | Sphinx | Paper model, API, provenance and explicitly labelled historical pages |
| Historical narrative | `docs/legacy/README.md` | Archive | Superseded narrative retained for provenance |
| Supplementary material | `supplementary/` | `poetry run python scripts/build_supplement.py` | English LaTeX description of software, scientific correspondence and verification |

## Is the repository aligned?

**The current `proton` variant and its reference workflow are aligned with the supplied paper. The historical engines are not interchangeable implementations of that paper.** In particular, their recoverability-driven geometry conflicts with the paper's exact decoupling of information diagnostics from forces and rates.

Alignment is scoped to what is implemented and tested. The current native transport API builds structure-conditioned generators and propagates normalized probabilities with frozen coefficients. It is not a general nonlinear self-consistent occupancy solver. The relaxation module is independent of transport trajectories. The original large risk, transfer and sensor-selection experiments remain in notebook replay; the native `hidden_state` study is a smaller illustration.

## Directory policy

The current API already has a separate physical directory, `octa_gtrqc_sim/proton/`. Original notebooks and recorded results also have separate directories. Historical code retains its original import paths to preserve existing scripts and tests. This is a deliberate compatibility boundary, not an assertion that everything under the package implements the same physics.

New paper-related models should be added only to `proton/`, new paper results to the current result roots, and original notebook sources should remain unchanged. A future physical relocation of historical modules into a `legacy/` namespace would require compatibility imports; it is not needed to reproduce or describe the paper and has not been performed here.

There is no need to create competing physical variants for the three paper modules: transport, relaxation, and recoverability are complementary components with different responsibilities. Retrospective field folds and finite-mesh versus smooth-reference tests are distinct protocols, not interchangeable evidence categories.
