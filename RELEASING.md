# Releasing Steplight

## Before the first public release

```bash
python -m pip install -e .[dev]
pytest
python -m build
```

## Automated release flow

Releases are fully automated via GitHub Actions. No manual version bumps, tags, or PyPI uploads required.

1. Push to `main` using conventional commit messages (`feat:`, `fix:`, `chore:`, etc.).
2. CI runs tests on Python 3.11, 3.12, and 3.13.
3. Release Please creates or updates a release PR with version bump and changelog.
4. The release PR auto-merges once CI passes.
5. A GitHub Release is created from the merged PR.
6. The publish workflow builds the package and uploads it to PyPI via trusted publishing.

## Initial public tag

Steplight's first public release can be cut manually from `main`:

```bash
git tag -a v0.1.0 -m "Steplight v0.1.0"
git push origin main
git push origin v0.1.0
gh release create v0.1.0 --generate-notes --title "Steplight v0.1.0"
```

## Ongoing releases with Release Please

Steplight is configured with `release-please` for ongoing version bumps, changelog updates, tags, and GitHub Releases. Release PRs are auto-merged after CI passes.

1. Merge changes to `main` using Conventional Commit titles such as `feat:` and `fix:`.
2. The `release-please` workflow opens or updates the release PR automatically.
3. The release PR auto-merges once CI passes, creating a GitHub Release.
4. The publish workflow uploads the package to PyPI.

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

## Manual override

If you need to publish a specific ref manually, trigger the `Publish to PyPI` workflow from the Actions tab with the desired git ref (e.g., `v0.2.0` or `main`).
