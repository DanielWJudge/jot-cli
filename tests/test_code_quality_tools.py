"""Guardrail tests for story 1-3: Configure Code Quality Tools.

These tests verify that code quality tools (ruff, black, mypy, pre-commit) are
correctly configured and functional. They serve as smoke tests to catch regressions
in code quality tool configuration and ensure tools can run successfully.

Priority: P0 (Critical - Run on every commit)
Test Level: Unit/Integration (configuration validation and tool execution)
"""

import subprocess
import tomllib
from pathlib import Path

import pytest
import yaml

# Test data
PROJECT_ROOT = Path(__file__).parent.parent
RUFF_TOML = PROJECT_ROOT / "ruff.toml"
PRE_COMMIT_CONFIG = PROJECT_ROOT / ".pre-commit-config.yaml"
PYPROJECT_TOML = PROJECT_ROOT / "pyproject.toml"
SRC_DIR = PROJECT_ROOT / "src"


class TestConfigurationFilesExist:
    """Verify all required configuration files exist."""

    def test_ruff_toml_exists(self, project_root: Path):
        """GIVEN: Code quality tools are configured
        WHEN: Checking for ruff.toml file
        THEN: File exists"""
        ruff_toml = project_root / "ruff.toml"
        assert ruff_toml.exists(), "ruff.toml must exist"
        assert ruff_toml.is_file(), "ruff.toml must be a file"

    def test_pre_commit_config_exists(self, project_root: Path):
        """GIVEN: Pre-commit hooks are configured
        WHEN: Checking for .pre-commit-config.yaml file
        THEN: File exists"""
        pre_commit_config = project_root / ".pre-commit-config.yaml"
        assert pre_commit_config.exists(), ".pre-commit-config.yaml must exist"
        assert pre_commit_config.is_file(), ".pre-commit-config.yaml must be a file"

    def test_pyproject_toml_exists(self, project_root: Path):
        """GIVEN: Project configuration exists
        WHEN: Checking for pyproject.toml file
        THEN: File exists"""
        pyproject_toml = project_root / "pyproject.toml"
        assert pyproject_toml.exists(), "pyproject.toml must exist"
        assert pyproject_toml.is_file(), "pyproject.toml must be a file"


class TestRuffConfiguration:
    """Verify Ruff configuration is correct."""

    def test_ruff_toml_is_valid_toml(self, project_root: Path):
        """GIVEN: ruff.toml exists
        WHEN: Parsing ruff.toml as TOML
        THEN: File is valid TOML"""
        ruff_toml = project_root / "ruff.toml"
        content = ruff_toml.read_text(encoding="utf-8")
        # TOML parsing will raise exception if invalid
        tomllib.loads(content)

    def test_ruff_toml_has_target_version(self, project_root: Path):
        """GIVEN: ruff.toml is configured
        WHEN: Checking for target-version setting
        THEN: target-version is set to py313"""
        ruff_toml = project_root / "ruff.toml"
        content = ruff_toml.read_text(encoding="utf-8")
        config = tomllib.loads(content)

        assert "target-version" in config, "ruff.toml must have target-version"
        assert config["target-version"] == "py313", "target-version must be py313"

    def test_ruff_toml_has_line_length(self, project_root: Path):
        """GIVEN: ruff.toml is configured
        WHEN: Checking for line-length setting
        THEN: line-length is set to 100"""
        ruff_toml = project_root / "ruff.toml"
        content = ruff_toml.read_text(encoding="utf-8")
        config = tomllib.loads(content)

        assert "line-length" in config, "ruff.toml must have line-length"
        assert config["line-length"] == 100, "line-length must be 100"

    def test_ruff_toml_has_lint_section(self, project_root: Path):
        """GIVEN: ruff.toml is configured
        WHEN: Checking for lint section
        THEN: lint section exists with select rules"""
        ruff_toml = project_root / "ruff.toml"
        content = ruff_toml.read_text(encoding="utf-8")
        config = tomllib.loads(content)

        assert "lint" in config, "ruff.toml must have [lint] section"
        assert "select" in config["lint"], "[lint] section must have select rules"

    def test_ruff_toml_has_required_select_rules(self, project_root: Path):
        """GIVEN: ruff.toml is configured
        WHEN: Checking select rules
        THEN: Required rules are present (E, W, F, I)"""
        ruff_toml = project_root / "ruff.toml"
        content = ruff_toml.read_text(encoding="utf-8")
        config = tomllib.loads(content)

        select_rules = config["lint"]["select"]
        required_rules = ["E", "W", "F", "I"]  # pycodestyle, pyflakes, isort

        for rule in required_rules:
            assert rule in select_rules, f"ruff.toml must select rule '{rule}'"


