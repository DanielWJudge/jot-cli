"""Guardrail tests for story 1-4: Implement XDG Path Resolution.

These tests verify that the XDG path resolution module is correctly implemented
and all architectural boundaries are maintained. They serve as smoke tests to
catch regressions in path handling, platform detection, and stdlib-only requirements.

Priority: P0 (Critical - Run on every commit)
Test Level: Unit/Integration (module structure, imports, and architectural compliance)
"""

import ast
import sys
from pathlib import Path

import pytest

# Test data
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"
JOT_PACKAGE_DIR = SRC_DIR / "jot"
CONFIG_PACKAGE_DIR = JOT_PACKAGE_DIR / "config"
PATHS_MODULE = CONFIG_PACKAGE_DIR / "paths.py"


class TestPathsModuleExists:
    """Verify paths module exists and is correctly structured."""

    def test_paths_module_file_exists(self):
        """GIVEN: Story 1.4 implemented
        WHEN: Checking for src/jot/config/paths.py file
        THEN: File exists"""
        assert PATHS_MODULE.exists(), "src/jot/config/paths.py must exist"
        assert PATHS_MODULE.is_file(), "src/jot/config/paths.py must be a file"

    def test_paths_module_has_docstring(self):
        """GIVEN: paths.py module exists
        WHEN: Checking for module docstring
        THEN: Module has comprehensive docstring"""
        content = PATHS_MODULE.read_text(encoding="utf-8")
        assert '"""' in content or "'''" in content, "paths.py should have a module docstring"
        # Check for XDG mention in docstring
        assert (
            "XDG" in content[:500]
        ), "paths.py docstring should mention XDG Base Directory specification"


class TestRequiredFunctionsExist:
    """Verify all required path resolution functions are implemented."""

    def test_get_config_dir_function_exists(self):
        """GIVEN: paths.py module is implemented
        WHEN: Importing get_config_dir function
        THEN: Function is available"""
        from jot.config.paths import get_config_dir

        assert callable(get_config_dir), "get_config_dir must be a callable function"

    def test_get_data_dir_function_exists(self):
        """GIVEN: paths.py module is implemented
        WHEN: Importing get_data_dir function
        THEN: Function is available"""
        from jot.config.paths import get_data_dir

        assert callable(get_data_dir), "get_data_dir must be a callable function"

    def test_get_runtime_dir_function_exists(self):
        """GIVEN: paths.py module is implemented
        WHEN: Importing get_runtime_dir function
        THEN: Function is available"""
        from jot.config.paths import get_runtime_dir

        assert callable(get_runtime_dir), "get_runtime_dir must be a callable function"


class TestPlatformDetectionHelpers:
    """Verify platform detection helper functions exist."""

    def test_is_windows_helper_exists(self):
        """GIVEN: paths.py module is implemented
        WHEN: Importing _is_windows helper
        THEN: Helper function is available"""
        from jot.config.paths import _is_windows

        assert callable(_is_windows), "_is_windows must be a callable function"

    def test_is_wsl_helper_exists(self):
        """GIVEN: paths.py module is implemented
        WHEN: Importing _is_wsl helper
        THEN: Helper function is available"""
        from jot.config.paths import _is_wsl

        assert callable(_is_wsl), "_is_wsl must be a callable function"


class TestFunctionSignatures:
    """Verify function signatures return correct types."""

    def test_get_config_dir_returns_path(self):
        """GIVEN: get_config_dir is implemented
        WHEN: Calling get_config_dir()
        THEN: Returns a Path object"""
        from jot.config.paths import get_config_dir

        result = get_config_dir()
        assert isinstance(result, Path), "get_config_dir() must return a Path object"

    def test_get_data_dir_returns_path(self):
        """GIVEN: get_data_dir is implemented
        WHEN: Calling get_data_dir()
        THEN: Returns a Path object"""
        from jot.config.paths import get_data_dir

        result = get_data_dir()
        assert isinstance(result, Path), "get_data_dir() must return a Path object"

    def test_get_runtime_dir_returns_path(self):
        """GIVEN: get_runtime_dir is implemented
        WHEN: Calling get_runtime_dir()
        THEN: Returns a Path object"""
        from jot.config.paths import get_runtime_dir

        result = get_runtime_dir()
        assert isinstance(result, Path), "get_runtime_dir() must return a Path object"

    def test_is_windows_returns_bool(self):
        """GIVEN: _is_windows is implemented
        WHEN: Calling _is_windows()
        THEN: Returns a boolean"""
        from jot.config.paths import _is_windows

        result = _is_windows()
        assert isinstance(result, bool), "_is_windows() must return a boolean"

    def test_is_wsl_returns_bool(self):
        """GIVEN: _is_wsl is implemented
        WHEN: Calling _is_wsl()
        THEN: Returns a boolean"""
        from jot.config.paths import _is_wsl

        result = _is_wsl()
        assert isinstance(result, bool), "_is_wsl() must return a boolean"


