from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from steplight.core.models import Diagnostic, Severity, Step, StepType, Trace
from steplight.core.stats import compute_trace_stats, trace_duration_ms


@dataclass(slots=True)
class AnalyzerConfig:
    high_cost_threshold_usd: float = 0.10
    slow_tool_threshold_ms: float = 5000.0


class Rule:
    name = "rule"

    def evaluate(self, trace: Trace, config: AnalyzerConfig) -> list[Diagnostic]:
        raise NotImplementedError


class BottleneckRule(Rule):
    name = "bottleneck"

    def evaluate(self, trace: Trace, config: AnalyzerConfig) -> list[Diagnostic]:
        total = trace_duration_ms(trace)
        if total <= 0:
            return []
        slowest = max((step for step in trace.steps if step.duration_ms), key=lambda step: step.duration_ms or 0, default=None)
        if slowest is None or not slowest.duration_ms:
            return []
        share = slowest.duration_ms / total
        if share <= 0.5:
            return []
        pct = round(share * 100, 1)
        return [
            Diagnostic(
                rule=self.name,
                severity=Severity.WARNING,
                step_id=slowest.id,
                message=f"Step '{slowest.name or slowest.type.value}' took {pct}% of total runtime.",
                metadata={"share": share},
            )
        ]


class RetryLoopRule(Rule):
    name = "retry_loop"

    def evaluate(self, trace: Trace, config: AnalyzerConfig) -> list[Diagnostic]:
        diagnostics: list[Diagnostic] = []
        current: list[Step] = []

        def flush() -> None:
            if len(current) >= 2:
                name = current[-1].name or current[-1].metadata.get("target_step") or "retry"
                diagnostics.append(
                    Diagnostic(
                        rule=self.name,
                        severity=Severity.WARNING,
                        step_id=current[-1].id,
                        message=f"Retry loop detected on '{name}' ({len(current)} attempts).",
                        metadata={"attempts": len(current)},
                    )
                )

        for step in trace.steps:
            if step.type == StepType.RETRY:
                current.append(step)
            else:
                flush()
                current = []
        flush()
        return diagnostics


class ContextGrowthRule(Rule):
    name = "context_growth"

    def evaluate(self, trace: Trace, config: AnalyzerConfig) -> list[Diagnostic]:
        diagnostics: list[Diagnostic] = []
        previous = None
        for step in trace.steps:
            if not step.tokens_in:
                continue
            if previous and previous.tokens_in and step.tokens_in > previous.tokens_in * 2:
                growth = step.tokens_in / previous.tokens_in
                diagnostics.append(
                    Diagnostic(
                        rule=self.name,
                        severity=Severity.INFO,
                        step_id=step.id,
                        message=(
                            f"Input tokens grew {growth:.1f}x between "
                            f"'{previous.name or previous.id}' and '{step.name or step.id}'."
                        ),
                        metadata={"growth": round(growth, 2)},
                    )
                )
            previous = step
        return diagnostics


class ToolAbuseRule(Rule):
    name = "tool_abuse"

    def evaluate(self, trace: Trace, config: AnalyzerConfig) -> list[Diagnostic]:
        counts = Counter(step.name or "tool" for step in trace.steps if step.type == StepType.TOOL_CALL)
        diagnostics: list[Diagnostic] = []
        for tool_name, count in counts.items():
            if count > 3:
                diagnostics.append(
                    Diagnostic(
                        rule=self.name,
                        severity=Severity.WARNING,
                        message=f"Tool '{tool_name}' was called {count} times. Consider batching or caching.",
                        metadata={"count": count, "tool": tool_name},
                    )
                )
        return diagnostics


class SilentErrorRule(Rule):
    name = "silent_error"

    def evaluate(self, trace: Trace, config: AnalyzerConfig) -> list[Diagnostic]:
        if (trace.status or "").lower() not in {"success", "completed", "ok"}:
            return []
        diagnostics: list[Diagnostic] = []
        for step in trace.steps:
            if step.error or step.type == StepType.ERROR:
                diagnostics.append(
                    Diagnostic(
                        rule=self.name,
                        severity=Severity.ERROR,
                        step_id=step.id,
                        message=f"Step '{step.name or step.type.value}' failed but the run is marked as successful.",
                    )
                )
        return diagnostics


class SlowToolRule(Rule):
    name = "slow_tool"

    def evaluate(self, trace: Trace, config: AnalyzerConfig) -> list[Diagnostic]:
        diagnostics: list[Diagnostic] = []
        for step in trace.steps:
            if step.type != StepType.TOOL_CALL or not step.duration_ms:
                continue
            if step.duration_ms > config.slow_tool_threshold_ms:
                diagnostics.append(
                    Diagnostic(
                        rule=self.name,
                        severity=Severity.WARNING,
                        step_id=step.id,
                        message=(
                            f"Tool '{step.name or step.id}' took {step.duration_ms / 1000:.1f}s. "
                            "Check timeouts, caching, or external latency."
                        ),
                    )
                )
        return diagnostics


class HighCostRule(Rule):
    name = "high_cost"

    def evaluate(self, trace: Trace, config: AnalyzerConfig) -> list[Diagnostic]:
        stats = compute_trace_stats(trace)
        if stats.total_cost_usd is None or stats.total_cost_usd <= config.high_cost_threshold_usd:
            return []
        return [
            Diagnostic(
                rule=self.name,
                severity=Severity.WARNING,
                message=(
                    f"Run cost ${stats.total_cost_usd:.3f}, above the configured "
                    f"${config.high_cost_threshold_usd:.2f} threshold."
                ),
                metadata={"threshold": config.high_cost_threshold_usd},
            )
        ]


class EmptyOutputRule(Rule):
    name = "empty_output"

    def evaluate(self, trace: Trace, config: AnalyzerConfig) -> list[Diagnostic]:
        diagnostics: list[Diagnostic] = []
        for step in trace.steps:
            if step.type == StepType.COMPLETION and not (step.output or "").strip():
                diagnostics.append(
                    Diagnostic(
                        rule=self.name,
                        severity=Severity.INFO,
                        step_id=step.id,
                        message=f"Completion step '{step.name or step.id}' returned empty output.",
                    )
                )
        return diagnostics


DEFAULT_RULES: tuple[Rule, ...] = (
    BottleneckRule(),
    RetryLoopRule(),
    ContextGrowthRule(),
    ToolAbuseRule(),
    SilentErrorRule(),
    SlowToolRule(),
    HighCostRule(),
    EmptyOutputRule(),
)


def analyze_trace(trace: Trace, config: AnalyzerConfig | None = None) -> list[Diagnostic]:
    analyzer_config = config or AnalyzerConfig()
    diagnostics: list[Diagnostic] = []
    for rule in DEFAULT_RULES:
        diagnostics.extend(rule.evaluate(trace, analyzer_config))

    severity_order = {
        Severity.ERROR: 0,
        Severity.WARNING: 1,
        Severity.INFO: 2,
    }
    diagnostics.sort(key=lambda item: (severity_order[item.severity], item.rule, item.step_id or ""))
    return diagnostics
