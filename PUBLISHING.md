# Publishing to PyPI

Operating procedures for building and publishing updates to the `koko-finance` Python SDK.

## Prerequisites

```bash
pip install build twine
```

PyPI API token stored at https://pypi.org/manage/account/token/ (scoped to `koko-finance` project).

## Publishing a New Version

### 1. Update the version number

Bump the version in **both** files:

- `pyproject.toml` → `version = "X.Y.Z"`
- `koko_finance/__init__.py` → `__version__ = "X.Y.Z"`

Follow [semver](https://semver.org/):
- **Patch** (0.1.0 → 0.1.1): Bug fixes, no API changes
- **Minor** (0.1.0 → 0.2.0): New methods, new parameters, backward-compatible changes
- **Major** (0.1.0 → 1.0.0): Breaking changes (renamed methods, removed parameters, changed return types)

### 2. Run tests

```bash
python -m pytest tests/ -v
```

All tests must pass before publishing.

### 3. Clean old build artifacts

```bash
rm -rf dist/ build/ *.egg-info
```

### 4. Build the package

```bash
python -m build
```

This creates two files in `dist/`:
- `koko_finance-X.Y.Z.tar.gz` (source distribution)
- `koko_finance-X.Y.Z-py3-none-any.whl` (wheel)

### 5. Upload to PyPI

```bash
twine upload dist/*
```

Paste your PyPI API token when prompted (starts with `pypi-`).

### 6. Verify the publish

```bash
pip install --upgrade koko-finance
python -c "import koko_finance; print(koko_finance.__version__)"
```

### 7. Commit and push

```bash
git add pyproject.toml koko_finance/__init__.py
git commit -m "chore: bump version to X.Y.Z"
git push
```

Optionally tag the release:

```bash
git tag vX.Y.Z
git push --tags
```

## Common Scenarios

### Adding a new client method

1. Add the method to `koko_finance/client.py`
2. Add tests to `tests/test_client.py`
3. Update `README.md` with usage example
4. Bump minor version (e.g., 0.1.0 → 0.2.0)
5. Publish

### Fixing a bug

1. Fix in `koko_finance/client.py` or `exceptions.py`
2. Add a regression test
3. Bump patch version (e.g., 0.1.0 → 0.1.1)
4. Publish

### Updating for a new API endpoint

1. Add the method to `client.py`
2. Update `README.md`
3. Bump minor version
4. Publish

## Important Notes

- **PyPI versions are immutable.** Once you upload `0.1.0`, you cannot overwrite it. You must bump to `0.1.1` even for typo fixes.
- **Always run tests before publishing.** There is no undo.
- **Keep `pyproject.toml` and `__init__.py` versions in sync.** PyPI uses the `pyproject.toml` version; the `__init__` version is for runtime `koko_finance.__version__`.
- **The `dist/` directory is gitignored.** Build artifacts are not committed.