class TestDirectoriesAreCreated:
    """Verify path functions create directories if they don't exist."""

    def test_get_config_dir_creates_directory(self):
        """GIVEN: get_config_dir is called
        WHEN: Path is returned
        THEN: Directory exists on filesystem"""
        from jot.config.paths import get_config_dir

        config_dir = get_config_dir()
        assert config_dir.exists(), f"get_config_dir() must create directory: {config_dir}"
        assert config_dir.is_dir(), f"get_config_dir() must return a directory: {config_dir}"

    def test_get_data_dir_creates_directory(self):
        """GIVEN: get_data_dir is called
        WHEN: Path is returned
        THEN: Directory exists on filesystem"""
        from jot.config.paths import get_data_dir

        data_dir = get_data_dir()
        assert data_dir.exists(), f"get_data_dir() must create directory: {data_dir}"
        assert data_dir.is_dir(), f"get_data_dir() must return a directory: {data_dir}"

    def test_get_runtime_dir_creates_directory(self):
        """GIVEN: get_runtime_dir is called
        WHEN: Path is returned
        THEN: Directory exists on filesystem"""
        from jot.config.paths import get_runtime_dir

        runtime_dir = get_runtime_dir()
        assert runtime_dir.exists(), f"get_runtime_dir() must create directory: {runtime_dir}"
        assert runtime_dir.is_dir(), f"get_runtime_dir() must return a directory: {runtime_dir}"


class TestPathsAreAbsolute:
    """Verify all returned paths are absolute."""

    def test_get_config_dir_returns_absolute_path(self):
        """GIVEN: get_config_dir is called
        WHEN: Path is returned
        THEN: Path is absolute"""
        from jot.config.paths import get_config_dir

        config_dir = get_config_dir()
        assert config_dir.is_absolute(), f"get_config_dir() must return absolute path: {config_dir}"

    def test_get_data_dir_returns_absolute_path(self):
        """GIVEN: get_data_dir is called
        WHEN: Path is returned
        THEN: Path is absolute"""
        from jot.config.paths import get_data_dir

        data_dir = get_data_dir()
        assert data_dir.is_absolute(), f"get_data_dir() must return absolute path: {data_dir}"

    def test_get_runtime_dir_returns_absolute_path(self):
        """GIVEN: get_runtime_dir is called
        WHEN: Path is returned
        THEN: Path is absolute"""
        from jot.config.paths import get_runtime_dir

        runtime_dir = get_runtime_dir()
        assert (
            runtime_dir.is_absolute()
        ), f"get_runtime_dir() must return absolute path: {runtime_dir}"


class TestPathsContainJot:
    """Verify all paths include 'jot' subdirectory."""

    def test_get_config_dir_contains_jot(self):
        """GIVEN: get_config_dir is called
        WHEN: Path is returned
        THEN: Path ends with 'jot'"""
        from jot.config.paths import get_config_dir

        config_dir = get_config_dir()
        assert config_dir.name == "jot", f"get_config_dir() path must end with 'jot': {config_dir}"

    def test_get_data_dir_contains_jot(self):
        """GIVEN: get_data_dir is called
        WHEN: Path is returned
        THEN: Path ends with 'jot'"""
        from jot.config.paths import get_data_dir

        data_dir = get_data_dir()
        assert data_dir.name == "jot", f"get_data_dir() path must end with 'jot': {data_dir}"

    def test_get_runtime_dir_contains_jot(self):
        """GIVEN: get_runtime_dir is called
        WHEN: Path is returned
        THEN: Path ends with 'jot'"""
        from jot.config.paths import get_runtime_dir

        runtime_dir = get_runtime_dir()
        assert (
            runtime_dir.name == "jot"
        ), f"get_runtime_dir() path must end with 'jot': {runtime_dir}"


