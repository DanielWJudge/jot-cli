"""Guardrail tests for story 1-6: Set Up CI/CD Pipeline.

These tests verify that GitHub Actions CI/CD workflows are correctly configured
and contain all required components. They serve as smoke tests to catch regressions
in pipeline configuration and ensure workflows remain functional.

Priority: P0 (Critical - Run on every commit)
Test Level: Unit/Integration (configuration validation and workflow structure)
"""

from pathlib import Path

import yaml

# Test data
PROJECT_ROOT = Path(__file__).parent.parent
GITHUB_DIR = PROJECT_ROOT / ".github"
WORKFLOWS_DIR = GITHUB_DIR / "workflows"
CI_WORKFLOW = WORKFLOWS_DIR / "ci.yml"
RELEASE_WORKFLOW = WORKFLOWS_DIR / "release.yml"


class TestWorkflowFilesExist:
    """Verify all required workflow files exist."""

    def test_github_directory_exists(self):
        """GIVEN: CI/CD pipeline is configured
        WHEN: Checking for .github/ directory
        THEN: Directory exists"""
        assert GITHUB_DIR.exists(), ".github/ directory must exist"
        assert GITHUB_DIR.is_dir(), ".github/ must be a directory"

    def test_workflows_directory_exists(self):
        """GIVEN: GitHub Actions workflows are configured
        WHEN: Checking for .github/workflows/ directory
        THEN: Directory exists"""
        assert WORKFLOWS_DIR.exists(), ".github/workflows/ directory must exist"
        assert WORKFLOWS_DIR.is_dir(), ".github/workflows/ must be a directory"

    def test_ci_workflow_exists(self):
        """GIVEN: CI pipeline is configured
        WHEN: Checking for .github/workflows/ci.yml
        THEN: File exists"""
        assert CI_WORKFLOW.exists(), ".github/workflows/ci.yml must exist"
        assert CI_WORKFLOW.is_file(), ".github/workflows/ci.yml must be a file"

    def test_release_workflow_exists(self):
        """GIVEN: Release automation is configured
        WHEN: Checking for .github/workflows/release.yml
        THEN: File exists"""
        assert RELEASE_WORKFLOW.exists(), ".github/workflows/release.yml must exist"
        assert RELEASE_WORKFLOW.is_file(), ".github/workflows/release.yml must be a file"


class TestCIWorkflowConfiguration:
    """Verify CI workflow is correctly configured."""

    def test_ci_workflow_is_valid_yaml(self):
        """GIVEN: ci.yml exists
        WHEN: Parsing ci.yml as YAML
        THEN: File is valid YAML"""
        content = CI_WORKFLOW.read_text(encoding="utf-8")
        # YAML parsing will raise exception if invalid
        yaml.safe_load(content)

    def test_ci_workflow_has_name(self):
        """GIVEN: ci.yml exists
        WHEN: Checking for workflow name
        THEN: Workflow has name 'CI'"""
        content = CI_WORKFLOW.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        assert "name" in config, "ci.yml must have 'name' field"
        assert config["name"] == "CI", "ci.yml name must be 'CI'"

    def test_ci_workflow_has_triggers(self):
        """GIVEN: ci.yml exists
        WHEN: Checking for trigger configuration
        THEN: Workflow has 'on' triggers"""
        content = CI_WORKFLOW.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        # Note: YAML parses 'on' as boolean True, not string 'on'
        assert True in config, "ci.yml must have 'on' trigger configuration"

    def test_ci_workflow_triggers_on_push(self):
        """GIVEN: ci.yml has triggers
        WHEN: Checking push trigger
        THEN: Workflow triggers on push events"""
        content = CI_WORKFLOW.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        # Note: YAML parses 'on' as boolean True, not string 'on'
        assert "push" in config[True], "ci.yml must trigger on push events"

    def test_ci_workflow_triggers_on_pull_request(self):
        """GIVEN: ci.yml has triggers
        WHEN: Checking pull_request trigger
        THEN: Workflow triggers on pull request events"""
        content = CI_WORKFLOW.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        # Note: YAML parses 'on' as boolean True, not string 'on'
        assert "pull_request" in config[True], "ci.yml must trigger on pull_request events"

    def test_ci_workflow_excludes_tag_pushes(self):
        """GIVEN: ci.yml triggers on push
        WHEN: Checking for tag exclusion
        THEN: Workflow excludes version tags (v*)"""
        content = CI_WORKFLOW.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        # Note: YAML parses 'on' as boolean True, not string 'on'
        push_config = config[True]["push"]
        # Check if tags are explicitly ignored
        assert (
            "tags-ignore" in push_config or "tags" not in push_config
        ), "ci.yml must exclude tag pushes (handled by release workflow)"

    def test_ci_workflow_has_jobs(self):
        """GIVEN: ci.yml exists
        WHEN: Checking for jobs configuration
        THEN: Workflow has 'jobs' section"""
        content = CI_WORKFLOW.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        assert "jobs" in config, "ci.yml must have 'jobs' section"
        assert isinstance(config["jobs"], dict), "jobs must be a dictionary"


