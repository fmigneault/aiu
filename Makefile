MAKEFILE_NAME := $(word $(words $(MAKEFILE_LIST)),$(MAKEFILE_LIST))
# Include custom config if it is available
-include Makefile.conf

# Application
APP_ROOT    := $(abspath $(lastword $(MAKEFILE_NAME))/..)
REPORTS_DIR ?=  $(APP_ROOT)/reports

## --- Versioning targets --- ##

# Bumpversion 'dry' config
# if 'dry' is specified as target, any bumpversion call using 'BUMP_XARGS' will not apply changes
BUMP_XARGS ?= --verbose --allow-dirty
ifeq ($(filter dry, $(MAKECMDGOALS)), dry)
	BUMP_XARGS := $(BUMP_XARGS) --dry-run
endif

.PHONY: dry
dry: setup.cfg	## run 'bump' target without applying changes (dry-run)
ifeq ($(findstring bump, $(MAKECMDGOALS)),)
	$(error Target 'dry' must be combined with a 'bump' target)
endif

.PHONY: bump
bump:	## bump version using VERSION specified as user input (make VERSION=<X.Y.Z> bump)
	@-echo "Updating package version ..."
	@[ "${VERSION}" ] || ( echo ">> 'VERSION' is not set"; exit 1 )
	@-test -f "$(CONDA_ENV_PATH)/bin/bump2version" || pip install $(PIP_XARGS) bump2version
	@-bump2version $(BUMP_XARGS) --new-version "${VERSION}" patch;

## --- Installation targets --- ##

.PHONY: install-dep
install-dep:
	pip install -r "$(APP_ROOT)/requirements.txt"

.PHONY: install-pkg
install-pkg:
	pip install --no-depds -e "$(APP_ROOT)"

.PHONY: install
install: install-dep install-pkg

.PHONY: install-dev
install-dev: install-dep
	pip install -r "$(APP_ROOT)/requirements-dev.txt"
	pip install -e "$(APP_ROOT)"

## --- Cleanup targets --- ##

.PHONY: clean
clean: clean-all	## alias for 'clean-all' target

.PHONY: clean-all
clean-all: clean-build clean-pyc clean-test clean-report		## remove all artifacts

.PHONY: clean-build
clean-build:	## remove build artifacts
	@echo "Cleaning build artifacts..."
	@-rm -fr build/
	@-rm -fr dist/
	@-rm -fr downloads/
	@-rm -fr .eggs/
	@find . -type d -name '*.egg-info' -exec rm -fr {} +
	@find . -type f -name '*.egg' -exec rm -f {} +

.PHONY: clean-pyc
clean-pyc:		## remove Python file artifacts
	@echo "Cleaning Python artifacts..."
	@find . -type f -name '*.pyc' -exec rm -f {} +
	@find . -type f -name '*.pyo' -exec rm -f {} +
	@find . -type f -name '*~' -exec rm -f {} +
	@find . -type f -name '__pycache__' -exec rm -fr {} +

.PHONY: clean-report
clean-report: 	## remove check linting reports
	@echo "Cleaning check linting reports..."
	@-rm -fr "$(REPORTS_DIR)"

.PHONY: clean-test
clean-test: clean-report	## remove test and coverage artifacts
	@echo "Cleaning tests artifacts..."
	@-rm -fr .tox/
	@-rm -fr .pytest_cache/
	@-rm -f .coverage*
	@-rm -f coverage.*
	@-rm -fr "$(APP_ROOT)/coverage/"
	@-rm -fr "$(APP_ROOT)/node_modules"
	@-rm -f "$(APP_ROOT)/package-lock.json"

## --- Testing targets --- ##

.PHONY: mkdir-reports
mkdir-reports:
	@mkdir -p "$(REPORTS_DIR)"

# autogen check variants with pre-install of dependencies using the '-only' target references
CHECKS := pep8 lint security security-code security-deps doc8 links imports css
CHECKS := $(addprefix check-, $(CHECKS))

$(CHECKS): check-%: install-dev check-%-only

.PHONY: check
check: install-dev $(CHECKS)  ## run code checks (alias to 'check-all' target)

# undocumented to avoid duplicating aliases in help listing
.PHONY: check-only
check-only: check-all-only

.PHONY: check-all-only
check-all-only: $(addsuffix -only, $(CHECKS))  ## run all code checks
	@echo "All checks passed!"

.PHONY: check-pep8-only
check-pep8-only: mkdir-reports		## run PEP8 code style checks
	@echo "Running PEP8 code style checks..."
	@-rm -fr "$(REPORTS_DIR)/check-pep8.txt"
	@$(CONDA_CMD) \
		flake8 --config="$(APP_ROOT)/setup.cfg" --output-file="$(REPORTS_DIR)/check-pep8.txt" --tee

