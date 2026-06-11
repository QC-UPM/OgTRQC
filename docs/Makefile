SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = source
BUILDDIR      = ..

help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help html clean

html:
	$(SPHINXBUILD) -b html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS)
	@touch ../.nojekyll
	@echo "Documentation compiled successfully. The .nojekyll bypass is active for github.io deployment."

clean:
	rm -rf ../*.html ../_static ../_sources ../.buildinfo ../objects.inv ../searchindex.js ../search.html ../.nojekyll
