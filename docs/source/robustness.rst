Robustness Study Workflow
=========================

The repository includes a delay-focused robustness workflow for the ``quantum``
engine. The purpose of this study is to probe whether the observed delay trend
is stable under targeted one-at-a-time perturbations of the numerical and
physical configuration.

Parameters varied in the default study
--------------------------------------

The current study perturbs the following quantities around the baseline
configuration:

* time step (``time_step``),
* initial visible-state population (``initial_density_population``),
* feedback stiffness (``g_oct_stiffness``),
* dephasing strength (``dephasing_gamma``),
* numerical tolerance (``numerical_tolerance``),
* initial geometry amplitudes (``initial_register``),
* graph topology (``topology``).

The delay values tested by default are ``0``, ``1``, ``2``, and ``5`` steps.

How to run the study
--------------------

The robustness workflow is exposed as a standalone Python module:

.. code-block:: bash

   python -m octa_gtrqc_sim.robustness -c config.yaml -o robustness_reports

Outputs
-------

The study writes three output artifacts into the selected directory:

* ``robustness_quantum_delay_study.json``,
* ``robustness_quantum_delay_study.csv``,
* ``robustness_quantum_delay_study.md``.

These files contain per-scenario and per-delay summaries of final matter
observable values, peak and mean distortion, effective-source statistics, and
the embedded null-test outcome.

Current limitation
------------------

The present proof of concept now exposes several built-in six-node graph
topologies through reduced topology-aware couplings. The resulting topology
comparison is informative, but it should still be interpreted cautiously
because the reduced engines do not all carry a full node-resolved graph state.
