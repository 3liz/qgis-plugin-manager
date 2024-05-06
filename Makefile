.PHONY: test

PYTHON_PKG=qgis_plugin_manager
TESTDIR=test

test:
	cd test && python3 -m unittest

lint:
	@ruff check $(PYTHON_PKG) $(TESTDIR)

lint-preview:
	@ruff check --preview $(PYTHON_PKG) $(TESTDIR)

lint-fix:
	@ruff check --fix --preview $(PYTHON_PKG) $(TESTDIR)
