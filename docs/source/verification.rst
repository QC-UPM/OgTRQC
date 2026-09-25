Verification scope
==================

.. code-block:: bash

   poetry run pytest -q
   poetry run python scripts/verify_results.py --native validation/native

Tests check holdout isolation, the analytic Jacobian, physical invariants,
mesh-parity limitations and agreement with an independent numeric generator
fixture. No test loads source notebooks.

The current numerical checker compares native results with compact reviewed
reference outputs. ``validation/migration.json`` preserves the historical
22-check migration record, which included the external 80-gate source audit.
Those historical counts are separate from the tests and comparisons run by
the current repository. None is an additional physical experiment.

Rendered-file hashes check identity; tolerance-based comparisons check
numerical agreement. Synthetic transfer and hidden-twin figures are recorded
result redraws, not new ensemble runs.
