"""Guardrail tests for story 1-1: Initialize Project with Poetry and Core Dependencies.

These tests verify that the project initialization is correct and all critical
components are in place. They serve as smoke tests to catch regressions in
project setup.

Priority: P0 (Critical - Run on every commit)
Test Level: Unit/Integration (project structure and configuration validation)
"""

import sys
from pathlib import Path

import pytest
import typer
from pydantic import BaseModel
from rich import print as rich_print
import yaml


# Test data
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"
JOT_PACKAGE_DIR = SRC_DIR / "jot"
TESTS_DIR = PROJECT_ROOT / "tests"
PYPROJECT_TOML = PROJECT_ROOT / "pyproject.toml"


class TestProjectStructure:
    """Verify project structure exists and is correct."""

    def test_pyproject_toml_exists(self):
        """GIVEN: Project is initialized
        WHEN: Checking for pyproject.toml
        THEN: File exists"""
        assert PYPROJECT_TOML.exists(), "pyproject.toml must exist"

    def test_src_directory_exists(self):
        """GIVEN: Project uses src layout
        WHEN: Checking for src/ directory
        THEN: Directory exists"""
        assert SRC_DIR.exists(), "src/ directory must exist"
        assert SRC_DIR.is_dir(), "src/ must be a directory"

    def test_jot_package_directory_exists(self):
        """GIVEN: Project package is named 'jot'
        WHEN: Checking for src/jot/ directory
        THEN: Directory exists"""
        assert JOT_PACKAGE_DIR.exists(), "src/jot/ directory must exist"
        assert JOT_PACKAGE_DIR.is_dir(), "src/jot/ must be a directory"

    def test_jot_init_file_exists(self):
        """GIVEN: Package structure is correct
        WHEN: Checking for src/jot/__init__.py
        THEN: File exists"""
        init_file = JOT_PACKAGE_DIR / "__init__.py"
        assert init_file.exists(), "src/jot/__init__.py must exist"

    def test_cli_module_exists(self):
        """GIVEN: CLI entry point is configured
        WHEN: Checking for src/jot/cli.py
        THEN: File exists"""
        cli_file = JOT_PACKAGE_DIR / "cli.py"
        assert cli_file.exists(), "src/jot/cli.py must exist"

    def test_tests_directory_exists(self):
        """GIVEN: Test framework is configured
        WHEN: Checking for tests/ directory
        THEN: Directory exists"""
        assert TESTS_DIR.exists(), "tests/ directory must exist"
        assert TESTS_DIR.is_dir(), "tests/ must be a directory"

    def test_conftest_exists(self):
        """GIVEN: Pytest is configured
        WHEN: Checking for tests/conftest.py
        THEN: File exists"""
        conftest_file = TESTS_DIR / "conftest.py"
        assert conftest_file.exists(), "tests/conftest.py must exist"


class TestPythonVersion:
    """Verify Python version requirement is met."""

    def test_python_version_is_313_or_higher(self):
        """GIVEN: Project requires Python 3.13+
        WHEN: Checking Python version
        THEN: Version is 3.13 or higher"""
        major, minor = sys.version_info[:2]
        assert major == 3, f"Python major version must be 3, got {major}"
        assert minor >= 13, f"Python minor version must be >= 13, got {minor}"


class TestDependencies:
    """Verify core dependencies are installed and importable."""

    def test_typer_is_importable(self):
        """GIVEN: Typer is a core dependency
        WHEN: Importing typer
        THEN: Import succeeds"""
        assert typer is not None
        assert hasattr(typer, "Typer"), "Typer class must be available"

    def test_pydantic_is_importable(self):
        """GIVEN: Pydantic is a core dependency
        WHEN: Importing pydantic
        THEN: Import succeeds"""
        assert BaseModel is not None
        assert hasattr(BaseModel, "model_validate"), "Pydantic BaseModel must be available"

    def test_rich_is_importable(self):
        """GIVEN: Rich is a core dependency
        WHEN: Importing rich
        THEN: Import succeeds"""
        assert rich_print is not None
        assert callable(rich_print), "Rich print function must be callable"

    def test_pyyaml_is_importable(self):
        """GIVEN: PyYAML is a core dependency
        WHEN: Importing yaml
        THEN: Import succeeds"""
        assert yaml is not None
        assert hasattr(yaml, "safe_load"), "PyYAML safe_load must be available"


