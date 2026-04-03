# Releasing Steplight

## Before the first public release

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
5. Bump the version in `pyproject.toml` and `steplight/__init__.py`.
6. Create an annotated tag such as `v0.1.0`.
7. Create a GitHub Release from that tag.
8. Publish to PyPI when ready.

## Initial public tag

Steplight's first public release can be cut manually from `main`:

```bash
git tag -a v0.1.0 -m "Steplight v0.1.0"
git push origin main
git push origin v0.1.0
gh release create v0.1.0 --generate-notes --title "Steplight v0.1.0"
```

## Ongoing releases with Release Please

Steplight is configured with `release-please` for ongoing version bumps, changelog updates, tags, and GitHub Releases.

Recommended flow after `v0.1.0`:

1. Merge changes to `main` using Conventional Commit titles such as `feat:` and `fix:`.
2. Let the `release-please` workflow open or update the release PR.
3. Review the generated changelog and version bumps in that PR.
4. Merge the release PR when you want to publish the next version.
5. Publish to PyPI from the tagged release when ready.

If you want CI to run on release PRs created by the workflow, add a `RELEASE_PLEASE_TOKEN` repository secret backed by a fine-scoped GitHub token. Without it, GitHub's default token can still open release PRs and create releases, but those PRs will not trigger other workflows.

## PyPI trusted publishing setup

The repository includes a dedicated PyPI publishing workflow at `.github/workflows/publish.yml`.

To activate tokenless publishing on PyPI:

1. Sign in to PyPI and open the publishing settings.
2. If the `steplight` project does not exist yet, create a pending publisher for a new project.
3. If the project already exists, add a trusted publisher to that project.
4. Use these GitHub Actions settings:

   - Owner: `riccardomerenda`
   - Repository: `steplight`
   - Workflow filename: `publish.yml`
   - Environment name: `pypi`

5. Publish a GitHub Release. The `Publish to PyPI` workflow will build the package, validate it with `twine check`, and upload it through PyPI Trusted Publishing.

Once this is configured on PyPI, no long-lived PyPI API token is needed in GitHub secrets.

If you want to publish an already existing tag such as `v0.1.0`, you can also run the `Publish to PyPI` workflow manually from GitHub Actions and set `ref` to that tag.

## Tagging example

```bash
git tag -a v0.1.0 -m "Steplight v0.1.0"
git push origin v0.1.0
gh release create v0.1.0 --generate-notes
```

## SemVer guidance

- Use `vMAJOR.MINOR.PATCH` tags
- Keep patch releases for fixes and low-risk improvements
- Use minor releases for new adapters, diagnostics, or notable UX additions
- Call out breaking changes clearly while Steplight is still in `0.x`

## Suggested first public release

- Keep the package version at `0.1.0` if you want to signal MVP/alpha status.
- Prefer a short changelog entry summarizing supported formats, diagnostics, and export features.