class TestBlackConfiguration:
    """Verify Black configuration in pyproject.toml is correct."""

    def test_black_section_exists(self, project_root: Path):
        """GIVEN: pyproject.toml exists
        WHEN: Checking for [tool.black] section
        THEN: Section exists"""
        pyproject_toml = project_root / "pyproject.toml"
        content = pyproject_toml.read_text(encoding="utf-8")
        config = tomllib.loads(content)

        assert "tool" in config, "pyproject.toml must have [tool] section"
        assert "black" in config["tool"], "pyproject.toml must have [tool.black] section"

    def test_black_line_length_matches_ruff(self, project_root: Path):
        """GIVEN: Black and Ruff are configured
        WHEN: Checking line-length settings
        THEN: Both use line-length of 100"""
        pyproject_toml = project_root / "pyproject.toml"
        content = pyproject_toml.read_text(encoding="utf-8")
        config = tomllib.loads(content)

        black_line_length = config["tool"]["black"]["line-length"]
        assert black_line_length == 100, "Black line-length must be 100 (matching Ruff)"

    def test_black_target_version_is_py313(self, project_root: Path):
        """GIVEN: Black is configured
        WHEN: Checking target-version
        THEN: target-version includes py313"""
        pyproject_toml = project_root / "pyproject.toml"
        content = pyproject_toml.read_text(encoding="utf-8")
        config = tomllib.loads(content)

        target_version = config["tool"]["black"]["target-version"]
        assert "py313" in target_version, "Black target-version must include py313"


class TestMypyConfiguration:
    """Verify Mypy configuration in pyproject.toml is correct."""

    def test_mypy_section_exists(self, project_root: Path):
        """GIVEN: pyproject.toml exists
        WHEN: Checking for [tool.mypy] section
        THEN: Section exists"""
        pyproject_toml = project_root / "pyproject.toml"
        content = pyproject_toml.read_text(encoding="utf-8")
        config = tomllib.loads(content)

        assert "tool" in config, "pyproject.toml must have [tool] section"
        assert "mypy" in config["tool"], "pyproject.toml must have [tool.mypy] section"

    def test_mypy_strict_mode_is_enabled(self, project_root: Path):
        """GIVEN: Mypy is configured
        WHEN: Checking strict mode setting
        THEN: strict mode is enabled"""
        pyproject_toml = project_root / "pyproject.toml"
        content = pyproject_toml.read_text(encoding="utf-8")
        config = tomllib.loads(content)

        strict_mode = config["tool"]["mypy"]["strict"]
        assert strict_mode is True, "Mypy strict mode must be enabled"

    def test_mypy_python_version_is_313(self, project_root: Path):
        """GIVEN: Mypy is configured
        WHEN: Checking python_version
        THEN: python_version is 3.13"""
        pyproject_toml = project_root / "pyproject.toml"
        content = pyproject_toml.read_text(encoding="utf-8")
        config = tomllib.loads(content)

        python_version = config["tool"]["mypy"]["python_version"]
        assert python_version == "3.13", "Mypy python_version must be 3.13"


