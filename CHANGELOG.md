# Changelog

All notable changes to this project will be documented in this file.

## [0.3.1](https://github.com/riccardomerenda/steplight/compare/steplight-v0.3.0...steplight-v0.3.1) (2026-04-05)


### Documentation

* update README and RELEASING for diff command and automated releases ([1f69c21](https://github.com/riccardomerenda/steplight/commit/1f69c210e81d67984a8134bc44ffa80fc7dbe080))

## [0.3.0](https://github.com/riccardomerenda/steplight/compare/steplight-v0.2.0...steplight-v0.3.0) (2026-04-05)


### Features

* **cli:** add trace diff command and structured roadmap ([a2a23eb](https://github.com/riccardomerenda/steplight/commit/a2a23eb6b54d8c813025be9fce0a1bd727005b87))

## [0.2.0](https://github.com/riccardomerenda/steplight/compare/steplight-v0.1.0...steplight-v0.2.0) (2026-04-03)


### Features

* **tui:** improve inspect view with colors, scrolling, and command palette ([c6ee2d1](https://github.com/riccardomerenda/steplight/commit/c6ee2d17440d92a1b3d85e9b731ce266277b1f00))

## [0.1.0] - 2026-04-03

### Added

- Initial Steplight release
- CLI commands for `inspect`, `summary`, `export`, and `validate`
- Trace adapters for OpenAI-style, LangChain, MCP, and generic JSON/YAML inputs
- Automated diagnostics for bottlenecks, retry loops, context growth, repeated tools, silent errors, slow tools, high cost, and empty outputs
- Textual TUI for interactive inspection
- Static HTML export with a shareable timeline report
- Public roadmap, versioning, and release documentation
- Baseline GitHub release automation with Release Please
- Sample traces and automated test coverage
