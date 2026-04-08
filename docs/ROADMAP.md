# Roadmap

Steplight is currently in its first public alpha. The goal is to become the local-first inspection tool for agent traces, tool-driven workflows, and LLM execution debugging.

Status legend: **done** | **in-progress** | **planned** | **future**

---

## 0.x — Alpha

### Core parsing & adapters

| Status | Feature |
|--------|---------|
| done | OpenAI responses adapter |
| done | Anthropic Messages API adapter |
| done | LangChain callback adapter |
| done | MCP log adapter |
| done | Generic YAML/JSON mapping adapter |
| planned | Expand OpenAI support for more response shapes |
| planned | Improve LangChain coverage for more callback variants |
| planned | More real-world MCP log patterns and edge cases |
| planned | Flexible generic mapping for nested/irregular payloads |
| future | LlamaIndex / CrewAI / AutoGen adapters |

### CLI commands

| Status | Feature |
|--------|---------|
| done | `slt inspect` — interactive TUI explorer |
| done | `slt summary` — non-interactive terminal summary |
| done | `slt export` — static HTML report |
| done | `slt validate` — verify trace is parseable |
| done | `slt diff` — compare two traces side-by-side |
| planned | `slt summary` batch mode (multiple files) |
| planned | JSON / CSV export formats |
| planned | CI-friendly output (JSON/JUnit + exit codes) |
| future | `slt watch` — re-run on file change |

### Diagnostics & analysis

| Status | Feature |
|--------|---------|
| done | Bottleneck detection (single step > 50% runtime) |
| done | Retry loop detection |
| done | Context growth warnings |
| done | Tool abuse detection (same tool > 3 calls) |
| done | Silent error detection |
| done | Slow tool warning (> 5s) |
| done | High cost warning |
| done | Empty output detection |
| planned | Richer timing diagnostics (stalled / imbalanced runs) |
| planned | Context-window pressure warnings |
| planned | Stronger silent-failure detection |
| planned | Cost / token breakdown by tool |
| future | Run-to-run comparison analysis |
| future | Trend analysis across many runs |
| future | Anomaly / outlier detection |

### TUI inspector

| Status | Feature |
|--------|---------|
| done | Timeline with step list |
| done | Step detail panel |
| done | Diagnostics panel |
| done | Color-coded step types |
| done | Color-coded diagnostic severity |
| done | Scrollable detail panel |
| done | Nested step indentation |
| done | Command palette (F1) with jump / filter / toggle |
| done | Cost in summary bar |
| planned | Timeline chart visualization |
| future | Streaming / live trace inspection |

### Configuration & extensibility

| Status | Feature |
|--------|---------|
| done | CLI flags for thresholds |
| planned | Project-level `.steplight.yaml` with rule config |
| planned | Custom diagnostic rules from user Python modules |
| future | Plugin system for adapters and rules |
| future | Adapter extension / registry API |

### Export & reporting

| Status | Feature |
|--------|---------|
| done | Static HTML report |
| planned | JSON export of parsed trace |
| planned | CSV export for post-processing |
| planned | Charts in HTML reports (timeline, token burn, cost) |
| future | Multi-trace dashboard (aggregated stats) |
| future | Markdown export |

### CI / integration

| Status | Feature |
|--------|---------|
| done | GitHub Actions CI (3.11, 3.12, 3.13) |
| done | Trusted PyPI publishing |
| done | Release Please with auto-merge |
| done | `slt summary --format json` for CI consumption |
| done | Non-zero exit code when diagnostics exceed threshold (`--fail-on`) |
| future | JUnit XML output for test runners |
| future | GitHub Actions action for trace analysis |

---

## Guiding Principles

- Local-first by default
- No mandatory cloud dependency
- Terminal-native, with a strong non-interactive story
- Extensible through plain Python
- Useful on day one, not only after a complex setup
