Build and publish documentation
===============================

Local build
-----------

.. code-block:: bash

   poetry install
   poetry run sphinx-build -b html -W --keep-going docs/source docs/_build/html

Open ``docs/_build/html/index.html``. The build treats warnings as errors.
Autodoc imports the installed package without executing studies. Google-style
docstrings are processed by Napoleon, and Mermaid diagrams render in the
browser. MathJax and Mermaid assets require network access in the browser.

GitHub Pages
------------

The checked-in ``.github/workflows/docs.yml`` builds from ``docs/source``;
old HTML files at the top of ``docs`` are not its deployment source.

1. Push the reviewed changes to GitHub.
2. In **Settings → Pages → Build and deployment**, select **GitHub Actions**.
3. Allow the default-branch documentation workflow to complete, or dispatch
   it manually on that branch.
4. Inspect the ``github-pages`` deployment environment for the published URL.

The workflow first installs the locked Poetry environment, runs tests, and
builds Sphinx. Pull requests build and test without publishing. Default-branch
runs upload a Pages artifact and deploy it with only the required deployment
permissions. The project-site address is expected to be
``https://QC-UPM.github.io/OgTRQC/`` once a remote deployment succeeds.

This uses GitHub Pages' artifact deployment mechanism, so a generated
``gh-pages`` branch is unnecessary. If an organization requires branch-based
publishing, the same ``docs/_build/html`` output can be published to the root
of that branch with a ``.nojekyll`` file; that alternative is not automated by
this workflow. Do not configure Pages to serve the historical ``docs`` HTML.

See the `GitHub custom-workflow documentation
<https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages>`_
for the repository setting and deployment permission requirements.

Reproducibility workflow
------------------------

``.github/workflows/reproduce.yml`` is a manually dispatched workflow that
executes the full native campaign and compares it with retained numeric
reference results, then uploads the generated results for inspection. It does not publish manuscript changes or
replace the primary holdout with retrospective fits.
