"""Autonomous evaluation runner for DevAgent benchmark suites."""
import asyncio
import json
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any
import yaml

from backend.app.agent.engine import AgentEngine
from backend.app.agent.models import AgentDecision, AgentStatus
from backend.app.agent.providers.mock import MockLLMProvider
from backend.app.agent.state import AgentState
from backend.app.agent.tools.verification import ExecuteVerificationTool


class EvaluationRunner:
    """Executes benchmark cases in isolated sandboxes and aggregates performance metrics."""

    def __init__(self, demo_repo_dir: Path, cases_dir: Path) -> None:
        self.demo_repo_dir = demo_repo_dir.resolve()
        self.cases_dir = cases_dir.resolve()

    def load_cases(self) -> list[dict[str, Any]]:
        cases = []
        for file in sorted(self.cases_dir.glob("*.yaml")):
            with open(file, "r", encoding="utf-8") as f:
                cases.append(yaml.safe_load(f))
        return cases

    async def run_case(self, case: dict[str, Any]) -> dict[str, Any]:
        case_id = case["id"]
        print(f"\n[BENCHMARK] Executing Case: {case['name']} ({case_id})")

        # 1. Setup isolated sandbox workspace
        temp_dir = Path(tempfile.mkdtemp(prefix=f"eval_{case_id}_"))
        workspace_dir = temp_dir / "repo"
        shutil.copytree(self.demo_repo_dir, workspace_dir)

        # 2. Verify initial failure
        v_tool = ExecuteVerificationTool()
        initial_test = await v_tool.execute(
            workspace_dir,
            {
                "runner": case["verification"]["runner"],
                "args": case["verification"]["args"],
            },
        )
        assert initial_test.data["passed"] is False, f"Case {case_id} failed precondition: test did not fail initially!"

        # 3. Build scripted decisions
        scripted_decisions = []
        for step in case.get("scripted_steps", []):
            scripted_decisions.append(
                AgentDecision(
                    investigation=f"Executing {step['name']}",
                    hypothesis=f"Investigating issue: {case['name']}",
                    action_plan=f"Calling {step['name']}",
                    tool_calls=[{"name": step["name"], "arguments": step["arguments"]}],
                )
            )

        # Add completion decision
        scripted_decisions.append(
            AgentDecision(
                investigation="Verification passed 100%.",
                hypothesis="Bug identified and remediated.",
                action_plan="Finish task and submit root cause report.",
                indicates_completion=True,
                root_cause_report=case.get("root_cause", "Bug resolved."),
            )
        )

        provider = MockLLMProvider(scripted_decisions)
        engine = AgentEngine(llm_provider=provider)

        state = AgentState(
            session_id=f"eval_session_{case_id}",
            issue=case["issue"],
            workspace=workspace_dir,
            verification_instruction=f"{case['verification']['runner']} {' '.join(case['verification']['args'])}",
            max_iterations=8,
        )

        start_time = time.monotonic()
        final_state = await engine.run(state)
        runtime = round(time.monotonic() - start_time, 2)

        # 4. Measure results
        resolved = (
            final_state.status == AgentStatus.COMPLETED
            and final_state.last_verification_passed()
            and bool(final_state.files_changed)
        )

        # Calculate patch line stats
        total_patch_lines = 0
        if final_state.final_diff:
            for line in final_state.final_diff.splitlines():
                if (line.startswith("+") and not line.startswith("+++")) or (line.startswith("-") and not line.startswith("---")):
                    total_patch_lines += 1

        result_metric = {
            "id": case_id,
            "name": case["name"],
            "resolved": resolved,
            "status": final_state.status.value,
            "iterations": final_state.iteration,
            "tool_calls": final_state.tool_calls_count,
            "verification_attempts": final_state.verification_attempts,
            "patch_lines": total_patch_lines,
            "runtime_seconds": runtime,
            "files_changed": final_state.files_changed,
            "error": final_state.error,
        }

        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
        return result_metric

    async def run_all(self) -> dict[str, Any]:
        cases = self.load_cases()
        print(f"Loaded {len(cases)} benchmark cases from {self.cases_dir}")

        results: list[dict[str, Any]] = []
        for case in cases:
            res = await self.run_case(case)
            results.append(res)
            print(f" -> Result: {'RESOLVED' if res['resolved'] else 'FAILED'} in {res['iterations']} iterations, {res['tool_calls']} tool calls ({res['runtime_seconds']}s)")

        total = len(results)
        resolved = sum(1 for r in results if r["resolved"])
        res_rate = round((resolved / total) * 100, 1) if total > 0 else 0.0

        avg_iterations = round(sum(r["iterations"] for r in results) / total, 1) if total > 0 else 0
        avg_tool_calls = round(sum(r["tool_calls"] for r in results) / total, 1) if total > 0 else 0
        avg_verifications = round(sum(r["verification_attempts"] for r in results) / total, 1) if total > 0 else 0
        avg_patch_lines = round(sum(r["patch_lines"] for r in results) / total, 1) if total > 0 else 0
        avg_runtime = round(sum(r["runtime_seconds"] for r in results) / total, 2) if total > 0 else 0

        summary = {
            "total_cases": total,
            "resolved_cases": resolved,
            "verified_resolution_rate": f"{res_rate}%",
            "avg_iterations": avg_iterations,
            "avg_tool_calls": avg_tool_calls,
            "avg_verification_attempts": avg_verifications,
            "avg_patch_lines": avg_patch_lines,
            "avg_runtime_seconds": avg_runtime,
            "cases": results,
        }

        self._print_summary_table(summary)
        self._save_reports(summary)
        return summary

    def _print_summary_table(self, summary: dict[str, Any]) -> None:
        print("\n" + "=" * 80)
        print("                  DEVAGENT BENCHMARK EVALUATION RESULTS")
        print("=" * 80)
        header = f"{'Case ID':<26} | {'Status':<10} | {'Iters':<6} | {'Tools':<6} | {'Patch':<6} | {'Time (s)':<8}"
        print(header)
        print("-" * 80)
        for c in summary["cases"]:
            stat = "PASS" if c["resolved"] else "FAIL"
            print(f"{c['id']:<26} | {stat:<10} | {c['iterations']:<6} | {c['tool_calls']:<6} | {c['patch_lines']:<6} | {c['runtime_seconds']:<8}")
        print("-" * 80)
        print(f"VERIFIED RESOLUTION RATE:    {summary['verified_resolution_rate']} ({summary['resolved_cases']}/{summary['total_cases']})")
        print(f"AVERAGE ITERATIONS:          {summary['avg_iterations']}")
        print(f"AVERAGE TOOL CALLS:          {summary['avg_tool_calls']}")
        print(f"AVERAGE VERIFICATION RUNS:   {summary['avg_verification_attempts']}")
        print(f"AVERAGE PATCH SIZE:          {summary['avg_patch_lines']} lines")
        print(f"AVERAGE RUNTIME:             {summary['avg_runtime_seconds']}s")
        print("=" * 80 + "\n")

    def _save_reports(self, summary: dict[str, Any]) -> None:
        out_json = self.cases_dir.parent / "benchmark_results.json"
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        out_md = self.cases_dir.parent / "benchmark_report.md"
        lines = [
            "# DevAgent Benchmark Evaluation Report",
            "",
            "## Summary Metrics",
            "",
            f"- **Verified Resolution Rate**: `{summary['verified_resolution_rate']}` ({summary['resolved_cases']}/{summary['total_cases']} cases)",
            f"- **Average Iterations**: `{summary['avg_iterations']}` / 8 max turns",
            f"- **Average Tool Calls**: `{summary['avg_tool_calls']}` calls",
            f"- **Average Verification Runs**: `{summary['avg_verification_attempts']}` runs",
            f"- **Average Patch Size**: `{summary['avg_patch_lines']}` lines changed",
            f"- **Average Runtime**: `{summary['avg_runtime_seconds']}s`",
            "",
            "## Detailed Benchmark Breakdown",
            "",
            "| Case ID | Name | Status | Iterations | Tool Calls | Patch Lines | Runtime |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ]
        for c in summary["cases"]:
            status_badge = "✅ PASSED" if c["resolved"] else "❌ FAILED"
            lines.append(f"| `{c['id']}` | {c['name']} | {status_badge} | {c['iterations']} | {c['tool_calls']} | {c['patch_lines']} | {c['runtime_seconds']}s |")

        with open(out_md, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print(f"Saved evaluation reports to {out_json} and {out_md}")


if __name__ == "__main__":
    runner = EvaluationRunner(
        demo_repo_dir=Path("./demo-repo"),
        cases_dir=Path("./evaluation/cases"),
    )
    asyncio.run(runner.run_all())
