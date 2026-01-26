"""Guardrail tests for story 1-2: Establish Project Directory Structure.

These tests verify that the project directory structure is correctly established
and all architectural boundaries are maintained. They serve as smoke tests to
catch regressions in project organization and dependency rules.

Priority: P0 (Critical - Run on every commit)
Test Level: Unit/Integration (project structure and import validation)
"""

from pathlib import Path

# Test data
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"
JOT_PACKAGE_DIR = SRC_DIR / "jot"
TESTS_DIR = PROJECT_ROOT / "tests"


class TestPackageDirectories:
    """Verify all required package directories exist."""

    def test_commands_directory_exists(self):
        """GIVEN: Project structure is established
        WHEN: Checking for src/jot/commands/ directory
        THEN: Directory exists"""
        commands_dir = JOT_PACKAGE_DIR / "commands"
        assert commands_dir.exists(), "src/jot/commands/ directory must exist"
        assert commands_dir.is_dir(), "src/jot/commands/ must be a directory"

    def test_monitor_directory_exists(self):
        """GIVEN: Project structure is established
        WHEN: Checking for src/jot/monitor/ directory
        THEN: Directory exists"""
        monitor_dir = JOT_PACKAGE_DIR / "monitor"
        assert monitor_dir.exists(), "src/jot/monitor/ directory must exist"
        assert monitor_dir.is_dir(), "src/jot/monitor/ must be a directory"

    def test_core_directory_exists(self):
        """GIVEN: Project structure is established
        WHEN: Checking for src/jot/core/ directory
        THEN: Directory exists"""
        core_dir = JOT_PACKAGE_DIR / "core"
        assert core_dir.exists(), "src/jot/core/ directory must exist"
        assert core_dir.is_dir(), "src/jot/core/ must be a directory"

    def test_db_directory_exists(self):
        """GIVEN: Project structure is established
        WHEN: Checking for src/jot/db/ directory
        THEN: Directory exists"""
        db_dir = JOT_PACKAGE_DIR / "db"
        assert db_dir.exists(), "src/jot/db/ directory must exist"
        assert db_dir.is_dir(), "src/jot/db/ must be a directory"

    def test_ipc_directory_exists(self):
        """GIVEN: Project structure is established
        WHEN: Checking for src/jot/ipc/ directory
        THEN: Directory exists"""
        ipc_dir = JOT_PACKAGE_DIR / "ipc"
        assert ipc_dir.exists(), "src/jot/ipc/ directory must exist"
        assert ipc_dir.is_dir(), "src/jot/ipc/ must be a directory"

    def test_config_directory_exists(self):
        """GIVEN: Project structure is established
        WHEN: Checking for src/jot/config/ directory
        THEN: Directory exists"""
        config_dir = JOT_PACKAGE_DIR / "config"
        assert config_dir.exists(), "src/jot/config/ directory must exist"
        assert config_dir.is_dir(), "src/jot/config/ must be a directory"


class TestPackageInitFiles:
    """Verify all packages have __init__.py files."""

    def test_commands_init_exists(self):
        """GIVEN: commands package exists
        WHEN: Checking for src/jot/commands/__init__.py
        THEN: File exists"""
        init_file = JOT_PACKAGE_DIR / "commands" / "__init__.py"
        assert init_file.exists(), "src/jot/commands/__init__.py must exist"
        assert init_file.is_file(), "src/jot/commands/__init__.py must be a file"

    def test_monitor_init_exists(self):
        """GIVEN: monitor package exists
        WHEN: Checking for src/jot/monitor/__init__.py
        THEN: File exists"""
        init_file = JOT_PACKAGE_DIR / "monitor" / "__init__.py"
        assert init_file.exists(), "src/jot/monitor/__init__.py must exist"
        assert init_file.is_file(), "src/jot/monitor/__init__.py must be a file"

    def test_core_init_exists(self):
        """GIVEN: core package exists
        WHEN: Checking for src/jot/core/__init__.py
        THEN: File exists"""
        init_file = JOT_PACKAGE_DIR / "core" / "__init__.py"
        assert init_file.exists(), "src/jot/core/__init__.py must exist"
        assert init_file.is_file(), "src/jot/core/__init__.py must be a file"

    def test_db_init_exists(self):
        """GIVEN: db package exists
        WHEN: Checking for src/jot/db/__init__.py
        THEN: File exists"""
        init_file = JOT_PACKAGE_DIR / "db" / "__init__.py"
        assert init_file.exists(), "src/jot/db/__init__.py must exist"
        assert init_file.is_file(), "src/jot/db/__init__.py must be a file"

    def test_ipc_init_exists(self):
        """GIVEN: ipc package exists
        WHEN: Checking for src/jot/ipc/__init__.py
        THEN: File exists"""
        init_file = JOT_PACKAGE_DIR / "ipc" / "__init__.py"
        assert init_file.exists(), "src/jot/ipc/__init__.py must exist"
        assert init_file.is_file(), "src/jot/ipc/__init__.py must be a file"

    def test_config_init_exists(self):
        """GIVEN: config package exists
        WHEN: Checking for src/jot/config/__init__.py
        THEN: File exists"""
        init_file = JOT_PACKAGE_DIR / "config" / "__init__.py"
        assert init_file.exists(), "src/jot/config/__init__.py must exist"
        assert init_file.is_file(), "src/jot/config/__init__.py must be a file"


