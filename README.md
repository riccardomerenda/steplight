# Steplight

Local-first trace inspector for LLM agents and tool-driven workflows.

> Load a trace. See what happened. Understand why.

Steplight is a terminal-native tool for inspecting LLM runs, tool calls, retries, token usage, errors, and execution bottlenecks without sending trace data to a third-party platform.

It is designed for developers building with OpenAI-style workflows, LangChain, MCP tooling, or custom JSON/YAML traces who want a fast local debugging loop and a shareable HTML report.

## Why Steplight

- Understand what your agent actually did, step by step
- Spot slow tools, retry loops, and cost spikes quickly
- Keep sensitive traces on your own machine
- Stay in the terminal instead of digging through raw JSON by hand
- Share a polished HTML report when you need feedback from teammates

## Features

- Interactive Textual inspector with color-coded timeline, scrollable details, and command palette (F1)
- Trace comparison (`slt diff`) to spot regressions in duration, tokens, cost, and step composition
- Rich terminal summary with JSON output (`--format json`) for CI pipelines
- Non-zero exit codes on diagnostic thresholds (`--fail-on warning`)
- Static HTML export for sharing a run with other people
- Built-in diagnostics for common agent failure patterns (bottlenecks, retry loops, cost spikes, context growth, and more)
- Support for OpenAI-style traces, Anthropic Messages API, LangChain callbacks, MCP logs, and generic JSON/YAML
- Extensible adapters and rules so you can grow it with your workflow

## Install

```bash
pip install steplight
```

The package installs both `steplight` and the shorter `slt` alias. The examples below use `slt` to avoid PowerShell's reserved `sl` alias.

## Quick Start

```bash
slt summary sample_traces/agent_with_tools.json
slt summary sample_traces/agent_with_tools.json --format json
slt summary sample_traces/agent_with_tools.json --fail-on warning
slt diff sample_traces/agent_with_tools.json sample_traces/expensive_run.json
slt validate sample_traces/simple_qa.json
slt export sample_traces/expensive_run.json -o report.html
slt inspect sample_traces/agent_with_tools.json
```

## Example Summary Output

```text
+------------------------ Steplight Summary ------------------------+
| Run: Find compliance gaps in policy                               |
| Source: openai                                                    |
| Overview: Duration: 14.0s | Steps: 4 | Tool calls: 2 | Retries: 0 |
| Tokens: 4,230 in / 670 out | Est. cost: $0.0028                   |
+-------------------------------------------------------------------+

Diagnostics
- WARNING: Step 'web_search' took 68.6% of total runtime.
- WARNING: Tool 'web_search' took 9.6s. Check timeouts, caching, or external latency.
- INFO: Input tokens grew 4.2x between 'Draft plan' and 'Final answer'.
Bottleneck: web_search (68.6% of total runtime)
```

## Example Diff Output

```text
Comparing: Find compliance gaps in policy  ->  Long form research synthesis

                        Stats
Metric     |    Base |    Head |               Change
-----------+---------+---------+---------------------
Duration   |  14.00s |  40.00s |    +26.00s (+185.7%)
Steps      |       4 |       7 |          +3 (+75.0%)
Tool calls |       2 |       4 |         +2 (+100.0%)
Retries    |       0 |       0 |                    0
Tokens in  |   4,230 |   5,100 |        +870 (+20.6%)
Tokens out |     670 |   1,800 |     +1,130 (+168.7%)
Cost       | $0.0028 | $0.4500 | +$0.4472 (+16180.8%)

Step type changes
  prompt         0 -> 1  +1
  tool_call      2 -> 4  +2
```

## Supported Trace Formats

- OpenAI-style step traces
- Anthropic Messages API conversation traces (text + tool_use + tool_result blocks)
- LangChain callback event exports
- MCP tool call logs
- Generic JSON or YAML with an optional `steplight.yaml` mapping file

## Diagnostics

Steplight currently flags:

- bottlenecks
- retry loops
- context growth
- repeated tool calls
- silent errors
- slow tools
- high-cost runs
- empty completions

## Custom Mapping Example

```yaml
mapping:
  steps_path: "$.events"
  timestamp_field: "ts"
  type_field: "event_type"
  type_values:
    prompt: "llm_start"
    completion: "llm_end"
    tool_call: "tool_start"
    tool_result: "tool_end"
```

## Commands

- `slt inspect <file>` opens the interactive Textual UI
- `slt summary <file>` prints a non-interactive terminal summary
- `slt summary <file> --format json` outputs machine-readable JSON
- `slt summary <file> --fail-on warning` exits with code 1 if diagnostics fire
- `slt diff <base> <head>` compares two traces side-by-side
- `slt export <file> -o report.html` creates a static HTML report
- `slt validate <file>` checks whether a trace can be parsed successfully

## Docs

- [Roadmap](docs/ROADMAP.md)
- [Versioning and Releases](docs/VERSIONING.md)
- [Release Process](RELEASING.md)

## Repository Layout

```text
steplight/
  cli/
  core/
  adapters/
  tui/
  export/
sample_traces/
tests/
```

## Development

```bash
python -m pip install -e .[dev]
pytest
python -m steplight.cli.main --help
```

## Releasing

Releases are fully automated. Push to `main` using conventional commit messages (`feat:`, `fix:`, etc.) and the pipeline handles the rest:

1. CI runs tests on Python 3.11, 3.12, and 3.13
2. Release Please creates a version bump PR with changelog
3. The PR auto-merges after CI passes
4. A GitHub Release is created and the package is published to PyPI

## Status

Steplight is currently an alpha-stage project focused on a clean local-first inspection experience, a solid parser surface, and practical diagnostics.

## License

MIT
