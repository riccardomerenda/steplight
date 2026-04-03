# Versioning and Releases

Steplight uses semantic versioning, annotated Git tags, and GitHub Releases.

## Recommended Tag Format

Use annotated Git tags in the form:

```text
v0.1.0
v0.1.1
v0.2.0
```

For a public GitHub repository, this is worth doing even in alpha:

- tags give users stable install and reference points
- GitHub Releases are built on top of tags
- changelog entries become easier to map to real published versions
- PyPI publishing becomes much cleaner

## Suggested SemVer Policy

While Steplight is still in the `0.x` phase:

- patch: bug fixes, parser fixes, workflow fixes, non-breaking diagnostics
- minor: new adapters, new diagnostics, new commands, notable UI/report improvements
- breaking changes: still possible in `0.x`, but should be clearly called out in the changelog and release notes

Once the CLI and trace schema feel stable, move toward `1.0.0`.

## Current Release Model

Steplight uses a hybrid approach:

- `v0.1.0` is cut manually as the first public baseline
- future versions are prepared by `release-please`
- GitHub Releases stay tag-based
- PyPI publishing can remain a separate step until the release process settles

## Automated Semantic Versioning

The repository includes `release-please` so future releases can be driven by Conventional Commits.

Recommended commit prefixes:

- `fix:` for patch releases
- `feat:` for minor releases
- `docs:` for documentation changes
- `chore:` for internal work that usually should not trigger a release on its own

This keeps version bumps, tags, and changelog updates consistent without forcing a full publish pipeline immediately.

## Recommended Release Flow

For future releases:

1. Merge changes to `main` using Conventional Commit titles.
2. Let `release-please` open or update the release PR.
3. Review the generated changelog and version changes.
4. Merge the release PR to create the tag and GitHub Release.
5. Publish to PyPI if needed.

For the initial public release:

1. Keep the package version at `0.1.0`.
2. Create an annotated `v0.1.0` tag from `main`.
3. Create the matching GitHub Release.

## Notes

- GitHub's own release model is tag-based, so using version tags is aligned with the platform.
- Release Please is a good fit for a GitHub-hosted OSS tool because it automates release PRs, changelog generation, tags, and GitHub Releases.
- If you want CI to run on release PRs, prefer a dedicated `RELEASE_PLEASE_TOKEN` secret instead of relying only on the default `GITHUB_TOKEN`.
