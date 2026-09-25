Generated supplement and figures
================================

.. code-block:: bash

   poetry run python scripts/build_supplement.py

* :download:`Editable supplementary.tex <../../supplementary/supplementary.tex>`
* :download:`Compiled supplementary PDF <../../supplementary/supplementary.pdf>`
* :download:`Output and figure map <../../README.md>`
* :download:`Numeric input documentation <../../data/README.md>`

The build verifies input hashes, redraws seven figures, embeds recorded tables
and profile curves, compiles the supplement, then packages both deliveries.

``supplementary/figures/`` contains PDF, SVG and PNG outputs.
``dist/supplementary-overleaf.zip`` contains supplementary.tex and its required
PDF figures. Select supplementary.tex as the main document and pdfLaTeX as
compiler. ``dist/supplementary-reproducibility.zip`` adds code, numeric inputs,
tests and the locked environment. Neither ZIP contains the paper or notebooks.

The four supplementary review figures cover residuals, structural curvature,
synthetic recoverability transfer and hidden-twin separation. The remaining
three figures show the four-model holdout, full-generator refinement and gaps.
Synthetic figures redraw retained outputs without rerunning the original full
ensemble or sensor-selection protocols.