@pytest.mark.skipif(sys.platform == "win32", reason="Unix-specific test")
class TestUnixPermissions:
    """Verify directories are created with secure permissions on Unix."""

    def test_config_dir_has_0700_permissions(self):
        """GIVEN: get_config_dir creates directory on Unix
        WHEN: Checking directory permissions
        THEN: Permissions are 0700 (owner-only)"""
        from jot.config.paths import get_config_dir

        config_dir = get_config_dir()
        actual_mode = config_dir.stat().st_mode & 0o777

        assert (
            actual_mode == 0o700
        ), f"Config directory must have 0700 permissions, got {oct(actual_mode)}"

    def test_data_dir_has_0700_permissions(self):
        """GIVEN: get_data_dir creates directory on Unix
        WHEN: Checking directory permissions
        THEN: Permissions are 0700 (owner-only)"""
        from jot.config.paths import get_data_dir

        data_dir = get_data_dir()
        actual_mode = data_dir.stat().st_mode & 0o777

        assert (
            actual_mode == 0o700
        ), f"Data directory must have 0700 permissions, got {oct(actual_mode)}"

    def test_runtime_dir_has_0700_permissions(self):
        """GIVEN: get_runtime_dir creates directory on Unix
        WHEN: Checking directory permissions
        THEN: Permissions are 0700 (owner-only)"""
        from jot.config.paths import get_runtime_dir

        runtime_dir = get_runtime_dir()
        actual_mode = runtime_dir.stat().st_mode & 0o777

        assert (
            actual_mode == 0o700
        ), f"Runtime directory must have 0700 permissions, got {oct(actual_mode)}"


class TestPlatformSpecificPaths:
    """Verify paths follow platform conventions."""

    @pytest.mark.skipif(sys.platform != "linux", reason="Linux-specific test")
    def test_linux_config_path_follows_xdg(self):
        """GIVEN: Running on Linux
        WHEN: Calling get_config_dir()
        THEN: Path follows XDG convention (~/.config/jot)"""
        from jot.config.paths import get_config_dir

        config_dir = get_config_dir()
        assert ".config" in str(
            config_dir
        ), f"Linux config path should contain .config: {config_dir}"

    @pytest.mark.skipif(sys.platform != "linux", reason="Linux-specific test")
    def test_linux_data_path_follows_xdg(self):
        """GIVEN: Running on Linux
        WHEN: Calling get_data_dir()
        THEN: Path follows XDG convention (~/.local/share/jot)"""
        from jot.config.paths import get_data_dir

        data_dir = get_data_dir()
        assert ".local" in str(data_dir), f"Linux data path should contain .local: {data_dir}"
        assert "share" in str(data_dir), f"Linux data path should contain share: {data_dir}"

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific test")
    def test_windows_config_path_uses_appdata(self):
        """GIVEN: Running on Windows
        WHEN: Calling get_config_dir()
        THEN: Path uses APPDATA"""
        from jot.config.paths import get_config_dir

        config_dir = get_config_dir()
        assert (
            "AppData" in str(config_dir) or "appdata" in str(config_dir).lower()
        ), f"Windows config path should use AppData: {config_dir}"

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific test")
    def test_windows_data_path_uses_localappdata(self):
        """GIVEN: Running on Windows
        WHEN: Calling get_data_dir()
        THEN: Path uses LOCALAPPDATA"""
        from jot.config.paths import get_data_dir

        data_dir = get_data_dir()
        assert (
            "AppData" in str(data_dir) or "appdata" in str(data_dir).lower()
        ), f"Windows data path should use AppData: {data_dir}"


class TestArchitecturalBoundaries:
    """Verify architectural boundaries are maintained - CRITICAL TESTS.

    The config/ module is the foundation layer and MUST use only stdlib.
    This is a hard architectural requirement that must never be violated.
    """

    def test_paths_module_imports_only_stdlib(self):
        """GIVEN: config/ is the foundation layer
        WHEN: Analyzing imports in paths.py
        THEN: Module imports only standard library modules"""
        content = PATHS_MODULE.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(PATHS_MODULE))

        # Allowed stdlib modules for this use case
        allowed_stdlib = {"os", "sys", "platform", "pathlib"}

        # Collect all imports
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module.split(".")[0])

        # Check that all imports are from stdlib
        for imp in imports:
            assert imp in allowed_stdlib, f"paths.py must only import stdlib modules, found: {imp}"

    def test_paths_module_has_no_jot_imports(self):
        """GIVEN: config/ cannot import from other jot modules
        WHEN: Checking for jot.* imports in paths.py
        THEN: No imports from jot packages"""
        content = PATHS_MODULE.read_text(encoding="utf-8")

        # Check for various import patterns that would violate architectural rules
        forbidden_patterns = [
            "from jot.",
            "import jot.",
            "from ..commands",
            "from ..monitor",
            "from ..core",
            "from ..db",
            "from ..ipc",
        ]

        for pattern in forbidden_patterns:
            assert (
                pattern not in content
            ), f"paths.py must not import from other jot modules (found: {pattern})"

    def test_config_package_docstring_documents_stdlib_only_rule(self):
        """GIVEN: Architectural rules are documented
        WHEN: Checking config/__init__.py docstring
        THEN: Docstring mentions stdlib-only requirement"""
        config_init = CONFIG_PACKAGE_DIR / "__init__.py"
        content = config_init.read_text(encoding="utf-8")

        # Check that docstring mentions the stdlib-only rule
        assert (
            "MUST use only stdlib" in content or "only stdlib" in content
        ), "config/__init__.py docstring must document stdlib-only requirement"

    def test_paths_module_has_no_external_dependencies(self):
        """GIVEN: paths.py module is implemented
        WHEN: Analyzing all imports
        THEN: No external dependencies (no pip packages)"""
        content = PATHS_MODULE.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(PATHS_MODULE))

        # These are external packages that should NOT be imported
        forbidden_external = {
            "typer",
            "rich",
            "pytest",
            "platformdirs",
            "appdirs",
            "click",
        }

        # Collect all imports
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module.split(".")[0])

        # Check that no forbidden external packages are imported
        for imp in imports:
            assert (
                imp not in forbidden_external
            ), f"paths.py must not import external packages, found: {imp}"