class TestCILintJob:
    """Verify CI lint job is correctly configured."""

    def test_ci_has_lint_job(self):
        """GIVEN: ci.yml exists
        WHEN: Checking for lint job
        THEN: Workflow has 'lint' job"""
        content = CI_WORKFLOW.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        assert "lint" in config["jobs"], "ci.yml must have 'lint' job"

    def test_lint_job_uses_ubuntu_latest(self):
        """GIVEN: lint job exists
        WHEN: Checking runner configuration
        THEN: Job runs on ubuntu-latest"""
        content = CI_WORKFLOW.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        lint_job = config["jobs"]["lint"]
        assert "runs-on" in lint_job, "lint job must have 'runs-on' configuration"
        assert lint_job["runs-on"] == "ubuntu-latest", "lint job must run on ubuntu-latest"

    def test_lint_job_has_steps(self):
        """GIVEN: lint job exists
        WHEN: Checking for steps
        THEN: Job has steps defined"""
        content = CI_WORKFLOW.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        lint_job = config["jobs"]["lint"]
        assert "steps" in lint_job, "lint job must have 'steps'"
        assert isinstance(lint_job["steps"], list), "steps must be a list"
        assert len(lint_job["steps"]) > 0, "lint job must have at least one step"

    def test_lint_job_checks_out_code(self):
        """GIVEN: lint job has steps
        WHEN: Checking for checkout step
        THEN: Job uses actions/checkout@v4"""
        content = CI_WORKFLOW.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        lint_job = config["jobs"]["lint"]
        checkout_step = None
        for step in lint_job["steps"]:
            if "uses" in step and "checkout" in step["uses"]:
                checkout_step = step
                break

        assert checkout_step is not None, "lint job must checkout code"
        assert (
            "actions/checkout@v4" in checkout_step["uses"]
        ), "lint job must use actions/checkout@v4"

    def test_lint_job_sets_up_python_313(self):
        """GIVEN: lint job has steps
        WHEN: Checking for Python setup step
        THEN: Job sets up Python 3.13"""
        content = CI_WORKFLOW.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        lint_job = config["jobs"]["lint"]
        python_step = None
        for step in lint_job["steps"]:
            if "uses" in step and "setup-python" in step["uses"]:
                python_step = step
                break

        assert python_step is not None, "lint job must set up Python"
        assert (
            "actions/setup-python@v4" in python_step["uses"]
        ), "lint job must use actions/setup-python@v4"
        assert "with" in python_step, "Python setup must have 'with' configuration"
        assert python_step["with"]["python-version"] == "3.13", "lint job must use Python 3.13"

    def test_lint_job_installs_poetry(self):
        """GIVEN: lint job has steps
        WHEN: Checking for Poetry installation
        THEN: Job installs Poetry"""
        content = CI_WORKFLOW.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        lint_job = config["jobs"]["lint"]
        poetry_step = None
        for step in lint_job["steps"]:
            if "uses" in step and "install-poetry" in step["uses"]:
                poetry_step = step
                break

        assert poetry_step is not None, "lint job must install Poetry"
        assert (
            "snok/install-poetry@v1" in poetry_step["uses"]
        ), "lint job must use snok/install-poetry@v1"

    def test_lint_job_runs_ruff(self):
        """GIVEN: lint job has steps
        WHEN: Checking for Ruff check step
        THEN: Job runs 'poetry run ruff check .'"""
        content = CI_WORKFLOW.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        lint_job = config["jobs"]["lint"]
        ruff_step = None
        for step in lint_job["steps"]:
            if "run" in step and "ruff check" in step["run"]:
                ruff_step = step
                break

        assert ruff_step is not None, "lint job must run Ruff check"
        assert (
            "poetry run ruff check" in ruff_step["run"]
        ), "lint job must run 'poetry run ruff check'"

    def test_lint_job_runs_black(self):
        """GIVEN: lint job has steps
        WHEN: Checking for Black check step
        THEN: Job runs 'poetry run black --check .'"""
        content = CI_WORKFLOW.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        lint_job = config["jobs"]["lint"]
        black_step = None
        for step in lint_job["steps"]:
            if "run" in step and "black" in step["run"] and "--check" in step["run"]:
                black_step = step
                break

        assert black_step is not None, "lint job must run Black check"
        assert (
            "poetry run black --check" in black_step["run"]
        ), "lint job must run 'poetry run black --check'"

    def test_lint_job_runs_mypy(self):
        """GIVEN: lint job has steps
        WHEN: Checking for Mypy check step
        THEN: Job runs 'poetry run mypy src/'"""
        content = CI_WORKFLOW.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        lint_job = config["jobs"]["lint"]
        mypy_step = None
        for step in lint_job["steps"]:
            if "run" in step and "mypy" in step["run"]:
                mypy_step = step
                break

        assert mypy_step is not None, "lint job must run Mypy type checking"
        assert "poetry run mypy" in mypy_step["run"], "lint job must run 'poetry run mypy'"