class TestPackageImports:
    """Verify all packages can be imported successfully."""

    def test_commands_package_is_importable(self):
        """GIVEN: commands package structure is correct
        WHEN: Importing jot.commands
        THEN: Import succeeds without errors"""
        import jot.commands  # noqa: F401

        assert jot.commands is not None

    def test_monitor_package_is_importable(self):
        """GIVEN: monitor package structure is correct
        WHEN: Importing jot.monitor
        THEN: Import succeeds without errors"""
        import jot.monitor  # noqa: F401

        assert jot.monitor is not None

    def test_core_package_is_importable(self):
        """GIVEN: core package structure is correct
        WHEN: Importing jot.core
        THEN: Import succeeds without errors"""
        import jot.core  # noqa: F401

        assert jot.core is not None

    def test_db_package_is_importable(self):
        """GIVEN: db package structure is correct
        WHEN: Importing jot.db
        THEN: Import succeeds without errors"""
        import jot.db  # noqa: F401

        assert jot.db is not None

    def test_ipc_package_is_importable(self):
        """GIVEN: ipc package structure is correct
        WHEN: Importing jot.ipc
        THEN: Import succeeds without errors"""
        import jot.ipc  # noqa: F401

        assert jot.ipc is not None

    def test_config_package_is_importable(self):
        """GIVEN: config package structure is correct
        WHEN: Importing jot.config
        THEN: Import succeeds without errors"""
        import jot.config  # noqa: F401

        assert jot.config is not None

    def test_all_packages_import_together(self):
        """GIVEN: All packages exist
        WHEN: Importing all packages in sequence
        THEN: All imports succeed without circular dependency errors"""
        import jot.commands  # noqa: F401
        import jot.config  # noqa: F401
        import jot.core  # noqa: F401
        import jot.db  # noqa: F401
        import jot.ipc  # noqa: F401
        import jot.monitor  # noqa: F401

        # If we get here, no circular import errors occurred
        assert True


class TestDependencyRules:
    """Verify architectural dependency rules are enforced.

    Critical rule: core/ must NOT import from commands/, monitor/, db/, ipc/, or config/
    This ensures core business logic remains pure and testable.
    """

    def test_core_init_has_no_imports_from_commands(self):
        """GIVEN: Dependency rules are enforced
        WHEN: Checking core/__init__.py for imports from commands
        THEN: No imports from commands package"""
        core_init = JOT_PACKAGE_DIR / "core" / "__init__.py"
        content = core_init.read_text(encoding="utf-8")

        # Check for various import patterns that would violate dependency rules
        forbidden_patterns = [
            "from jot.commands",
            "import jot.commands",
            "from ..commands",
            "from ...commands",
        ]

        for pattern in forbidden_patterns:
            assert (
                pattern not in content
            ), f"core/__init__.py must not import from commands/ (found: {pattern})"

    def test_core_init_has_no_imports_from_monitor(self):
        """GIVEN: Dependency rules are enforced
        WHEN: Checking core/__init__.py for imports from monitor
        THEN: No imports from monitor package"""
        core_init = JOT_PACKAGE_DIR / "core" / "__init__.py"
        content = core_init.read_text(encoding="utf-8")

        forbidden_patterns = [
            "from jot.monitor",
            "import jot.monitor",
            "from ..monitor",
            "from ...monitor",
        ]

        for pattern in forbidden_patterns:
            assert (
                pattern not in content
            ), f"core/__init__.py must not import from monitor/ (found: {pattern})"

    def test_core_init_has_no_imports_from_db(self):
        """GIVEN: Dependency rules are enforced
        WHEN: Checking core/__init__.py for imports from db
        THEN: No imports from db package"""
        core_init = JOT_PACKAGE_DIR / "core" / "__init__.py"
        content = core_init.read_text(encoding="utf-8")

        forbidden_patterns = [
            "from jot.db",
            "import jot.db",
            "from ..db",
            "from ...db",
        ]

        for pattern in forbidden_patterns:
            assert (
                pattern not in content
            ), f"core/__init__.py must not import from db/ (found: {pattern})"

    def test_core_init_has_no_imports_from_ipc(self):
        """GIVEN: Dependency rules are enforced
        WHEN: Checking core/__init__.py for imports from ipc
        THEN: No imports from ipc package"""
        core_init = JOT_PACKAGE_DIR / "core" / "__init__.py"
        content = core_init.read_text(encoding="utf-8")

        forbidden_patterns = [
            "from jot.ipc",
            "import jot.ipc",
            "from ..ipc",
            "from ...ipc",
        ]

        for pattern in forbidden_patterns:
            assert (
                pattern not in content
            ), f"core/__init__.py must not import from ipc/ (found: {pattern})"

    def test_core_init_has_no_imports_from_config(self):
        """GIVEN: Dependency rules are enforced
        WHEN: Checking core/__init__.py for imports from config
        THEN: No imports from config package"""
        core_init = JOT_PACKAGE_DIR / "core" / "__init__.py"
        content = core_init.read_text(encoding="utf-8")

        forbidden_patterns = [
            "from jot.config",
            "import jot.config",
            "from ..config",
            "from ...config",
        ]

        for pattern in forbidden_patterns:
            assert (
                pattern not in content
            ), f"core/__init__.py must not import from config/ (found: {pattern})"

    def test_core_package_docstring_documents_dependency_rules(self):
        """GIVEN: Dependency rules are documented
        WHEN: Checking core/__init__.py docstring
        THEN: Docstring mentions dependency restrictions"""
        core_init = JOT_PACKAGE_DIR / "core" / "__init__.py"
        content = core_init.read_text(encoding="utf-8")

        # Check that docstring mentions the dependency rule (case-insensitive)
        content_lower = content.lower()
        assert (
            "must not import" in content_lower
            or "cannot import" in content_lower
            or "does not import" in content_lower
        ), "core/__init__.py docstring should document dependency restrictions"