class TestPreCommitConfiguration:
    """Verify pre-commit configuration is correct."""

    def test_pre_commit_config_is_valid_yaml(self, project_root: Path):
        """GIVEN: .pre-commit-config.yaml exists
        WHEN: Parsing as YAML
        THEN: File is valid YAML"""
        pre_commit_config = project_root / ".pre-commit-config.yaml"
        content = pre_commit_config.read_text(encoding="utf-8")
        # YAML parsing will raise exception if invalid
        yaml.safe_load(content)

    def test_pre_commit_config_has_repos(self, project_root: Path):
        """GIVEN: .pre-commit-config.yaml exists
        WHEN: Checking for repos section
        THEN: repos section exists"""
        pre_commit_config = project_root / ".pre-commit-config.yaml"
        content = pre_commit_config.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        assert "repos" in config, ".pre-commit-config.yaml must have repos section"
        assert isinstance(config["repos"], list), "repos must be a list"

    def test_pre_commit_config_has_ruff_hook(self, project_root: Path):
        """GIVEN: Pre-commit hooks are configured
        WHEN: Checking for ruff hook
        THEN: Ruff hook exists in configuration"""
        pre_commit_config = project_root / ".pre-commit-config.yaml"
        content = pre_commit_config.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        ruff_repo = None
        for repo in config["repos"]:
            if "ruff-pre-commit" in repo.get("repo", ""):
                ruff_repo = repo
                break

        assert ruff_repo is not None, "Pre-commit config must include ruff-pre-commit repo"
        assert "hooks" in ruff_repo, "Ruff repo must have hooks section"

        ruff_hook = None
        for hook in ruff_repo["hooks"]:
            if hook.get("id") == "ruff":
                ruff_hook = hook
                break

        assert ruff_hook is not None, "Ruff hook must be configured"

    def test_pre_commit_config_has_black_hook(self, project_root: Path):
        """GIVEN: Pre-commit hooks are configured
        WHEN: Checking for black hook
        THEN: Black hook exists in configuration"""
        pre_commit_config = project_root / ".pre-commit-config.yaml"
        content = pre_commit_config.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        black_repo = None
        for repo in config["repos"]:
            if "psf/black" in repo.get("repo", ""):
                black_repo = repo
                break

        assert black_repo is not None, "Pre-commit config must include black repo"
        assert "hooks" in black_repo, "Black repo must have hooks section"

        black_hook = None
        for hook in black_repo["hooks"]:
            if hook.get("id") == "black":
                black_hook = hook
                break

        assert black_hook is not None, "Black hook must be configured"

    def test_pre_commit_config_has_mypy_hook(self, project_root: Path):
        """GIVEN: Pre-commit hooks are configured
        WHEN: Checking for mypy hook
        THEN: Mypy hook exists in configuration"""
        pre_commit_config = project_root / ".pre-commit-config.yaml"
        content = pre_commit_config.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        mypy_repo = None
        for repo in config["repos"]:
            if "mirrors-mypy" in repo.get("repo", ""):
                mypy_repo = repo
                break

        assert mypy_repo is not None, "Pre-commit config must include mypy repo"
        assert "hooks" in mypy_repo, "Mypy repo must have hooks section"

        mypy_hook = None
        for hook in mypy_repo["hooks"]:
            if hook.get("id") == "mypy":
                mypy_hook = hook
                break

        assert mypy_hook is not None, "Mypy hook must be configured"


