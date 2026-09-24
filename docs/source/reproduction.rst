Reproduction and provenance
===========================

Environment
-----------

From the repository root:

.. code-block:: bash

   poetry install
   poetry run proton-study --study calibration
   poetry run pytest -q

The lock file fixes the scientific and documentation dependencies. Notebook
replay additionally uses the development-group Jupyter packages installed by
the default command. Native imports have no notebook execution side effects.

For predictable numerical-thread allocation on shared systems, optional
``OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1`` can prefix commands. Numerical
comparisons use tolerances rather than claiming bitwise portability across
BLAS implementations and SciPy versions.

Native campaign
---------------

.. code-block:: bash

   poetry run proton-study --study all --output paper_results

The following tasks are individually selectable with ``--study``:

.. list-table:: Executable study map
   :header-rows: 1
   :widths: 25 45 30

   * - Study
     - Output
     - Source
   * - calibration
     - Original three-model strict holdout
     - v3.1
   * - uncertainty
     - 100 residual-bootstrap refits and prediction bands
     - v3.1
   * - identifiability
     - Correlation, original alpha grid, five extra profiles
     - R2.5
   * - review
     - Four field folds, biexponential, information criteria
     - Review addendum
   * - start_sensitivity
     - Original-model optimizer-start audit
     - Review addendum
   * - transport_sensitivity
     - Independent coefficient sweep and frozen checks
     - Review addendum
   * - continuum
     - Constant-D matched-generator convergence
     - v3.1 section 9
   * - refinement
     - Full-generator R3 refinement and parity counterexample
     - R3
   * - hidden_state
     - Small synthetic reflected-pair illustration
     - Native illustration of the diagnostic boundary

``--original-profile-only`` omits the five additional nuisance profiles.
``--bootstrap-repetitions`` changes the number of refits; the paper uses 100.
``--reference-cells`` changes the R3 reference mesh; the paper uses 8192 with
a 4096-cell doubling check. Reduced settings are not the full paper experiment.

The original alpha interval is retained as an accepted-grid interval, not
replaced by interpolated endpoints. The additional five intervals record all
nuisance fits and their convergence diagnostics.

Full notebook record
--------------------

.. code-block:: bash

   poetry run proton-reference --output reference_results
   poetry run proton-reference --notebook proton_R2_5_identifiability.ipynb

The four notebooks under ``notebooks/reference`` retain their original bytes.
Their SHA-256 hashes are checked before execution. The runner saves executed
copies even on failure, writes ``execution.json``, and closes each kernel.
The interpreter is the same Python used by Poetry, rather than an arbitrary
system Jupyter kernel. Per-cell timeout defaults to 3600 seconds.

The v3.1 replay appends an export cell only to its executed copy. This exports
the complete machine-readable summary and pandas tables, including the
80-gate audit and synthetic risk, ablation, transfer, and hidden-twin studies.
These original analyses remain available rather than being approximated by
the smaller native reflected-pair example.

The R3 source notebook's second cell redraws recorded embedded evidence; it
is not a fresh calibration fit. Native figures, in contrast, are rendered
from the current ``StudyResult`` tables.

Data boundary
-------------

The bundled numerical matrix is the 87 by 12 matrix embedded in the supplied
v3.1 notebook, originating from the publisher data for
`DOI 10.1038/s41467-024-49213-0 <https://doi.org/10.1038/s41467-024-49213-0>`_.
The matrix hash is
``859f76869eb087bc05e0aba24f3543bddb90b03842d10bb49d0dc66d1814354a``.
The time column is converted from milliseconds to seconds. The raw 133 kV/cm
trace is divided by its first value; the other three normalized traces use
the notebook's selected columns. The original clipping to [0, 1.2] is retained.
Publisher fitted curves are not used in native model calibration.

The original workbook hash is retained as inherited provenance. The workbook
itself is not bundled, and replay does not download it. Literature claims
inside the notebooks are source records, not new external verification.

Artifacts and supplementary material
-------------------------------------

Each native study exports CSV tables, JSON metadata and environment versions,
optional compressed numeric arrays, and relevant PDF/SVG figures. A manifest
hashes the generated files; no timestamp is required for numerical identity.
Metadata distinguishes primary holdout, retrospective comparisons, synthetic
examples, and conditional transport assumptions.

The self-contained LaTeX supplement uses these recorded artifacts to embed
its tables and plot coordinates directly in one Overleaf-ready source file.
Its bibliography and all sections are inline; external images and data files
are unnecessary for compilation. See :doc:`supplementary` for downloads and
refresh/build instructions.
