Object-oriented architecture
============================

The package follows the existing repository's Model–View–Presenter (MVP)
pattern. A scientific model never calls a CLI, writes files, or imports a view.
Studies compose models and return ``StudyResult``. ``PaperPresenter`` chooses a
study and delegates presentation to the ``StudyView`` protocol.

.. mermaid::

   classDiagram
       StudyView <|.. ArtifactView
       PaperPresenter --> StudyView
       PaperPresenter --> CalibrationStudy
       PaperPresenter --> IdentifiabilityStudy
       PaperPresenter --> RefinementStudy
       PaperPresenter --> TransportSensitivityStudy
       CalibrationStudy --> RelaxationModel
       CalibrationStudy --> PolarizationDataset
       IdentifiabilityStudy --> RelaxationModel
       RefinementStudy --> TransportModel
       TransportSensitivityStudy --> TransportModel
       TransportModel --> StructuralModel
       TransportModel --> FrozenGenerator
       ArtifactView --> StudyResult
       class StudyView {
           <<interface>>
           +render(result) Path
       }
       class PaperPresenter {
           +run(study) list
       }
       class StudyResult {
           +tables
           +metadata
           +arrays
       }

``StructuralModel`` and ``DeviceConfig`` store dimensioned parameters.
``FrozenGenerator`` exposes sparse evolution and invariant checks.
``RelaxationModel`` owns the field law, optimizer bounds, and fixed starts.
``FitResult`` records the training partition and local covariance.
``PolarizationDataset`` validates the embedded data hash before use.

Scientific dependencies
-----------------------

.. mermaid::

   flowchart LR
       C[Prescribed occupancy] --> S[Two-mode structural closure]
       S --> Q[Local-detailed-balance generator]
       Q --> P[Frozen probability evolution]
       C --> D[Recoverability diagnostic]
       E[Experimental calibration fields] --> R[Relaxation fit]
       R --> H[Held-out polarization prediction]
       R -. Explicit conditional coefficient transfer .-> Q

The diagnostic has no arrow back to the physical dynamics. The relaxation
readout is independent of the propagated probability.

Artifact lifecycle
------------------

.. mermaid::

   sequenceDiagram
       actor User
       User->>PaperPresenter: CLI requests a study
       PaperPresenter->>Study: run()
       Study->>Model: fit or propagate
       Model-->>Study: numerical results
       Study-->>PaperPresenter: StudyResult
       PaperPresenter->>ArtifactView: render(result)
       ArtifactView-->>User: CSV, JSON, NPZ, PDF/SVG, manifest

Publication figure generation is independent of the native study presenter.
``scripts/export_publication_figures.py`` redraws reviewed numeric inputs;
``scripts/render_supplement.py`` embeds tables and profiles in the LaTeX source.
The build needs neither original notebooks nor a manuscript file.