class TestCITestJob:
    """Verify CI test job is correctly configured."""

    def test_ci_has_test_job(self):
        """GIVEN: ci.yml exists
        WHEN: Checking for test job
        THEN: Workflow has 'test' job"""
        content = CI_WORKFLOW.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        assert "test" in config["jobs"], "ci.yml must have 'test' job"

    def test_test_job_uses_ubuntu_latest(self):
        """GIVEN: test job exists
        WHEN: Checking runner configuration
        THEN: Job runs on ubuntu-latest"""
        content = CI_WORKFLOW.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        test_job = config["jobs"]["test"]
        assert "runs-on" in test_job, "test job must have 'runs-on' configuration"
        assert test_job["runs-on"] == "ubuntu-latest", "test job must run on ubuntu-latest"

    def test_test_job_has_steps(self):
        """GIVEN: test job exists
        WHEN: Checking for steps
        THEN: Job has steps defined"""
        content = CI_WORKFLOW.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        test_job = config["jobs"]["test"]
        assert "steps" in test_job, "test job must have 'steps'"
        assert isinstance(test_job["steps"], list), "steps must be a list"
        assert len(test_job["steps"]) > 0, "test job must have at least one step"

    def test_test_job_checks_out_code(self):
        """GIVEN: test job has steps
        WHEN: Checking for checkout step
        THEN: Job uses actions/checkout@v4"""
        content = CI_WORKFLOW.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        test_job = config["jobs"]["test"]
        checkout_step = None
        for step in test_job["steps"]:
            if "uses" in step and "checkout" in step["uses"]:
                checkout_step = step
                break

        assert checkout_step is not None, "test job must checkout code"
        assert (
            "actions/checkout@v4" in checkout_step["uses"]
        ), "test job must use actions/checkout@v4"

    def test_test_job_sets_up_python_313(self):
        """GIVEN: test job has steps
        WHEN: Checking for Python setup step
        THEN: Job sets up Python 3.13"""
        content = CI_WORKFLOW.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        test_job = config["jobs"]["test"]
        python_step = None
        for step in test_job["steps"]:
            if "uses" in step and "setup-python" in step["uses"]:
                python_step = step
                break

        assert python_step is not None, "test job must set up Python"
        assert (
            "actions/setup-python@v4" in python_step["uses"]
        ), "test job must use actions/setup-python@v4"
        assert "with" in python_step, "Python setup must have 'with' configuration"
        assert python_step["with"]["python-version"] == "3.13", "test job must use Python 3.13"

    def test_test_job_installs_poetry(self):
        """GIVEN: test job has steps
        WHEN: Checking for Poetry installation
        THEN: Job installs Poetry"""
        content = CI_WORKFLOW.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        test_job = config["jobs"]["test"]
        poetry_step = None
        for step in test_job["steps"]:
            if "uses" in step and "install-poetry" in step["uses"]:
                poetry_step = step
                break

        assert poetry_step is not None, "test job must install Poetry"
        assert (
            "snok/install-poetry@v1" in poetry_step["uses"]
        ), "test job must use snok/install-poetry@v1"

    def test_test_job_runs_pytest_with_coverage(self):
        """GIVEN: test job has steps
        WHEN: Checking for pytest execution
        THEN: Job runs pytest with coverage reporting"""
        content = CI_WORKFLOW.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        test_job = config["jobs"]["test"]
        pytest_step = None
        for step in test_job["steps"]:
            if "run" in step and "pytest" in step["run"]:
                pytest_step = step
                break

        assert pytest_step is not None, "test job must run pytest"
        assert "poetry run pytest" in pytest_step["run"], "test job must run 'poetry run pytest'"
        assert "--cov" in pytest_step["run"], "test job must run pytest with coverage (--cov)"

    def test_test_job_enforces_80_percent_coverage_threshold(self):
        """GIVEN: test job runs pytest with coverage
        WHEN: Checking for coverage threshold
        THEN: Job enforces minimum 80% coverage"""
        content = CI_WORKFLOW.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        test_job = config["jobs"]["test"]
        pytest_step = None
        for step in test_job["steps"]:
            if "run" in step and "pytest" in step["run"]:
                pytest_step = step
                break

        assert pytest_step is not None, "test job must run pytest"
        assert (
            "--cov-fail-under=80" in pytest_step["run"]
        ), "test job must enforce 80% coverage threshold (--cov-fail-under=80)"

    def test_test_job_generates_coverage_report(self):
        """GIVEN: test job runs pytest with coverage
        WHEN: Checking for coverage report generation
        THEN: Job generates XML coverage report"""
        content = CI_WORKFLOW.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        test_job = config["jobs"]["test"]
        pytest_step = None
        for step in test_job["steps"]:
            if "run" in step and "pytest" in step["run"]:
                pytest_step = step
                break

        assert pytest_step is not None, "test job must run pytest"
        assert (
            "--cov-report=xml" in pytest_step["run"]
        ), "test job must generate XML coverage report (--cov-report=xml)"

    def test_test_job_uploads_coverage_artifact(self):
        """GIVEN: test job generates coverage report
        WHEN: Checking for coverage upload step
        THEN: Job uploads coverage artifact"""
        content = CI_WORKFLOW.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        test_job = config["jobs"]["test"]
        upload_step = None
        for step in test_job["steps"]:
            if "uses" in step and "upload-artifact" in step["uses"]:
                upload_step = step
                break

        assert upload_step is not None, "test job must upload coverage artifact"
        assert (
            "actions/upload-artifact@v4" in upload_step["uses"]
        ), "test job must use actions/upload-artifact@v4"


