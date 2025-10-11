MAKEFILE_NAME := $(word $(words $(MAKEFILE_LIST)),$(MAKEFILE_LIST))
# Include custom config if it is available
-include Makefile.conf

# Application
APP_ROOT    := $(abspath $(lastword $(MAKEFILE_NAME))/..)
REPORTS_DIR ?=  $(APP_ROOT)/reports

## --- Versioning targets --- ##

.PHONY: version
version:	## display the current version
	@sed -n -e 's/current_version = "\(.*\)"/\1/p' "$(APP_ROOT)/pyproject.toml"

BUMP_TOOL ?= bump-my-version

# Bumpversion 'dry' config
# if 'dry' is specified as target, any bumpversion call using 'BUMP_XARGS' will not apply changes
BUMP_XARGS ?= --verbose --allow-dirty
ifeq ($(filter dry, $(MAKECMDGOALS)), dry)
	BUMP_XARGS := $(BUMP_XARGS) --dry-run
endif

.PHONY: dry
dry:	## run 'bump' target without applying changes (dry-run)
ifeq ($(findstring bump, $(MAKECMDGOALS)),)
	$(error Target 'dry' must be combined with a 'bump' target)
endif

.PHONY: bump
bump:	## bump version using VERSION specified as user input (make VERSION=<X.Y.Z> bump)
	@-echo "Updating package version ..."
	@[ "${VERSION}" ] || ( echo ">> 'VERSION' is not set"; exit 1 )
	@-test -f "$(CONDA_ENV_PATH)/bin/$(BUMP_TOOL)" || pip install $(PIP_XARGS) bump2version
	@-$(BUMP_TOOL) $(BUMP_XARGS) --new-version "${VERSION}" patch;

## --- Installation targets --- ##

.PHONY: install-dep
install-dep:
	@cd "$(APP_ROOT)" && pip install .

.PHONY: install-pkg
install-pkg:
	@cd "$(APP_ROOT)" && pip install --no-depds -e .

.PHONY: install
install: install-dep install-pkg

.PHONY: install-dev
install-dev: install-dep
	@cd "$(APP_ROOT)" && pip install '.[dev]'
	@cd "$(APP_ROOT)" && pip install -e .

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
CHECKS := pep8 lint security security-code security-deps doc8 docf docstring fstring imports
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
	@bash -c '$(CONDA_CMD) \
		ruff check --config "$(APP_ROOT)/pyproject.toml" "$(APP_ROOT)" \
		1> >(tee "$(REPORTS_DIR)/check-pep8.txt")'

.PHONY: check-lint-only
check-lint-only: mkdir-reports		## run linting code style checks
	@echo "Running linting code style checks..."
	@-rm -fr "$(REPORTS_DIR)/check-lint.txt"
	@bash -c '$(CONDA_CMD) \
		ruff check --config "$(APP_ROOT)/pyproject.toml" "$(APP_ROOT)" \
		1> >(tee "$(REPORTS_DIR)/check-lint.txt")'

.PHONY: check-security-only
check-security-only: check-security-code-only check-security-deps-only  ## run security checks

# ignored codes:
#	42194: https://github.com/kvesteri/sqlalchemy-utils/issues/166  # not fixed since 2015
#	51668: https://github.com/sqlalchemy/sqlalchemy/pull/8563  # still in beta + major version change sqlalchemy 2.0.0b1
.PHONY: check-security-deps-only
check-security-deps-only: mkdir-reports  ## run security checks on package dependencies
	@echo "Running security checks of dependencies..."
	@-rm -fr "$(REPORTS_DIR)/check-security-deps.txt"
	@bash -c '$(CONDA_CMD) \
		safety check \
			--policy-file "$(APP_ROOT)/.safety-policy.yml" \
			-r "$(APP_ROOT)/pyproject.toml" \
		1> >(tee "$(REPORTS_DIR)/check-security-deps.txt")'

.PHONY: check-security-code-only
check-security-code-only: mkdir-reports  ## run security checks on source code
	@echo "Running security code checks..."
	@-rm -fr "$(REPORTS_DIR)/check-security-code.txt"
	@bash -c '$(CONDA_CMD) \
		bandit -v -c "$(APP_ROOT)/pyproject.toml" -r "$(APP_ROOT)/aiu" \
		1> >(tee "$(REPORTS_DIR)/check-security-code.txt")'

.PHONY: check-docs-only
check-docs-only: check-doc8-only check-docf-only	## run every code documentation checks

.PHONY: check-doc8-only
check-doc8-only: mkdir-reports		## run PEP8 documentation style checks
	@echo "Running PEP8 doc style checks..."
	@-rm -fr "$(REPORTS_DIR)/check-doc8.txt"
	@[ ! -d "$(APP_ROOT)/docs" ] && echo "No docs to verify!" || \
		bash -c '$(CONDA_CMD) \
			doc8 --config "$(APP_ROOT)/pyproject.toml" "$(APP_ROOT)/docs" \
			1> >(tee "$(REPORTS_DIR)/check-doc8.txt")'

