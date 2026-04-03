# Releasing Steplight

## Before you release

```bash
python -m pip install -e .[dev]
pytest
python -m build
```

## Release checklist

1. Confirm `README.md`, `CHANGELOG.md`, `LICENSE`, and `pyproject.toml` are up to date.
2. Review sample traces and screenshots or reports used in documentation.
3. Build a fresh wheel and source distribution with `python -m build`.
4. Smoke-test the CLI from the built package in a clean environment.
5. Tag the release in GitHub.
6. Publish to PyPI when ready.

## Suggested first public release

- Keep the package version at `0.1.0` if you want to signal MVP/alpha status.
- Prefer a short changelog entry summarizing supported formats, diagnostics, and export features.