class TestReleaseWorkflowConfiguration:
    """Verify release workflow is correctly configured."""

    def test_release_workflow_is_valid_yaml(self):
        """GIVEN: release.yml exists
        WHEN: Parsing release.yml as YAML
        THEN: File is valid YAML"""
        content = RELEASE_WORKFLOW.read_text(encoding="utf-8")
        # YAML parsing will raise exception if invalid
        yaml.safe_load(content)

    def test_release_workflow_has_name(self):
        """GIVEN: release.yml exists
        WHEN: Checking for workflow name
        THEN: Workflow has name 'Release'"""
        content = RELEASE_WORKFLOW.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        assert "name" in config, "release.yml must have 'name' field"
        assert config["name"] == "Release", "release.yml name must be 'Release'"

    def test_release_workflow_triggers_on_version_tags(self):
        """GIVEN: release.yml exists
        WHEN: Checking for trigger configuration
        THEN: Workflow triggers on version tags (v*)"""
        content = RELEASE_WORKFLOW.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        # Note: YAML parses 'on' as boolean True, not string 'on'
        assert True in config, "release.yml must have 'on' trigger configuration"
        assert "push" in config[True], "release.yml must trigger on push events"
        assert "tags" in config[True]["push"], "release.yml must trigger on tag pushes"

        tags = config[True]["push"]["tags"]
        assert isinstance(tags, list), "tags must be a list"
        assert "v*" in tags, "release.yml must trigger on version tags (v*)"

    def test_release_workflow_has_permissions(self):
        """GIVEN: release.yml exists
        WHEN: Checking for permissions configuration
        THEN: Workflow has required permissions"""
        content = RELEASE_WORKFLOW.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        assert "permissions" in config, "release.yml must have 'permissions' configuration"
        permissions = config["permissions"]

        assert "contents" in permissions, "release.yml must have 'contents' permission"
        assert (
            permissions["contents"] == "write"
        ), "release.yml must have 'contents: write' permission for GitHub release creation"

    def test_release_workflow_has_jobs(self):
        """GIVEN: release.yml exists
        WHEN: Checking for jobs configuration
        THEN: Workflow has 'jobs' section"""
        content = RELEASE_WORKFLOW.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        assert "jobs" in config, "release.yml must have 'jobs' section"
        assert isinstance(config["jobs"], dict), "jobs must be a dictionary"