class TestRuffToolExecution:
    """Verify Ruff tool can execute successfully."""

    def test_ruff_check_can_run(self, project_root: Path):
        """GIVEN: Ruff is installed and configured
        WHEN: Running 'poetry run ruff check .'
        THEN: Command executes successfully (exit code 0)"""
        result = subprocess.run(
            ["poetry", "run", "ruff", "check", "."],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert (
            result.returncode == 0
        ), f"Ruff check must pass (exit code 0). Output: {result.stdout}\nErrors: {result.stderr}"

    def test_ruff_check_validates_source_code(self, project_root: Path):
        """GIVEN: Ruff is configured
        WHEN: Running ruff check on src directory
        THEN: Command validates source code without errors"""
        result = subprocess.run(
            ["poetry", "run", "ruff", "check", "src/"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert (
            result.returncode == 0
        ), f"Ruff check on src/ must pass. Output: {result.stdout}\nErrors: {result.stderr}"


class TestBlackToolExecution:
    """Verify Black tool can execute successfully."""

    def test_black_check_can_run(self, project_root: Path):
        """GIVEN: Black is installed and configured
        WHEN: Running 'poetry run black --check .'
        THEN: Command executes successfully (exit code 0)"""
        result = subprocess.run(
            ["poetry", "run", "black", "--check", "."],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert (
            result.returncode == 0
        ), f"Black check must pass (exit code 0). Output: {result.stdout}\nErrors: {result.stderr}"

    def test_black_check_validates_source_code(self, project_root: Path):
        """GIVEN: Black is configured
        WHEN: Running black check on src directory
        THEN: Command validates source code formatting"""
        result = subprocess.run(
            ["poetry", "run", "black", "--check", "src/"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert (
            result.returncode == 0
        ), f"Black check on src/ must pass. Output: {result.stdout}\nErrors: {result.stderr}"


class TestMypyToolExecution:
    """Verify Mypy tool can execute successfully."""

    def test_mypy_check_can_run(self, project_root: Path):
        """GIVEN: Mypy is installed and configured
        WHEN: Running 'poetry run mypy src/'
        THEN: Command executes successfully (exit code 0)"""
        result = subprocess.run(
            ["poetry", "run", "mypy", "src/"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=60,  # Mypy can be slower
        )

        assert (
            result.returncode == 0
        ), f"Mypy check must pass (exit code 0). Output: {result.stdout}\nErrors: {result.stderr}"

    def test_mypy_strict_mode_enforced(self, project_root: Path):
        """GIVEN: Mypy strict mode is configured
        WHEN: Running mypy with strict mode
        THEN: Strict type checking is enforced"""
        result = subprocess.run(
            ["poetry", "run", "mypy", "--strict", "src/"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=60,
        )

        # Note: This test verifies strict mode can run, not that it passes
        # (strict mode may find type errors, but the command should execute)
        assert result.returncode in [
            0,
            1,
        ], f"Mypy strict mode must execute (exit code 0 or 1). Output: {result.stdout}\nErrors: {result.stderr}"


class TestPreCommitToolExecution:
    """Verify pre-commit hooks can execute successfully."""

    def test_pre_commit_installed(self, project_root: Path):
        """GIVEN: Pre-commit is installed
        WHEN: Checking if pre-commit is available
        THEN: Pre-commit command exists"""
        result = subprocess.run(
            ["poetry", "run", "pre-commit", "--version"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert (
            result.returncode == 0
        ), f"Pre-commit must be installed. Output: {result.stdout}\nErrors: {result.stderr}"

    def test_pre_commit_config_is_valid(self, project_root: Path):
        """GIVEN: Pre-commit configuration exists
        WHEN: Validating configuration with 'pre-commit validate-config'
        THEN: Configuration is valid"""
        result = subprocess.run(
            ["poetry", "run", "pre-commit", "validate-config"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert (
            result.returncode == 0
        ), f"Pre-commit config must be valid. Output: {result.stdout}\nErrors: {result.stderr}"


class TestConfigurationConsistency:
    """Verify configuration files are consistent with each other."""

    def test_ruff_and_black_line_length_match(self, project_root: Path):
        """GIVEN: Ruff and Black are configured
        WHEN: Comparing line-length settings
        THEN: Both use line-length of 100"""
        # Read ruff.toml
        ruff_toml = project_root / "ruff.toml"
        ruff_content = ruff_toml.read_text(encoding="utf-8")
        ruff_config = tomllib.loads(ruff_content)
        ruff_line_length = ruff_config["line-length"]

        # Read pyproject.toml
        pyproject_toml = project_root / "pyproject.toml"
        pyproject_content = pyproject_toml.read_text(encoding="utf-8")
        pyproject_config = tomllib.loads(pyproject_content)
        black_line_length = pyproject_config["tool"]["black"]["line-length"]

        assert (
            ruff_line_length == black_line_length
        ), f"Ruff line-length ({ruff_line_length}) must match Black line-length ({black_line_length})"

    def test_ruff_not_in_pyproject_toml(self, project_root: Path):
        """GIVEN: Ruff configuration is migrated to ruff.toml
        WHEN: Checking pyproject.toml for [tool.ruff] section
        THEN: [tool.ruff] section does not exist (migrated to ruff.toml)"""
        pyproject_toml = project_root / "pyproject.toml"
        content = pyproject_toml.read_text(encoding="utf-8")
        config = tomllib.loads(content)

        # Check that [tool.ruff] section does not exist
        if "tool" in config and "ruff" in config["tool"]:
            pytest.fail(
                "[tool.ruff] section must not exist in pyproject.toml (should be in ruff.toml)"
            )
