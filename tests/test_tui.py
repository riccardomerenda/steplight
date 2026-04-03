import asyncio
from pathlib import Path

from steplight.core.analyzer import analyze_trace
from steplight.core.parser import parse_trace_file
from steplight.tui.app import SteplightApp


ROOT = Path(__file__).resolve().parents[1]


def test_tui_smoke() -> None:
    async def run() -> None:
        trace = parse_trace_file(ROOT / "sample_traces" / "agent_with_tools.json")
        app = SteplightApp(trace, analyze_trace(trace))
        async with app.run_test() as pilot:
            await pilot.pause()

    asyncio.run(run())