class TestReleasePublishJob:
    """Verify release publish job is correctly configured."""

    def test_release_has_publish_job(self):
        """GIVEN: release.yml exists
        WHEN: Checking for publish job
        THEN: Workflow has 'publish' job"""
        content = RELEASE_WORKFLOW.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        assert "publish" in config["jobs"], "release.yml must have 'publish' job"

    def test_publish_job_uses_ubuntu_latest(self):
        """GIVEN: publish job exists
        WHEN: Checking runner configuration
        THEN: Job runs on ubuntu-latest"""
        content = RELEASE_WORKFLOW.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        publish_job = config["jobs"]["publish"]
        assert "runs-on" in publish_job, "publish job must have 'runs-on' configuration"
        assert publish_job["runs-on"] == "ubuntu-latest", "publish job must run on ubuntu-latest"

    def test_publish_job_has_steps(self):
        """GIVEN: publish job exists
        WHEN: Checking for steps
        THEN: Job has steps defined"""
        content = RELEASE_WORKFLOW.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        publish_job = config["jobs"]["publish"]
        assert "steps" in publish_job, "publish job must have 'steps'"
        assert isinstance(publish_job["steps"], list), "steps must be a list"
        assert len(publish_job["steps"]) > 0, "publish job must have at least one step"

    def test_publish_job_checks_out_code(self):
        """GIVEN: publish job has steps
        WHEN: Checking for checkout step
        THEN: Job uses actions/checkout@v4"""
        content = RELEASE_WORKFLOW.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        publish_job = config["jobs"]["publish"]
        checkout_step = None
        for step in publish_job["steps"]:
            if "uses" in step and "checkout" in step["uses"]:
                checkout_step = step
                break

        assert checkout_step is not None, "publish job must checkout code"
        assert (
            "actions/checkout@v4" in checkout_step["uses"]
        ), "publish job must use actions/checkout@v4"

    def test_publish_job_sets_up_python_313(self):
        """GIVEN: publish job has steps
        WHEN: Checking for Python setup step
        THEN: Job sets up Python 3.13"""
        content = RELEASE_WORKFLOW.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        publish_job = config["jobs"]["publish"]
        python_step = None
        for step in publish_job["steps"]:
            if "uses" in step and "setup-python" in step["uses"]:
                python_step = step
                break

        assert python_step is not None, "publish job must set up Python"
        assert (
            "actions/setup-python@v4" in python_step["uses"]
        ), "publish job must use actions/setup-python@v4"
        assert "with" in python_step, "Python setup must have 'with' configuration"
        assert python_step["with"]["python-version"] == "3.13", "publish job must use Python 3.13"

    def test_publish_job_installs_poetry(self):
        """GIVEN: publish job has steps
        WHEN: Checking for Poetry installation
        THEN: Job installs Poetry"""
        content = RELEASE_WORKFLOW.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        publish_job = config["jobs"]["publish"]
        poetry_step = None
        for step in publish_job["steps"]:
            if "uses" in step and "install-poetry" in step["uses"]:
                poetry_step = step
                break

        assert poetry_step is not None, "publish job must install Poetry"
        assert (
            "snok/install-poetry@v1" in poetry_step["uses"]
        ), "publish job must use snok/install-poetry@v1"

    def test_publish_job_builds_package(self):
        """GIVEN: publish job has steps
        WHEN: Checking for build step
        THEN: Job runs 'poetry build'"""
        content = RELEASE_WORKFLOW.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        publish_job = config["jobs"]["publish"]
        build_step = None
        for step in publish_job["steps"]:
            if "run" in step and "poetry build" in step["run"]:
                build_step = step
                break

        assert build_step is not None, "publish job must build package"
        assert "poetry build" in build_step["run"], "publish job must run 'poetry build'"

    def test_publish_job_publishes_to_pypi(self):
        """GIVEN: publish job has steps
        WHEN: Checking for publish step
        THEN: Job runs 'poetry publish' with PyPI token"""
        content = RELEASE_WORKFLOW.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        publish_job = config["jobs"]["publish"]
        publish_step = None
        for step in publish_job["steps"]:
            if "run" in step and "poetry publish" in step["run"]:
                publish_step = step
                break

        assert publish_step is not None, "publish job must publish to PyPI"
        assert "poetry publish" in publish_step["run"], "publish job must run 'poetry publish'"
        assert "env" in publish_step, "publish step must have environment variables"
        assert (
            "POETRY_PYPI_TOKEN_PYPI" in publish_step["env"]
        ), "publish step must use POETRY_PYPI_TOKEN_PYPI environment variable"

    def test_publish_job_uses_pypi_token_secret(self):
        """GIVEN: publish job publishes to PyPI
        WHEN: Checking for PyPI token configuration
        THEN: Job uses GitHub secret for PyPI token"""
        content = RELEASE_WORKFLOW.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        publish_job = config["jobs"]["publish"]
        publish_step = None
        for step in publish_job["steps"]:
            if "run" in step and "poetry publish" in step["run"]:
                publish_step = step
                break

        assert publish_step is not None, "publish job must publish to PyPI"
        pypi_token = publish_step["env"]["POETRY_PYPI_TOKEN_PYPI"]
        assert (
            "secrets.PYPI_API_TOKEN" in pypi_token
        ), "publish step must use secrets.PYPI_API_TOKEN"

    def test_publish_job_creates_github_release(self):
        """GIVEN: publish job has steps
        WHEN: Checking for GitHub release creation
        THEN: Job uses action to create GitHub release"""
        content = RELEASE_WORKFLOW.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        publish_job = config["jobs"]["publish"]
        release_step = None
        for step in publish_job["steps"]:
            if "uses" in step and "gh-release" in step["uses"]:
                release_step = step
                break

        assert release_step is not None, "publish job must create GitHub release"
        assert (
            "softprops/action-gh-release@v1" in release_step["uses"]
        ), "publish job must use softprops/action-gh-release@v1"

    def test_publish_job_uploads_build_artifacts_to_release(self):
        """GIVEN: publish job creates GitHub release
        WHEN: Checking release configuration
        THEN: Job uploads wheel and tarball to release"""
        content = RELEASE_WORKFLOW.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        publish_job = config["jobs"]["publish"]
        release_step = None
        for step in publish_job["steps"]:
            if "uses" in step and "gh-release" in step["uses"]:
                release_step = step
                break

        assert release_step is not None, "publish job must create GitHub release"
        assert "with" in release_step, "release step must have 'with' configuration"
        assert "files" in release_step["with"], "release step must specify files to upload"

        files = release_step["with"]["files"]
        files_str = str(files)  # Convert to string for pattern matching
        assert "dist/*.whl" in files_str, "release must upload wheel files (dist/*.whl)"
        assert "dist/*.tar.gz" in files_str, "release must upload tarball files (dist/*.tar.gz)"