class TestCLIStillWorks:
    """Verify CLI entry point still works after structure changes."""

    def test_cli_module_still_importable(self):
        """GIVEN: Project structure has been established
        WHEN: Importing jot.cli
        THEN: Import succeeds"""
        from jot.cli import app  # noqa: F401

        assert app is not None

    def test_cli_app_is_typer_instance(self):
        """GIVEN: CLI entry point exists
        WHEN: Checking app type
        THEN: App is a Typer instance"""
        import typer

        from jot.cli import app

        assert isinstance(app, typer.Typer), "app must be a Typer instance"

    def test_cli_has_name(self):
        """GIVEN: CLI is configured
        WHEN: Checking app name
        THEN: App has name attribute"""
        from jot.cli import app

        assert hasattr(app, "info"), "Typer app must have info attribute"
        assert app.info.name == "jot", "CLI app name must be 'jot'"


class TestPackageDocumentation:
    """Verify packages have proper documentation in __init__.py files."""

    def test_commands_init_has_docstring(self):
        """GIVEN: commands package exists
        WHEN: Checking for docstring in __init__.py
        THEN: File has module docstring"""
        commands_init = JOT_PACKAGE_DIR / "commands" / "__init__.py"
        content = commands_init.read_text(encoding="utf-8")

        # Check for docstring (triple quotes at start)
        assert '"""' in content or "'''" in content, "commands/__init__.py should have a docstring"

    def test_monitor_init_has_docstring(self):
        """GIVEN: monitor package exists
        WHEN: Checking for docstring in __init__.py
        THEN: File has module docstring"""
        monitor_init = JOT_PACKAGE_DIR / "monitor" / "__init__.py"
        content = monitor_init.read_text(encoding="utf-8")

        assert '"""' in content or "'''" in content, "monitor/__init__.py should have a docstring"

    def test_core_init_has_docstring(self):
        """GIVEN: core package exists
        WHEN: Checking for docstring in __init__.py
        THEN: File has module docstring"""
        core_init = JOT_PACKAGE_DIR / "core" / "__init__.py"
        content = core_init.read_text(encoding="utf-8")

        assert '"""' in content or "'''" in content, "core/__init__.py should have a docstring"

    def test_db_init_has_docstring(self):
        """GIVEN: db package exists
        WHEN: Checking for docstring in __init__.py
        THEN: File has module docstring"""
        db_init = JOT_PACKAGE_DIR / "db" / "__init__.py"
        content = db_init.read_text(encoding="utf-8")

        assert '"""' in content or "'''" in content, "db/__init__.py should have a docstring"

    def test_ipc_init_has_docstring(self):
        """GIVEN: ipc package exists
        WHEN: Checking for docstring in __init__.py
        THEN: File has module docstring"""
        ipc_init = JOT_PACKAGE_DIR / "ipc" / "__init__.py"
        content = ipc_init.read_text(encoding="utf-8")

        assert '"""' in content or "'''" in content, "ipc/__init__.py should have a docstring"

    def test_config_init_has_docstring(self):
        """GIVEN: config package exists
        WHEN: Checking for docstring in __init__.py
        THEN: File has module docstring"""
        config_init = JOT_PACKAGE_DIR / "config" / "__init__.py"
        content = config_init.read_text(encoding="utf-8")

        assert '"""' in content or "'''" in content, "config/__init__.py should have a docstring"


