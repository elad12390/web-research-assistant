# Release Checklist

This guide walks you through releasing a new version to PyPI.

## Prerequisites

1. **Set up PyPI Trusted Publishing** (one-time setup)
   - Go to https://pypi.org/manage/account/publishing/
   - Add GitHub publisher for `elad12390/web-research-assistant`
   - Workflow: `.github/workflows/publish.yml`
   - Environment: leave blank (or create `release` environment)

2. **Ensure you have permissions**
   - You need write access to the repository
   - GitHub Actions must be enabled

## Release Process

### 1. Update Version

Edit `pyproject.toml` and bump the version:
```toml
version = "0.2.0"  # or whatever the new version is
```

### 2. Update CHANGELOG.md

Move items from `[Unreleased]` to a new version section:

```markdown
## [0.2.0] - 2025-01-XX

### Added
- New feature X
- New tool Y

### Fixed
- Bug Z

## [0.1.0] - 2025-01-16
...
```

Update the comparison links at the bottom:
```markdown
[Unreleased]: https://github.com/elad12390/web-research-assistant/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/elad12390/web-research-assistant/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/elad12390/web-research-assistant/releases/tag/v0.1.0
```

### 3. Commit and Push

```bash
git add pyproject.toml CHANGELOG.md
git commit -m "chore: bump version to 0.2.0"
git push origin main
```

### 4. Create a Git Tag

```bash
git tag -a v0.2.0 -m "Release v0.2.0"
git push origin v0.2.0
```

### 5. Create GitHub Release

Using GitHub CLI:
```bash
gh release create v0.2.0 \
  --title "v0.2.0" \
  --notes-file CHANGELOG.md \
  --latest
```

Or manually:
1. Go to https://github.com/elad12390/web-research-assistant/releases/new
2. Choose tag: `v0.2.0`
3. Release title: `v0.2.0`
4. Copy relevant section from CHANGELOG.md into description
5. Check "Set as the latest release"
6. Click "Publish release"

### 6. Automated Publishing

The GitHub Action will automatically:
1. Detect the new release
2. Build the package with `uv build`
3. Publish to PyPI using trusted publishing

Monitor the action at: https://github.com/elad12390/web-research-assistant/actions

### 7. Verify Release

After a few minutes, verify the package is available:

```bash
# Check PyPI
pip install web-research-assistant==0.2.0

# Or browse
# https://pypi.org/project/web-research-assistant/
```

## Troubleshooting

### Action failed: "Invalid or missing PyPI token"

You need to set up Trusted Publishing on PyPI first (see Prerequisites).

### Action failed: "Version already exists"

You can't overwrite existing versions on PyPI. Bump to a new version.

### Tag already exists

Delete the tag and recreate:
```bash
git tag -d v0.2.0
git push origin :refs/tags/v0.2.0
git tag -a v0.2.0 -m "Release v0.2.0"
git push origin v0.2.0
```

## Pre-release Testing

Before releasing, run full tests locally:

```bash
# Install dev dependencies
uv sync --all-extras

# Run tests
uv run pytest tests/ -v

# Check linting
uv run ruff check src/
uv run ruff format --check src/

# Type checking
uv run mypy src/ --ignore-missing-imports

# Build locally
uv build
```

## Versioning

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (1.0.0): Breaking changes
- **MINOR** (0.1.0): New features, backwards compatible
- **PATCH** (0.0.1): Bug fixes, backwards compatible
