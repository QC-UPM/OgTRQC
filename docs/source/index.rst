Hx–NdNiO3 reduced models
==========================

This package implements the modular framework in **Proton Transport and
Polarization Relaxation in Hx–NdNiO3: Literature-Constrained Reduced Models and
a Recoverability Diagnostic**. Its current API is ``octa_gtrqc_sim.proton``.

The physical transport model, independently fitted polarization model, and
recoverability diagnostic answer different questions. Recoverability has zero
coupling to forces and rates. No calibrated dynamical map from concentration
to polarization is assumed.

.. toctree::
   :maxdepth: 2
   :caption: Paper implementation

   paper_models
   architecture
   reproduction
   verification
   supplementary
   api
   publishing

.. toctree::
   :maxdepth: 1
   :caption: Historical prototype (different physical assumptions)

   theory
   software
   results
   comparative
   cptp_evolution
   robustness

Indices
---------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