class TestCICDIntegration:
    """Verify CI and release workflows are properly integrated."""

    def test_ci_and_release_use_same_python_version(self):
        """GIVEN: CI and release workflows are configured
        WHEN: Comparing Python versions
        THEN: Both workflows use Python 3.13"""
        ci_content = CI_WORKFLOW.read_text(encoding="utf-8")
        ci_config = yaml.safe_load(ci_content)

        release_content = RELEASE_WORKFLOW.read_text(encoding="utf-8")
        release_config = yaml.safe_load(release_content)

        # Extract Python version from CI lint job
        ci_lint_job = ci_config["jobs"]["lint"]
        ci_python_version = None
        for step in ci_lint_job["steps"]:
            if "uses" in step and "setup-python" in step["uses"]:
                ci_python_version = step["with"]["python-version"]
                break

        # Extract Python version from release publish job
        release_publish_job = release_config["jobs"]["publish"]
        release_python_version = None
        for step in release_publish_job["steps"]:
            if "uses" in step and "setup-python" in step["uses"]:
                release_python_version = step["with"]["python-version"]
                break

        assert ci_python_version is not None, "CI workflow must configure Python version"
        assert release_python_version is not None, "Release workflow must configure Python version"
        assert (
            ci_python_version == release_python_version
        ), f"CI and release workflows must use same Python version (CI: {ci_python_version}, Release: {release_python_version})"
        assert ci_python_version == "3.13", "Both workflows must use Python 3.13"

    def test_ci_and_release_use_same_poetry_action(self):
        """GIVEN: CI and release workflows are configured
        WHEN: Comparing Poetry installation actions
        THEN: Both workflows use snok/install-poetry@v1"""
        ci_content = CI_WORKFLOW.read_text(encoding="utf-8")
        ci_config = yaml.safe_load(ci_content)

        release_content = RELEASE_WORKFLOW.read_text(encoding="utf-8")
        release_config = yaml.safe_load(release_content)

        # Extract Poetry action from CI lint job
        ci_lint_job = ci_config["jobs"]["lint"]
        ci_poetry_action = None
        for step in ci_lint_job["steps"]:
            if "uses" in step and "install-poetry" in step["uses"]:
                ci_poetry_action = step["uses"]
                break

        # Extract Poetry action from release publish job
        release_publish_job = release_config["jobs"]["publish"]
        release_poetry_action = None
        for step in release_publish_job["steps"]:
            if "uses" in step and "install-poetry" in step["uses"]:
                release_poetry_action = step["uses"]
                break

        assert ci_poetry_action is not None, "CI workflow must install Poetry"
        assert release_poetry_action is not None, "Release workflow must install Poetry"
        assert "snok/install-poetry@v1" in ci_poetry_action, "CI must use snok/install-poetry@v1"
        assert (
            "snok/install-poetry@v1" in release_poetry_action
        ), "Release must use snok/install-poetry@v1"

    def test_ci_workflow_does_not_run_on_release_tags(self):
        """GIVEN: CI and release workflows are configured
        WHEN: Checking CI trigger configuration
        THEN: CI workflow excludes version tags to avoid duplication with release workflow"""
        ci_content = CI_WORKFLOW.read_text(encoding="utf-8")
        ci_config = yaml.safe_load(ci_content)

        # Note: YAML parses 'on' as boolean True, not string 'on'
        push_config = ci_config[True]["push"]

        # CI should either explicitly ignore tags or not include them
        has_tag_ignore = "tags-ignore" in push_config
        has_no_tags = "tags" not in push_config

        assert (
            has_tag_ignore or has_no_tags
        ), "CI workflow must exclude version tags (handled by release workflow)"