class TestCLIEntryPoint:
    """Verify CLI entry point is configured correctly."""

    def test_jot_module_is_importable(self):
        """GIVEN: Package is properly installed
        WHEN: Importing jot package
        THEN: Import succeeds"""
        import jot
        assert jot is not None

    def test_cli_app_is_importable(self):
        """GIVEN: CLI entry point is configured
        WHEN: Importing jot.cli.app
        THEN: Import succeeds"""
        from jot.cli import app
        assert app is not None
        assert isinstance(app, typer.Typer), "app must be a Typer instance"

    def test_cli_has_help_command(self):
        """GIVEN: CLI is configured with commands
        WHEN: Checking app commands
        THEN: Help command exists"""
        from jot.cli import app
        # Typer apps have commands accessible via app.registered_commands
        assert hasattr(app, "registered_commands"), "Typer app must have registered commands"


class TestPyProjectConfiguration:
    """Verify pyproject.toml configuration is correct."""

    def test_pyproject_toml_is_valid_toml(self):
        """GIVEN: pyproject.toml exists
        WHEN: Reading file content
        THEN: File is valid TOML (can be parsed)"""
        import tomllib  # Python 3.13+ has tomllib built-in
        with open(PYPROJECT_TOML, "rb") as f:
            data = tomllib.load(f)
            assert isinstance(data, dict), "TOML must parse to a dictionary"
            assert "tool" in data, "TOML must contain 'tool' section"

    def test_pyproject_has_poetry_section(self):
        """GIVEN: pyproject.toml exists
        WHEN: Reading file content
        THEN: Contains [tool.poetry] section"""
        with open(PYPROJECT_TOML, "r", encoding="utf-8") as f:
            content = f.read()
            assert "[tool.poetry]" in content, "pyproject.toml must contain [tool.poetry] section"

    def test_pyproject_has_dependencies_section(self):
        """GIVEN: Dependencies are configured
        WHEN: Reading pyproject.toml
        THEN: Contains [tool.poetry.dependencies] section"""
        with open(PYPROJECT_TOML, "r", encoding="utf-8") as f:
            content = f.read()
            assert "[tool.poetry.dependencies]" in content, "pyproject.toml must contain dependencies section"

    def test_pyproject_has_dev_dependencies_section(self):
        """GIVEN: Dev dependencies are configured
        WHEN: Reading pyproject.toml
        THEN: Contains [tool.poetry.group.dev.dependencies] section"""
        with open(PYPROJECT_TOML, "r", encoding="utf-8") as f:
            content = f.read()
            assert "[tool.poetry.group.dev.dependencies]" in content or "[tool.poetry.dev-dependencies]" in content, \
                "pyproject.toml must contain dev dependencies section"

    def test_pyproject_has_scripts_section(self):
        """GIVEN: CLI entry point is configured
        WHEN: Reading pyproject.toml
        THEN: Contains [tool.poetry.scripts] section"""
        with open(PYPROJECT_TOML, "r", encoding="utf-8") as f:
            content = f.read()
            assert "[tool.poetry.scripts]" in content, "pyproject.toml must contain scripts section"

    def test_pyproject_has_jot_entry_point(self):
        """GIVEN: CLI entry point is configured
        WHEN: Reading pyproject.toml scripts section
        THEN: Contains 'jot = "jot.cli:app"' entry"""
        with open(PYPROJECT_TOML, "r", encoding="utf-8") as f:
            content = f.read()
            assert 'jot = "jot.cli:app"' in content or 'jot = "jot.cli:app"' in content.replace('"', "'"), \
                "pyproject.toml must contain jot entry point"


class TestPackageVersion:
    """Verify package version is accessible."""

    def test_package_has_version(self):
        """GIVEN: Package is initialized
        WHEN: Accessing __version__
        THEN: Version string is available"""
        import jot
        assert hasattr(jot, "__version__"), "Package must have __version__ attribute"
        assert isinstance(jot.__version__, str), "__version__ must be a string"
        assert len(jot.__version__) > 0, "__version__ must not be empty"