.PHONY: check-docf-only
check-docf-only: mkdir-reports	## run PEP8 code documentation format checks
	@echo "Checking PEP8 doc formatting problems..."
	@-rm -fr "$(REPORTS_DIR)/check-docf.txt"
	@bash -c '$(CONDA_CMD) \
		docformatter --check --diff --recursive --config "$(APP_ROOT)/pyproject.toml" "$(APP_ROOT)" \
		1>&2 2> >(tee "$(REPORTS_DIR)/check-docf.txt")'

.PHONY: check-fstring-only
check-fstring-only: mkdir-reports	## check f-string format definitions
	@echo "Running code f-string formats substitutions..."
	@-rm -f "$(REPORTS_DIR)/check-fstring.txt"
	@bash -c '$(CONDA_CMD) \
		ruff check --select FLY "$(APP_ROOT)" \
		1> >(tee "$(REPORTS_DIR)/check-fstring.txt")'

.PHONY: check-docstring-only
check-docstring-only: mkdir-reports  ## check code docstring style and linting
	@echo "Running docstring checks..."
	@-rm -fr "$(REPORTS_DIR)/check-docstring.txt"
	@bash -c '$(CONDA_CMD) \
		ruff check --select D --config "$(APP_ROOT)/pyproject.toml" "$(APP_ROOT)" \
		1> >(tee "$(REPORTS_DIR)/check-docstring.txt")'

.PHONY: check-imports-only
check-imports-only: mkdir-reports	## run imports code checks
	@echo "Running import checks..."
	@-rm -fr "$(REPORTS_DIR)/check-imports.txt"
	@bash -c '$(CONDA_CMD) \
		ruff check --select I --config "$(APP_ROOT)/pyproject.toml" "$(APP_ROOT)" \
		1> >(tee "$(REPORTS_DIR)/check-imports.txt")'

.PHONY: fixme-list-only
fixme-list-only: mkdir-reports  	## list all FIXME/TODO/HACK items that require attention in the code
	@echo "Listing code that requires fixes..."
	@echo '[MISCELLANEOUS]\nnotes=FIXME,TODO,HACK' > "$(REPORTS_DIR)/fixmerc"
	@bash -c '$(CONDA_CMD) \
		pylint \
			--disable=all,use-symbolic-message-instead --enable=miscellaneous,W0511 \
			--score n --persistent n \
			--rcfile="$(REPORTS_DIR)/fixmerc" \
			-f colorized \
			"$(APP_ROOT)/weaver" "$(APP_ROOT)/tests" \
		1> >(tee "$(REPORTS_DIR)/fixme.txt")'

.PHONY: fixme-list
fixme-list: install-dev fixme-list-only  ## list all FIXME/TODO/HACK items with pre-installation of dependencies

# autogen check variants with pre-install of dependencies using the '-only' target references
FIXES := imports lint docf fstring
FIXES := $(addprefix fix-, $(FIXES))

$(FIXES): fix-%: install-dev fix-%-only

.PHONY: fix
fix: fix-all 	## alias for 'fix-all' target

.PHONY: fix-only
fix-only: $(addsuffix -only, $(FIXES))	## run all automatic fixes without development dependencies pre-install

.PHONY: fix-all
fix-all: install-dev $(FIXES_ALL)  ## fix all code check problems automatically after install of dependencies

.PHONY: fix-imports-only
fix-imports-only: mkdir-reports	## apply import code checks corrections
	@echo "Fixing flagged import checks..."
	@-rm -fr "$(REPORTS_DIR)/fixed-imports.txt"
	@bash -c '$(CONDA_CMD) \
		ruff check --select I --fix --config "$(APP_ROOT)/pyproject.toml" "$(APP_ROOT)" \
		1> >(tee "$(REPORTS_DIR)/fixed-imports.txt")'

.PHONY: fix-lint-only
fix-lint-only: mkdir-reports  ## fix some PEP8 code style problems automatically
	@echo "Fixing PEP8 code style problems..."
	@-rm -fr "$(REPORTS_DIR)/fixed-lint.txt"
	@bash -c '$(CONDA_CMD) \
		ruff check --config "$(APP_ROOT)/pyproject.toml" --fix "$(APP_ROOT)" \
		1> >(tee "$(REPORTS_DIR)/fixed-lint.txt")'

.PHONY: fix-docf-only
fix-docf-only: mkdir-reports  ## fix some PEP8 code documentation style problems automatically
	@echo "Fixing PEP8 code documentation problems..."
	@-rm -fr "$(REPORTS_DIR)/fixed-docf.txt"
	@bash -c '$(CONDA_CMD) \
		docformatter --in-place --diff --recursive --config "$(APP_ROOT)/pyproject.toml" "$(APP_ROOT)" \
		1> >(tee "$(REPORTS_DIR)/fixed-docf.txt")'

.PHONY: fix-fstring-only
fix-fstring-only: mkdir-reports
	@echo "Fixing code string formats substitutions to f-string definitions..."
	@-rm -f "$(REPORTS_DIR)/fixed-fstring.txt"
	@bash -c '$(CONDA_CMD) \
		flynt $(FLYNT_FLAGS) "$(APP_ROOT)" \
		1> >(tee "$(REPORTS_DIR)/fixed-fstring.txt")'


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
