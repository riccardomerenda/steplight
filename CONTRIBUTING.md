# Contributing

Thanks for contributing to Steplight.

## Local setup

```bash
python -m pip install -e .[dev]
```

## Common commands

```bash
pytest
python -m steplight.cli.main --help
python -m steplight.cli.main summary sample_traces/agent_with_tools.json
python -m steplight.cli.main export sample_traces/expensive_run.json --output report.html
```

## Guidelines

- Keep the project English-only for code, docs, and release notes.
- Prefer small, focused changes with tests.
- Add or update sample traces when introducing new parser behavior.
- Keep adapters and diagnostic rules straightforward to extend.
- Prefer Conventional Commit prefixes such as `feat:`, `fix:`, `docs:`, and `chore:` so release automation can classify changes correctly.

## Pull requests

- Explain the user-facing impact clearly.
- Include tests for new behavior when practical.
- Update the README if a command, workflow, or supported format changes.
- Use a commit or squash-merge title that follows Conventional Commits whenever possible.
