# Story 1.3: Configure Code Quality Tools

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer**,
I want **automated code quality checks configured**,
So that **code style and type safety are enforced consistently**.

## Acceptance Criteria

**Given** the project structure from Story 1.2
**When** I configure the code quality tools
**Then** `ruff.toml` exists with linting rules (line length, import sorting, PEP 8)
**And** `pyproject.toml` contains Black configuration
**And** `pyproject.toml` contains Mypy strict mode configuration
**And** `.pre-commit-config.yaml` exists with hooks for ruff, black, and mypy
**And** `poetry run ruff check .` passes on the codebase
**And** `poetry run black --check .` passes on the codebase
**And** `poetry run mypy src/` passes on the codebase

**Requirements:** ARCH-21, ARCH-22, ARCH-23, ARCH-24

## Tasks / Subtasks

- [ ] Configure Ruff linting (AC: #1)
  - [ ] Create `ruff.toml` with linting rules
  - [ ] Configure line length, import sorting, PEP 8 rules
  - [ ] Verify `poetry run ruff check .` passes
- [ ] Configure Black formatting (AC: #2)
  - [ ] Add Black configuration to `pyproject.toml`
  - [ ] Verify `poetry run black --check .` passes
- [ ] Configure Mypy type checking (AC: #3)
  - [ ] Add Mypy strict mode configuration to `pyproject.toml`
  - [ ] Verify `poetry run mypy src/` passes
- [ ] Set up pre-commit hooks (AC: #4)
  - [ ] Create `.pre-commit-config.yaml` with hooks for ruff, black, and mypy
  - [ ] Install pre-commit hooks: `poetry run pre-commit install`
  - [ ] Verify hooks run on commit

## Dev Notes

### Architecture Patterns and Constraints

**Code Quality Tool Stack:**
The architecture specifies using Ruff, Black, and Mypy for code quality enforcement:

- **Ruff** (v0.14.14): Fast linter replacing flake8 and isort
  - Handles linting (PEP 8, import sorting, bug detection)
  - 10-100x faster than traditional tools
  - Configured via `ruff.toml` or `pyproject.toml`
  
- **Black** (v26.1.0): Code formatter
  - Enforces consistent code formatting
  - Configured in `pyproject.toml` under `[tool.black]`
  - Line length: 100 characters (matches Ruff)
  
- **Mypy** (v1.19.1): Static type checker
  - Enforces type safety with strict mode
  - Configured in `pyproject.toml` under `[tool.mypy]`
  - Target: Python 3.13+

**Pre-commit Integration:**
- Pre-commit hooks run automatically before git commits
- Ensures code quality checks pass before code enters repository
- Hooks configured in `.pre-commit-config.yaml`
- Must install hooks: `poetry run pre-commit install`

**Configuration File Locations:**
- `ruff.toml` - Standalone Ruff configuration (preferred for complex configs)
- `pyproject.toml` - Black and Mypy configuration (standard Python location)
- `.pre-commit-config.yaml` - Pre-commit hook definitions

### Source Tree Components to Touch

**Files to Create:**
- `ruff.toml` - Ruff linting configuration
- `.pre-commit-config.yaml` - Pre-commit hooks configuration

**Files to Modify:**
- `pyproject.toml` - Add/verify Black and Mypy configuration sections
  - `[tool.black]` section (may already exist, verify completeness)
  - `[tool.mypy]` section (may already exist, verify strict mode)

**Files Already Configured (from Story 1.1):**
- `pyproject.toml` already has basic Ruff configuration in `[tool.ruff]` section
- Dependencies already installed: ruff, black, mypy in dev dependencies
- Need to verify configurations are complete and add missing pieces

### Testing Standards Summary

**Code Quality Verification:**
- Run `poetry run ruff check .` - Should pass with no errors
- Run `poetry run black --check .` - Should pass (no formatting changes needed)
- Run `poetry run mypy src/` - Should pass with strict mode enabled
- Run `poetry run pre-commit run --all-files` - All hooks should pass

**Pre-commit Hook Testing:**
- Make a test commit to verify hooks run automatically
- Verify hooks block commits with linting/formatting errors
- Verify hooks allow commits when all checks pass

**No Functional Tests Required:**
- This story configures tooling, not business logic
- Verification is through tool execution, not unit tests

### Project Structure Notes

**Alignment with Architecture:**
- ✅ Ruff configuration matches architecture specification (ARCH-21)
- ✅ Black configuration matches architecture specification (ARCH-22)
- ✅ Mypy strict mode matches architecture specification (ARCH-23)
- ✅ Pre-commit hooks match architecture specification (ARCH-24)

**Current State Analysis:**
- `pyproject.toml` already has `[tool.ruff]` section with basic configuration
- `pyproject.toml` already has `[tool.black]` section with line-length=100
- `pyproject.toml` already has `[tool.mypy]` section with strict=true
- Need to verify all configurations are complete and add `ruff.toml` if needed
- Need to create `.pre-commit-config.yaml` (does not exist yet)

**Configuration Completeness:**
- Ruff: Currently configured in `pyproject.toml`, may benefit from standalone `ruff.toml`
- Black: Configured in `pyproject.toml`, verify completeness
- Mypy: Configured with strict mode, verify all strict options enabled
- Pre-commit: Not yet configured, needs to be created

### Critical Implementation Details

**Ruff Configuration (`ruff.toml`):**
```toml
target-version = "py313"
line-length = 100
src = ["src", "tests"]

[lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort (import sorting)
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
    "ARG", # flake8-unused-arguments
    "SIM", # flake8-simplify
]
ignore = [
    "E501",  # line too long, handled by black
]

[lint.per-file-ignores]
"__init__.py" = ["F401"]  # unused imports in __init__.py
"tests/**/*.py" = ["ARG", "S101"]  # Allow assert and unused args in tests
```

**Black Configuration (in `pyproject.toml`):**
```toml
[tool.black]
line-length = 100
target-version = ["py313"]
include = '\.pyi?$'
```

**Mypy Configuration (in `pyproject.toml`):**
```toml
[tool.mypy]
python_version = "3.13"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_generics = false
ignore_missing_imports = true
```

**Pre-commit Configuration (`.pre-commit-config.yaml`):**
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=1000']
  
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.14.14
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format
  
  - repo: https://github.com/psf/black
    rev: 26.1.0
    hooks:
      - id: black
        language_version: python3.13
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.19.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: [--strict, --ignore-missing-imports]
```

**Installation Commands:**
```bash
# Install pre-commit (if not already installed)
poetry add --group dev pre-commit

# Install pre-commit hooks
poetry run pre-commit install

# Run all hooks manually
poetry run pre-commit run --all-files

# Verify individual tools
poetry run ruff check .
poetry run black --check .
poetry run mypy src/
```

**Verification Steps:**
1. Create `ruff.toml` with complete configuration
2. Verify `pyproject.toml` has complete Black and Mypy configs
3. Create `.pre-commit-config.yaml` with all hooks
4. Install pre-commit hooks
5. Run all quality checks to verify they pass
6. Make a test commit to verify hooks run automatically

### References

- **Epic 1 Story 1.3:** [_bmad-output/planning-artifacts/epics.md#story-13](epics.md) - Complete story requirements and acceptance criteria
- **Architecture Decision ARCH-21:** [_bmad-output/planning-artifacts/architecture.md#code-quality-tools](architecture.md) - Ruff configuration specification
- **Architecture Decision ARCH-22:** [_bmad-output/planning-artifacts/architecture.md#code-quality-tools](architecture.md) - Black configuration specification
- **Architecture Decision ARCH-23:** [_bmad-output/planning-artifacts/architecture.md#code-quality-tools](architecture.md) - Mypy strict mode specification
- **Architecture Decision ARCH-24:** [_bmad-output/planning-artifacts/architecture.md#code-quality-tools](architecture.md) - Pre-commit hooks specification
- **Previous Story 1.1:** [_bmad-output/implementation-artifacts/1-1-initialize-project-with-poetry-and-core-dependencies.md](1-1-initialize-project-with-poetry-and-core-dependencies.md) - Initial project setup with dependencies
- **Previous Story 1.2:** [_bmad-output/implementation-artifacts/1-2-establish-project-directory-structure.md](1-2-establish-project-directory-structure.md) - Project structure foundation

### Additional Context

**Why Ruff + Black (Not Ruff Only):**
While Ruff can format code, the architecture specifies using both Ruff (linting) and Black (formatting) for:
- **Consistency**: Black is the Python community standard formatter
- **Separation**: Ruff focuses on linting, Black on formatting
- **Compatibility**: Many projects use Black, maintaining compatibility
- **Architecture Decision**: Architecture explicitly specifies both tools (ARCH-21, ARCH-22)

**Why Mypy Strict Mode:**
- Catches type errors at development time, not runtime
- Enforces type annotations throughout codebase
- Prevents common Python type-related bugs
- Required by architecture for maintainability (ARCH-23)

**Why Pre-commit Hooks:**
- Prevents low-quality code from entering repository
- Catches issues before CI/CD pipeline runs
- Saves CI/CD time and resources
- Enforces consistent code quality across team
- Required by architecture for automated enforcement (ARCH-24)

**Configuration File Strategy:**
- **ruff.toml**: Standalone file for Ruff (allows complex configuration, easier to read)
- **pyproject.toml**: Standard location for Black and Mypy (PEP 518 standard)
- **.pre-commit-config.yaml**: Standard pre-commit configuration format

**Tool Execution Order:**
1. Ruff (linting) - Fast, catches errors early
2. Black (formatting) - Ensures consistent style
3. Mypy (type checking) - Validates type safety
4. Pre-commit runs all three automatically

**Integration with CI/CD:**
- These same tools will run in CI/CD pipeline (Story 1.6)
- Pre-commit hooks ensure local and CI checks match
- Consistent tooling prevents "works on my machine" issues

### Previous Story Intelligence

**From Story 1.1 (Initialize Project):**
- ✅ Dependencies already installed: `ruff = "^0.14.14"`, `black = "^26.1.0"`, `mypy = "^1.19.1"` in dev dependencies
- ✅ Basic Ruff configuration exists in `pyproject.toml` under `[tool.ruff]` section
- ✅ Basic Black configuration exists in `pyproject.toml` under `[tool.black]` section  
- ✅ Basic Mypy configuration exists in `pyproject.toml` under `[tool.mypy]` section with `strict = true`
- ✅ Project uses Poetry 2.1+ with PEP 621 support
- ✅ Python 3.13+ requirement is set
- ✅ Project structure uses `--src` layout: `src/jot/` package

**From Story 1.2 (Project Structure):**
- ✅ Package structure established: `commands/`, `monitor/`, `core/`, `db/`, `ipc/`, `config/`
- ✅ Dependency rules documented: core doesn't import from commands/monitor
- ✅ All packages have `__init__.py` files with docstrings
- ✅ Tests directory structure exists: `tests/` with `conftest.py`
- ✅ Import patterns established and validated

**Key Learnings:**
- Configuration files should follow existing patterns in `pyproject.toml`
- All tool configurations should be consistent with Python 3.13 target
- Pre-commit hooks should match CI/CD pipeline (Story 1.6 will use same tools)
- Code quality tools must not break existing tests (62 tests currently pass)

**Files Created/Modified in Previous Stories:**
- `pyproject.toml` - Contains basic tool configurations (needs verification/completion)
- `src/jot/` - Package structure (all packages empty except `__init__.py`)
- `tests/conftest.py` - Shared fixtures (empty, ready for use)
- No existing `ruff.toml` or `.pre-commit-config.yaml` files

### Architecture Compliance Requirements

**ARCH-21: Ruff Configuration**
- Must replace flake8 and isort functionality
- Must enforce PEP 8 compliance
- Must handle import sorting
- Must be configured for Python 3.13 target
- Must use line length of 100 characters (matches Black)

**ARCH-22: Black Configuration**
- Must enforce consistent code formatting
- Must use line length of 100 characters
- Must target Python 3.13
- Must be configured in `pyproject.toml` (standard location)

**ARCH-23: Mypy Strict Mode**
- Must enable strict type checking
- Must enforce type annotations throughout codebase
- Must target Python 3.13
- Must be configured in `pyproject.toml` (standard location)

**ARCH-24: Pre-commit Hooks**
- Must run ruff, black, and mypy automatically before commits
- Must prevent commits with linting/formatting errors
- Must be configured in `.pre-commit-config.yaml`
- Must use same tool versions as dev dependencies

**Enforcement Pattern (from Architecture):**
- Automated enforcement through pre-commit hooks
- Linting errors block CI
- Type errors block CI
- Test failures block merge
- All tools must pass before code enters repository

### Library and Framework Requirements

**Ruff v0.14.14:**
- Fast linter (10-100x faster than flake8/isort)
- Replaces flake8, isort, and other linting tools
- Supports Python 3.13 via `target-version = "py313"`
- Configuration can be in `ruff.toml` (standalone) or `pyproject.toml`
- Must select appropriate rule sets: E, W, F, I, B, C4, UP, ARG, SIM
- Must ignore E501 (line length) since Black handles formatting
- Must allow unused imports in `__init__.py` files (F401)
- Must allow assert statements and unused args in tests (ARG, S101)

**Black v26.1.0:**
- Code formatter (Python community standard)
- Must use line length 100 (matches Ruff)
- Must target Python 3.13
- Configuration in `pyproject.toml` under `[tool.black]`
- Must include pattern `'\.pyi?$'` for Python files

**Mypy v1.19.1:**
- Static type checker with strict mode
- Must enable strict mode: `strict = true`
- Must target Python 3.13: `python_version = "3.13"`
- Must disallow untyped definitions: `disallow_untyped_defs = true`
- Must warn on return any: `warn_return_any = true`
- Must ignore missing imports: `ignore_missing_imports = true` (for third-party libs)
- Configuration in `pyproject.toml` under `[tool.mypy]`

**Pre-commit Framework:**
- Hook management system
- Must install via Poetry: `poetry add --group dev pre-commit`
- Must use official repos for each tool:
  - `astral-sh/ruff-pre-commit` (v0.14.14)
  - `psf/black` (v26.1.0)
  - `pre-commit/mirrors-mypy` (v1.19.1)
- Must include standard hooks: trailing-whitespace, end-of-file-fixer, check-yaml, check-added-large-files

### File Structure Requirements

**Files to Create:**
1. `ruff.toml` (project root)
   - Standalone Ruff configuration file
   - Preferred over `pyproject.toml` for complex Ruff configs
   - Must match existing `pyproject.toml` Ruff config if migrating

2. `.pre-commit-config.yaml` (project root)
   - Pre-commit hooks configuration
   - Must reference correct tool versions
   - Must configure hooks for ruff, black, and mypy

**Files to Modify:**
1. `pyproject.toml` (project root)
   - Verify `[tool.ruff]` section completeness (may migrate to `ruff.toml`)
   - Verify `[tool.black]` section completeness
   - Verify `[tool.mypy]` section completeness and strict mode settings

**Files NOT to Modify:**
- `src/jot/**/*.py` - No code changes needed for this story
- `tests/**/*.py` - No test changes needed
- `pyproject.toml` dependencies - Already correct from Story 1.1

**Configuration File Locations:**
- Project root: `ruff.toml`, `.pre-commit-config.yaml`
- Project root: `pyproject.toml` (Black and Mypy configs)

### Testing Requirements

**No Unit Tests Required:**
- This story configures tooling, not business logic
- Verification is through tool execution, not pytest tests

**Tool Verification Commands:**
```bash
# Verify Ruff linting
poetry run ruff check .

# Verify Black formatting (check mode, no changes)
poetry run black --check .

# Verify Mypy type checking
poetry run mypy src/

# Verify all pre-commit hooks
poetry run pre-commit run --all-files
```

**Pre-commit Hook Testing:**
- Create a test file with intentional linting errors
- Attempt to commit (should be blocked by hooks)
- Fix errors and verify commit succeeds
- Verify hooks run automatically on `git commit`

**Regression Testing:**
- Ensure all existing tests still pass (62 tests from previous stories)
- No breaking changes to existing code structure
- All imports still work correctly

### Latest Technical Information (January 2026)

**Ruff 0.14.14:**
- Latest stable version as of January 2026
- Supports Python 3.13 via `target-version = "py313"`
- Integrates with pre-commit via `ruff-pre-commit` repo
- Can replace Black for formatting, but architecture specifies using both
- Configuration best practices: Use `ruff.toml` for complex configs, `pyproject.toml` for simple configs

**Black 26.1.0:**
- Latest stable version as of January 2026
- Python community standard formatter
- Compatible with Python 3.13
- Configuration in `pyproject.toml` is standard practice

**Mypy 1.19.1:**
- Latest stable version as of January 2026
- Full support for Python 3.13 type system
- Strict mode recommended for new projects
- `ignore_missing_imports = true` needed for third-party libraries without type stubs

**Pre-commit Best Practices (2026):**
- Use official repos for each tool (not custom hooks)
- Pin exact versions in `.pre-commit-config.yaml` (match dev dependencies)
- Run hooks in order: ruff → black → mypy
- Use `--fix` flag for ruff to auto-fix issues
- Use `--exit-non-zero-on-fix` to fail if fixes were applied

**Modern Python Quality Stack (2026):**
- Ruff + Black + Mypy is the recommended stack
- Ruff handles linting (10-100x faster than alternatives)
- Black handles formatting (community standard)
- Mypy handles type checking (strict mode for safety)
- Pre-commit ensures consistency across team

### Project Context Reference

**Current Project State:**
- Python 3.13+ project using Poetry 2.1+
- Source layout: `src/jot/` package structure
- 6 packages: commands/, monitor/, core/, db/, ipc/, config/
- 62 existing tests passing
- Basic tool configurations exist in `pyproject.toml`
- No pre-commit hooks configured yet

**Integration Points:**
- Story 1.6 (CI/CD Pipeline) will use same tools in GitHub Actions
- Future stories will add code that must pass these quality checks
- Pre-commit hooks ensure local and CI checks match

**Dependencies Already Installed:**
- `ruff = "^0.14.14"` in dev dependencies
- `black = "^26.1.0"` in dev dependencies
- `mypy = "^1.19.1"` in dev dependencies
- Need to add: `pre-commit` to dev dependencies

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
