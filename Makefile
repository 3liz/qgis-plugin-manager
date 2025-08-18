.PHONY: test dist

PYTHON=python3

PYTHON_PKG=qgis_plugin_manager
TESTDIR=tests


dist: clean
	$(PYTHON) -m build --no-isolation --sdist

clean:
	rm -rf *.egg-info ./dist

install: 
	pip install -U --upgrade-strategy=eager -e .

install-dev:
	pip install -U --upgrade-strategy=eager -r requirements-dev.txt

test:
	cd $(TESTDIR) && pytest -v

lint:
	@ruff check $(PYTHON_PKG) $(TESTDIR)

lint-preview:
	@ruff check --preview $(PYTHON_PKG) $(TESTDIR)

lint-fix:
	@ruff check --fix --preview $(PYTHON_PKG) $(TESTDIR)