class TestConfigPackageExports:
    """Verify path functions are exported from config package."""

    def test_get_config_dir_exported_from_config(self):
        """GIVEN: paths.py functions are implemented
        WHEN: Importing from jot.config
        THEN: get_config_dir is available"""
        from jot.config import get_config_dir

        assert callable(get_config_dir), "get_config_dir must be exported from jot.config"

    def test_get_data_dir_exported_from_config(self):
        """GIVEN: paths.py functions are implemented
        WHEN: Importing from jot.config
        THEN: get_data_dir is available"""
        from jot.config import get_data_dir

        assert callable(get_data_dir), "get_data_dir must be exported from jot.config"

    def test_get_runtime_dir_exported_from_config(self):
        """GIVEN: paths.py functions are implemented
        WHEN: Importing from jot.config
        THEN: get_runtime_dir is available"""
        from jot.config import get_runtime_dir

        assert callable(get_runtime_dir), "get_runtime_dir must be exported from jot.config"


class TestModuleImportability:
    """Verify module can be imported without errors."""

    def test_paths_module_is_importable(self):
        """GIVEN: paths.py module is implemented
        WHEN: Importing jot.config.paths
        THEN: Import succeeds without errors"""
        import jot.config.paths  # noqa: F401

        assert jot.config.paths is not None

    def test_config_package_is_still_importable(self):
        """GIVEN: paths.py is added to config package
        WHEN: Importing jot.config
        THEN: Import succeeds without circular dependency errors"""
        import jot.config  # noqa: F401

        assert jot.config is not None

    def test_all_path_functions_import_together(self):
        """GIVEN: All path functions are implemented
        WHEN: Importing all functions at once
        THEN: All imports succeed without errors"""
        from jot.config.paths import (
            get_config_dir,
            get_data_dir,
            get_runtime_dir,
        )

        assert callable(get_config_dir)
        assert callable(get_data_dir)
        assert callable(get_runtime_dir)


class TestNoRegressions:
    """Verify existing functionality still works after adding paths module."""

    def test_all_packages_still_importable(self):
        """GIVEN: paths.py module is added
        WHEN: Importing all jot packages
        THEN: No import errors or circular dependencies"""
        import jot.commands  # noqa: F401
        import jot.config  # noqa: F401
        import jot.core  # noqa: F401
        import jot.db  # noqa: F401
        import jot.ipc  # noqa: F401
        import jot.monitor  # noqa: F401

        # If we get here, no circular import errors occurred
        assert True

    def test_cli_still_works(self):
        """GIVEN: paths.py module is added
        WHEN: Importing CLI entry point
        THEN: CLI still works without errors"""
        from jot.cli import app  # noqa: F401

        assert app is not None


class TestFunctionReturnConsistency:
    """Verify functions return consistent results on multiple calls."""

    def test_get_config_dir_is_idempotent(self):
        """GIVEN: get_config_dir is called multiple times
        WHEN: Comparing results
        THEN: Returns same path each time"""
        from jot.config.paths import get_config_dir

        path1 = get_config_dir()
        path2 = get_config_dir()
        path3 = get_config_dir()

        assert path1 == path2 == path3, "get_config_dir() must return consistent path"

    def test_get_data_dir_is_idempotent(self):
        """GIVEN: get_data_dir is called multiple times
        WHEN: Comparing results
        THEN: Returns same path each time"""
        from jot.config.paths import get_data_dir

        path1 = get_data_dir()
        path2 = get_data_dir()
        path3 = get_data_dir()

        assert path1 == path2 == path3, "get_data_dir() must return consistent path"

    def test_get_runtime_dir_is_idempotent(self):
        """GIVEN: get_runtime_dir is called multiple times
        WHEN: Comparing results
        THEN: Returns same path each time"""
        from jot.config.paths import get_runtime_dir

        path1 = get_runtime_dir()
        path2 = get_runtime_dir()
        path3 = get_runtime_dir()

        assert path1 == path2 == path3, "get_runtime_dir() must return consistent path"
