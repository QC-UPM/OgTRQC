Generation and recalculation
============================

Install the locked Python environment with ``poetry install``. Local supplement
compilation also needs pdfLaTeX with TikZ/PGFPlots.

.. code-block:: bash

   poetry run python scripts/build_supplement.py

The default build reads reviewed numeric inputs. It does not refit models or
execute external documents. The root README maps every figure to its inputs.

For independent native recalculation:

.. code-block:: bash

   poetry run proton-study --study all --output generated/native
   poetry run python scripts/verify_results.py --native generated/native

The comparison report is ``generated/verification.json``. Reviewed inputs in
``validation/native/`` are not overwritten. The full native campaign includes
100 bootstrap refits and the 8192-cell refinement reference. The native
hidden-state example is a reflected-profile illustration, not a rerun of the
full original risk or sensor-selection studies.

Original paper and notebook identities are in ``data/provenance.json``. Only
their compact numerical outputs are retained in the working tree.
