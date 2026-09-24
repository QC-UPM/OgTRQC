Supplementary material and repository variants
===============================================

The current paper implementation is ``octa_gtrqc_sim/proton/``. The original
notebook computational record is under ``notebooks/reference/``. Historical
quantum-geometric engines remain at their original import paths and are
explicitly excluded from the current paper's physical interpretation. The
repository-level ``VARIANTS.md`` maps these categories and their output folders.

Single-file Overleaf document
-----------------------------

The English supplementary material documents the equation-to-code mapping,
class architecture, native/reference coverage, units, inference protocols,
recorded validation and provenance.

* :download:`Standalone LaTeX source <../../supplementary/main.tex>`
* :download:`Compiled review PDF <../../supplementary/supplementary_material.pdf>`
* :download:`Repository variant map <../../VARIANTS.md>`

Upload only ``main.tex`` to Overleaf and select **pdfLaTeX**. All sections,
bibliography entries, tables, TikZ diagrams and PGFPlots coordinates are
embedded. No external figures, data files or bibliography files are required.

Repository maintenance
----------------------

.. code-block:: bash

   poetry run python scripts/update_supplement.py
   poetry run python scripts/build_supplement.py

The updater reads recorded results after checking their manifests; it does not
refit models. Only named generated blocks in the source are replaced. The
builder tests self-containment by compiling the file in an otherwise empty
temporary directory. Use ``--no-refresh`` to compile an edited source without
refreshing embedded evidence. These scripts are not required on Overleaf.

The supplement describes a working-tree source snapshot and the recorded
verification. It does not assert an already published repository tag or DOI.