class TestArchitecturalDocumentation:
    """Verify architectural dependency rules are correctly documented in docstrings.

    These tests validate that each package's __init__.py correctly documents
    what it CAN and CANNOT import, per the architecture specification.
    """

    def test_db_package_documents_no_core_imports(self):
        """GIVEN: Architecture specifies db/ uses only stdlib
        WHEN: Checking db/__init__.py docstring
        THEN: Docstring states db MUST NOT import from core/"""
        db_init = JOT_PACKAGE_DIR / "db" / "__init__.py"
        content = db_init.read_text(encoding="utf-8")

        # db/ should document that it uses ONLY stdlib, no core imports
        assert (
            "MUST use only stdlib" in content or "only stdlib" in content
        ), "db/__init__.py must document stdlib-only constraint"
        assert (
            "MUST NOT import from core" in content or "not import from core" in content.lower()
        ), "db/__init__.py must explicitly forbid core imports"

    def test_config_package_documents_no_jot_imports(self):
        """GIVEN: Architecture specifies config/ uses only stdlib
        WHEN: Checking config/__init__.py docstring
        THEN: Docstring states config MUST NOT import from ANY jot module"""
        config_init = JOT_PACKAGE_DIR / "config" / "__init__.py"
        content = config_init.read_text(encoding="utf-8")

        # config/ is lowest layer - no imports from any other jot module
        assert (
            "MUST use only stdlib" in content or "only stdlib" in content
        ), "config/__init__.py must document stdlib-only constraint"
        assert (
            "MUST NOT import from any other jot" in content
            or "not import from any other jot" in content.lower()
        ), "config/__init__.py must forbid all jot module imports"

    def test_ipc_package_documents_limited_imports(self):
        """GIVEN: Architecture specifies ipc/ can only import core.exceptions, config.paths
        WHEN: Checking ipc/__init__.py docstring
        THEN: Docstring specifies ONLY core.exceptions and config.paths"""
        ipc_init = JOT_PACKAGE_DIR / "ipc" / "__init__.py"
        content = ipc_init.read_text(encoding="utf-8")

        # ipc/ should document it can ONLY import specific modules
        assert (
            "ONLY import from core.exceptions" in content
            or "only import from core.exceptions" in content.lower()
        ), "ipc/__init__.py must specify limited import scope"
        assert (
            "config.paths" in content
        ), "ipc/__init__.py must mention config.paths as allowed import"

    def test_core_package_documents_db_interface_imports(self):
        """GIVEN: Architecture allows core/ to import db/ interfaces only
        WHEN: Checking core/__init__.py docstring
        THEN: Docstring mentions core can import from db/ (interfaces only)"""
        core_init = JOT_PACKAGE_DIR / "core" / "__init__.py"
        content = core_init.read_text(encoding="utf-8")

        # core/ can import db interfaces
        assert (
            "import from db" in content.lower() and "interfaces only" in content.lower()
        ), "core/__init__.py must document allowed db interface imports"

    def test_commands_package_documents_ipc_client(self):
        """GIVEN: Architecture specifies commands/ uses ipc.client
        WHEN: Checking commands/__init__.py docstring
        THEN: Docstring mentions ipc.client specifically"""
        commands_init = JOT_PACKAGE_DIR / "commands" / "__init__.py"
        content = commands_init.read_text(encoding="utf-8")

        # commands/ should specify ipc.client (not just ipc/)
        assert (
            "ipc.client" in content
        ), "commands/__init__.py must specify ipc.client (not generic ipc/)"

    def test_monitor_package_documents_ipc_server(self):
        """GIVEN: Architecture specifies monitor/ uses ipc.server
        WHEN: Checking monitor/__init__.py docstring
        THEN: Docstring mentions ipc.server specifically"""
        monitor_init = JOT_PACKAGE_DIR / "monitor" / "__init__.py"
        content = monitor_init.read_text(encoding="utf-8")

        # monitor/ should specify ipc.server (not just ipc/)
        assert (
            "ipc.server" in content
        ), "monitor/__init__.py must specify ipc.server (not generic ipc/)"
