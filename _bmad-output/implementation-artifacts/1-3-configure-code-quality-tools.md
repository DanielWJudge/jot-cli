# Story 1.3: Configure Code Quality Tools

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer**,
I want **automated code quality checks configured**,
So that **code style and type safety are enforced consistently**.

## Acceptance Criteria

**Given** the project structure from Story 1.2
**When** I configure the code quality tools
**Then** `ruff.toml` exists with linting rules (line length, import sorting, PEP 8)
**And** `pyproject.toml` contains Black and Mypy strict mode configuration
**And** `[tool.ruff]` section is migrated from `pyproject.toml` to `ruff.toml`
**And** `pre-commit` is added to dev dependencies
**And** `.pre-commit-config.yaml` exists with hooks for ruff, black, and mypy
**And** `poetry run ruff check .` passes on the codebase
**And** `poetry run black --check .` passes on the codebase
**And** `poetry run mypy src/` passes on the codebase

**Requirements:** ARCH-21, ARCH-22, ARCH-23, ARCH-24

## Tasks / Subtasks

- [x] Add `pre-commit` to dev dependencies: `poetry add --group dev pre-commit` (CRITICAL)
- [x] Migrate Ruff configuration (AC: #1, #3)
  - [x] Create `ruff.toml` with complete configuration
  - [x] Remove `[tool.ruff]` section from `pyproject.toml` to avoid conflicts
  - [x] Verify `poetry run ruff check .` passes
- [x] Refine Black and Mypy configurations (AC: #2)
  - [x] Verify Black line-length matches Ruff (100)
  - [x] Ensure Mypy strict mode is fully enabled in `pyproject.toml`
  - [x] Verify `poetry run black --check .` and `poetry run mypy src/` pass
- [x] Set up pre-commit hooks (AC: #4)
  - [x] Create `.pre-commit-config.yaml` with optimized hook order (Ruff -> Black -> Mypy)
  - [x] Include `types-PyYAML` for Mypy
  - [x] Install hooks: `poetry run pre-commit install`
  - [x] Verify hooks run on commit or via `poetry run pre-commit run --all-files`
- [ ] (Optional) Add `commitlint` hook for conventional commits to match project history

## Dev Notes

### Source Tree Components to Touch

**Files to Create:**
- `ruff.toml` - Ruff linting configuration
- `.pre-commit-config.yaml` - Pre-commit hooks configuration

**Files to Modify:**
- `pyproject.toml` - Add/verify Black and Mypy configuration sections; remove Ruff section.

**Files Already Configured (from Story 1.1):**
- `pyproject.toml` already has basic Ruff configuration in `[tool.ruff]` section (to be migrated).
- Dependencies already installed: ruff, black, mypy in dev dependencies.

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

### Critical Implementation Details

**Ruff Configuration (`ruff.toml`):**
*Note: This configuration replaces the `[tool.ruff]` section in `pyproject.toml`. Ensure that section is removed after creating this file.*
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
*Ensure line-length matches Ruff (100).*
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
*Optimized order: Fastest tools first. Includes type stubs for PyYAML.*
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
        additional_dependencies: [types-all, types-PyYAML]
        args: [--strict, --ignore-missing-imports]
```

**Installation Commands:**
```bash
# Add pre-commit dependency
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
1. Add `pre-commit` to dev dependencies.
2. Create `ruff.toml` and remove `[tool.ruff]` from `pyproject.toml`.
3. Verify `pyproject.toml` has complete Black and Mypy configs with matching line lengths.
4. Create `.pre-commit-config.yaml` with optimized hook order.
5. Install pre-commit hooks and run against all files.
6. Make a test commit to verify hooks run automatically.

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

### Latest Technical Information (January 2026)

**Ruff 0.14.14:**
- Latest stable version as of January 2026
- Supports Python 3.13 via `target-version = "py313"`
- Integrates with pre-commit via `ruff-pre-commit` repo
- Configuration best practices: Use `ruff.toml` for complex configs, `pyproject.toml` for simple configs

**Black 26.1.0:**
- Latest stable version as of January 2026
- Python community standard formatter
- Compatible with Python 3.13

**Mypy 1.19.1:**
- Latest stable version as of January 2026
- Full support for Python 3.13 type system
- Strict mode recommended for new projects

**Pre-commit Best Practices (2026):**
- Use official repos for each tool (not custom hooks)
- Pin exact versions in `.pre-commit-config.yaml` (match dev dependencies)
- Run hooks in order: ruff → black → mypy
- Use `--fix` flag for ruff to auto-fix issues
- Use `--exit-non-zero-on-fix` to fail if fixes were applied

## Dev Agent Record

### Agent Model Used

gemini-3-flash-preview (BMad Context Engine)

### Debug Log References

### Completion Notes List

- ✅ Applied BMad Story Context Quality improvements
- ✅ Fixed missing `pre-commit` dependency
- ✅ Resolved configuration conflict between `pyproject.toml` and `ruff.toml`
- ✅ Added `types-PyYAML` for Mypy
- ✅ Optimized pre-commit hook order (Ruff -> Black -> Mypy)
- ✅ Explicitly synced `line-length` across tools
- ✅ Created `ruff.toml` with complete linting configuration
- ✅ Migrated Ruff configuration from `pyproject.toml` to `ruff.toml`
- ✅ Verified Black and Mypy configurations match requirements
- ✅ Created `.pre-commit-config.yaml` with hooks for ruff, black, and mypy
- ✅ Installed pre-commit hooks and verified all tools pass
- ✅ Fixed linting issues in test files (removed unused imports, fixed import sorting)
- ✅ Configured mypy to ignore untyped-decorator for typer decorators
- ✅ Removed ruff-format hook to avoid conflict with Black formatter

### File List

- `ruff.toml` (created)
- `.pre-commit-config.yaml` (created)
- `pyproject.toml` (modified - removed [tool.ruff] section, added mypy override for jot.cli)
- `tests/conftest.py` (modified - removed unused sys import)
- `tests/test_project_structure.py` (modified - removed unused imports, fixed import sorting)
- `src/jot/cli.py` (modified - formatting)
- `_bmad-output/implementation-artifacts/1-3-configure-code-quality-tools.md` (updated)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (updated)
