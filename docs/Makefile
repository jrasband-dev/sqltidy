# Makefile for Sphinx documentation
#
# You can set these variables from the command line.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
PAPER         ?=
BUILDDIR      ?= _build

# User-facing targets
.PHONY: help Makefile html clean

# Put it first so that "make" without argument is not special.
help:
	@$(SPHINXBUILD) -M help "$(CURDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

# Default target - build HTML documentation
html:
	@$(SPHINXBUILD) -M html "$(CURDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@echo ""
	@echo "Build finished. The HTML documentation is in $(BUILDDIR)/html"

# Clean build directory
clean:
	@rm -rf "$(BUILDDIR)"

# Catch-all target: route all unknown targets to Sphinx
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(CURDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
