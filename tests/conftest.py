"""Shared pytest fixtures."""

from pathlib import Path

import pytest


@pytest.fixture
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def src_dir(project_root: Path) -> Path:
    """Return the src directory."""
    return project_root / "src"


@pytest.fixture
def jot_package_dir(src_dir: Path) -> Path:
    """Return the jot package directory."""
    return src_dir / "jot"
