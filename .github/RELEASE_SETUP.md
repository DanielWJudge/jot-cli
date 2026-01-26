# Release Setup Guide

This document explains how to set up the automated release workflow for publishing to PyPI.

## Prerequisites

1. **PyPI Account**: Create an account at [pypi.org](https://pypi.org/account/register/)
2. **Verified Email**: Verify your PyPI email address
3. **Project Name**: Ensure `jot-cli` is available on PyPI (or update name in `pyproject.toml`)

## PyPI API Token Setup

### Step 1: Generate PyPI API Token

1. Log into your PyPI account at [pypi.org](https://pypi.org/)
2. Go to Account Settings → API tokens
3. Click "Add API token"
4. Configure the token:
   - **Token name**: `jot-cli-github-actions`
   - **Scope**:
     - First release: Choose "Entire account" (can be scoped after first publish)
     - After first release: Choose "Project: jot-cli"
5. Click "Add token"
6. **IMPORTANT**: Copy the token immediately (starts with `pypi-`)
   - This is your only chance to see it!
   - Save it temporarily in a secure location

### Step 2: Add Token to GitHub Secrets

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click "New repository secret"
4. Add the secret:
   - **Name**: `PYPI_API_TOKEN`
   - **Value**: Paste the PyPI token (starting with `pypi-`)
5. Click "Add secret"

### Step 3: Verify Configuration

The release workflow is already configured to use this token:

```yaml
- name: Publish to PyPI
  env:
    POETRY_PYPI_TOKEN_PYPI: ${{ secrets.PYPI_API_TOKEN }}
  run: poetry publish
```

## Branch Protection (Optional but Recommended)

1. Go to **Settings** → **Branches**
2. Add rule for `main` branch:
   - ✅ Require status checks to pass before merging
   - ✅ Require `lint` and `test` to pass
   - ✅ Require branches to be up to date before merging
   - ✅ Require pull request before merging (optional)

## Creating a Release

### Automatic Method (Recommended)

```bash
# Update version (patch/minor/major)
poetry version patch

# Commit the version bump
git add pyproject.toml
git commit -m "chore: bump version to $(poetry version -s)"

# Create and push tag
git tag "v$(poetry version -s)"
git push origin main --tags
```

The release workflow will automatically:
1. Build the package with Poetry
2. Publish to PyPI
3. Create a GitHub release with changelog
4. Upload build artifacts (.whl and .tar.gz)

### Manual Testing (First Time Only)

Before your first real release, test with a pre-release tag:

```bash
# Create a test tag
git tag v0.0.1-test
git push origin v0.0.1-test

# Watch the release workflow run
# Delete the test release from GitHub and PyPI if needed
```

## Verifying the Release

After the release workflow completes:

1. **Check PyPI**: Visit [pypi.org/project/jot-cli/](https://pypi.org/project/jot-cli/)
2. **Check GitHub Releases**: Visit your repository's releases page
3. **Test Installation**:
   ```bash
   pipx install jot-cli
   jot --help
   ```

## Troubleshooting

### "Project name already exists"

If someone already registered `jot-cli` on PyPI:
1. Choose a different name (e.g., `jot-task-cli`)
2. Update `name` in `pyproject.toml`
3. Update README and documentation

### "Invalid API token"

1. Regenerate the token in PyPI
2. Update the `PYPI_API_TOKEN` secret in GitHub
3. Ensure the token has upload permissions

### "Version already exists"

You're trying to publish a version that already exists on PyPI:
1. Bump the version: `poetry version patch`
2. Commit and create a new tag

### Release workflow fails

1. Check the GitHub Actions logs for detailed errors
2. Verify the `PYPI_API_TOKEN` secret is set correctly
3. Ensure `pyproject.toml` has all required metadata
4. Check that Poetry can build locally: `poetry build`

## CI/CD Architecture

```
Push to main → CI runs (lint + test)
                 ↓
            All checks pass
                 ↓
         Ready to merge PR
                 ↓
        Create version tag (v*)
                 ↓
        Release workflow triggers
                 ↓
         Poetry build → PyPI publish
                 ↓
         GitHub Release created
                 ↓
         Artifacts uploaded
```

## Security Best Practices

1. **Never commit tokens**: Tokens are stored in GitHub Secrets only
2. **Use scoped tokens**: After first release, scope token to project
3. **Rotate tokens**: Periodically regenerate tokens
4. **Review permissions**: Ensure workflow has minimal required permissions
5. **Enable 2FA**: Use two-factor authentication on PyPI and GitHub

## References

- [Poetry Publishing Documentation](https://python-poetry.org/docs/libraries/#publishing-to-pypi)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [PyPI API Tokens](https://pypi.org/help/#apitoken)