.PHONY: check-lint-only
check-lint-only: mkdir-reports		## run linting code style checks
	@echo "Running linting code style checks..."
	@-rm -fr "$(REPORTS_DIR)/check-lint.txt"
	@pylint \
			--rcfile="$(APP_ROOT)/pylint.ini" \
			--reports y \
			"$(APP_ROOT)/$(APP_NAME)" "$(APP_ROOT)/tests" \
		1> >(tee "$(REPORTS_DIR)/check-lint.txt")

.PHONY: check-security-only
check-security-only: check-security-code-only check-security-deps-only  ## run security checks

# ignored codes:
#	42194: https://github.com/kvesteri/sqlalchemy-utils/issues/166  # not fixed since 2015
#	51668: https://github.com/sqlalchemy/sqlalchemy/pull/8563  # still in beta + major version change sqlalchemy 2.0.0b1
.PHONY: check-security-deps-only
check-security-deps-only: mkdir-reports  ## run security checks on package dependencies
	@echo "Running security checks of dependencies..."
	@-rm -fr "$(REPORTS_DIR)/check-security-deps.txt"
	@safety check \
			-r "$(APP_ROOT)/requirements.txt" \
			-r "$(APP_ROOT)/requirements-dev.txt" \
			-i 42194 \
			-i 51668 \
		1> >(tee "$(REPORTS_DIR)/check-security-deps.txt")

.PHONY: check-security-code-only
check-security-code-only: mkdir-reports  ## run security checks on source code
	@echo "Running security code checks..."
	@-rm -fr "$(REPORTS_DIR)/check-security-code.txt"
	@bandit -v --ini "$(APP_ROOT)/setup.cfg" -r \
		1> >(tee "$(REPORTS_DIR)/check-security-code.txt")

.PHONY: check-docs-only
check-docs-only: check-doc8-only check-docf-only	## run every code documentation checks

.PHONY: check-doc8-only
check-doc8-only: mkdir-reports		## run PEP8 documentation style checks
	@echo "Running PEP8 doc style checks..."
	@-rm -fr "$(REPORTS_DIR)/check-doc8.txt"
	@doc8 --config "$(APP_ROOT)/setup.cfg" "$(APP_ROOT)/docs" \
		1> >(tee "$(REPORTS_DIR)/check-doc8.txt")

# FIXME: move parameters to setup.cfg when implemented (https://github.com/myint/docformatter/issues/10)
# NOTE: docformatter only reports files with errors on stderr, redirect trace stderr & stdout to file with tee
# NOTE:
#	Don't employ '--wrap-descriptions 120' since they *enforce* that length and rearranges format if any word can fit
#	within remaining space, which often cause big diffs of ugly formatting for no important reason. Instead only check
#	general formatting operations, and let other linter capture docstrings going over 120 (what we really care about).
.PHONY: check-docf-only
check-docf-only: mkdir-reports	## run PEP8 code documentation format checks
	@echo "Checking PEP8 doc formatting problems..."
	@-rm -fr "$(REPORTS_DIR)/check-docf.txt"
	@docformatter \
			--pre-summary-newline \
			--wrap-descriptions 0 \
			--wrap-summaries 120 \
			--make-summary-multi-line \
			--check \
			--recursive \
			"$(APP_ROOT)" \
		1>&2 2> >(tee "$(REPORTS_DIR)/check-docf.txt")

.PHONY: check-imports-only
check-imports-only: mkdir-reports	## run imports code checks
	@echo "Running import checks..."
	@-rm -fr "$(REPORTS_DIR)/check-imports.txt"
	@isort --check-only --diff --recursive $(APP_ROOT) \
		1> >(tee "$(REPORTS_DIR)/check-imports.txt")

# autogen tests variants with pre-install of dependencies using the '-only' target references
TESTS := cli local
TESTS := $(addprefix test-, $(TESTS))
TEST_VERBOSITY ?= -vvv
TEST_LOG_LEVEL ?= ll

$(TESTS): test-%: install install-dev test-%-only

.PHONY: test
test: clean-test test-all   ## run tests (alias for 'test-all' target)

.PHONY: test-all
test-all: install install-dev test-only  ## run all tests (including long running tests)

.PHONY: test-only
test-only: mkdir-reports		 ## run all tests combinations without pre-installation of dependencies
	@echo "Running tests..."
	@pytest tests \
		$(TEST_VERBOSITY) \
		$(TEST_LOG_LEVEL) \
		--junitxml "$(APP_ROOT)/tests/results.xml"
