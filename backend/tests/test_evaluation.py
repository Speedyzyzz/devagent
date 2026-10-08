"""Integration test running the evaluation suite under pytest."""
from pathlib import Path
import pytest
from evaluation.runner import EvaluationRunner


@pytest.mark.asyncio
async def test_evaluation_benchmark_all_cases() -> None:
    runner = EvaluationRunner(
        demo_repo_dir=Path("./demo-repo"),
        cases_dir=Path("./evaluation/cases"),
    )
    summary = await runner.run_all()

    assert summary["total_cases"] == 5
    assert summary["resolved_cases"] == 5
    assert summary["verified_resolution_rate"] == "100.0%"