class TestCICDArchitectureCompliance:
    """Verify CI/CD workflows comply with architecture specifications."""

    def test_ci_workflow_runs_all_quality_checks(self):
        """GIVEN: Architecture specifies lint stage (Ruff, Black, Mypy)
        WHEN: Checking CI workflow
        THEN: All quality checks are configured"""
        content = CI_WORKFLOW.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        lint_job = config["jobs"]["lint"]
        steps_str = str(lint_job["steps"])

        assert "ruff check" in steps_str, "CI must run Ruff check"
        assert "black" in steps_str and "--check" in steps_str, "CI must run Black check"
        assert "mypy" in steps_str, "CI must run Mypy type checking"

    def test_ci_workflow_runs_tests_with_coverage(self):
        """GIVEN: Architecture specifies test stage with coverage
        WHEN: Checking CI workflow
        THEN: Tests run with coverage reporting"""
        content = CI_WORKFLOW.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        test_job = config["jobs"]["test"]
        steps_str = str(test_job["steps"])

        assert "pytest" in steps_str, "CI must run pytest"
        assert "--cov" in steps_str, "CI must run tests with coverage"
        assert "--cov-fail-under=80" in steps_str, "CI must enforce 80% coverage threshold"

    def test_release_workflow_builds_and_publishes_to_pypi(self):
        """GIVEN: Architecture specifies publish stage (PyPI on tag)
        WHEN: Checking release workflow
        THEN: Workflow builds package and publishes to PyPI"""
        content = RELEASE_WORKFLOW.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        publish_job = config["jobs"]["publish"]
        steps_str = str(publish_job["steps"])

        assert "poetry build" in steps_str, "Release must build package"
        assert "poetry publish" in steps_str, "Release must publish to PyPI"

    def test_release_workflow_creates_github_release(self):
        """GIVEN: Architecture specifies GitHub release creation
        WHEN: Checking release workflow
        THEN: Workflow creates GitHub release with artifacts"""
        content = RELEASE_WORKFLOW.read_text(encoding="utf-8")
        config = yaml.safe_load(content)

        publish_job = config["jobs"]["publish"]
        release_step = None
        for step in publish_job["steps"]:
            if "uses" in step and "gh-release" in step["uses"]:
                release_step = step
                break

        assert release_step is not None, "Release workflow must create GitHub release"
        assert "files" in release_step["with"], "Release must upload build artifacts"

    def test_coverage_threshold_matches_nfr38_requirement(self):
        """GIVEN: NFR38 specifies 80% test coverage requirement
        WHEN: Checking CI workflow coverage configuration
        THEN: Coverage threshold is set to 80%"""
        content = CI_WORKFLOW.read_text(encoding="utf-8")
        content_str = content

        assert (
            "--cov-fail-under=80" in content_str
        ), "CI must enforce 80% coverage threshold per NFR38 requirement"
