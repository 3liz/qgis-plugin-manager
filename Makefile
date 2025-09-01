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

test: lint typing
	$(MAKE) -C tests

lint:
	@ruff check --output-format=concise $(PYTHON_PKG) $(TESTDIR)

lint-preview:
	@ruff check --preview $(PYTHON_PKG) $(TESTDIR)

lint-fix:
	@ruff check --fix --preview $(PYTHON_PKG) $(TESTDIR)

typing:
	@mypy -p $(PYTHON_PKG)

format-diff:
	@ruff format --diff $(PYTHON_PKG) $(TESTDIR)

format:
	@ruff format $(PYTHON_PKG) $(TESTDIR) 
