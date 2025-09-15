.PHONY: test dist

PYTHON=python3

PYTHON_MODULE=qgis_plugin_manager
TESTDIR=tests

-include .localconfig.mk

#
# Configure
#

ifeq ($(USE_UV), 1)
UV_RUN ?= uv run
endif

REQUIREMENTS=\
	dev \
	lint \
	tests \
	packaging \
	$(NULL)

.PHONY: update-requirements

update-requirements: $(patsubst %, update-requirements-%, $(REQUIREMENTS))

# Require uv (https://docs.astral.sh/uv/) for extracting
# infos from project's dependency-groups
update-requirements-tests:
	@echo "Updating requirements for 'tests'"; \
	uv export --no-dev --group tests --format requirements.txt \
		--no-annotate \
		--no-editable \
		--no-hashes \
		-q -o requirements/tests.txt; \

update-requirements-%:
	@echo "Updating requirements for '$*'"; \
	uv export --format requirements.txt \
		--no-annotate \
		--no-editable \
		--no-hashes \
		--only-group $*\
		-q -o requirements/$*.txt; \

#
# Static analysis
#

LINT_TARGETS=$(PYTHON_MODULE) $(TESTDIR)  $(EXTRA_LINT_TARGETS)

lint:
	@ $(UV_RUN) ruff check --preview  --output-format=concise $(LINT_TARGETS)

lint-preview:
	@ruff check --preview $(LINT_TARGETS)

lint-fix:
	@ $(UV_RUN) ruff check --preview --fix $(LINT_TARGETS)

format:
	@ $(UV_RUN) format $(LINT_TARGETS) 

format-diff:
	@ $(UV_RUN) format --diff $(LINT_TARGETS) 

typecheck:
	@ $(UV_RUN) mypy $(LINT_TARGETS)

#
# Tests
#

test:
	cd tests && $(UV_RUN) pytest -v

#
# Packaging
#

dist: clean
	$(PYTHON) -m build --no-isolation --sdist

clean:
	rm -rf *.egg-info ./dist
