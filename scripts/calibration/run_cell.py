"""Dispatch one calibration cell and persist the ledger rows."""
from __future__ import annotations

import argparse
import json
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from scripts.agent_runtime import runner
from scripts.agent_runtime.errors import AgentTimeoutError

from . import schema
from .models import CalibrationModel, LANES, model_by_canonical

REPO_ROOT = Path(__file__).resolve().parents[2]
PROMPT_ROOT = REPO_ROOT / "scripts" / "calibration" / "prompts" / "v1"
DEFAULT_DB_PATH = REPO_ROOT / "calibration" / "v1" / "ledger.db"
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "calibration" / "v1"


@dataclass(frozen=True)
class DispatchPlan:
    kind: str
    argv: tuple[str, ...] = ()
    agent_name: str | None = None
    mode: str = "read-only"
    model: str | None = None
    prompt_prefix: str = ""


@dataclass(frozen=True)
class DispatchResult:
    response: str
    task_id: str
    latency_s: float
    cost_usd: float | None = None
    returncode: int | None = 0
    stderr_excerpt: str | None = None


DispatchFn = Callable[[CalibrationModel, str, Path, int], DispatchResult]


def load_fixture_prompt(lane: str, fixture_id: str) -> str:
    path = PROMPT_ROOT / lane / f"{fixture_id}.md"
    if not path.exists():
        raise FileNotFoundError(f"missing calibration fixture prompt: {path}")
    return path.read_text(encoding="utf-8")


def build_dispatch_plan(model: CalibrationModel) -> DispatchPlan:
    if model.provider_cli == "claude-cli" and model.effort_mechanism == "native_flag":
        return DispatchPlan(
            kind="subprocess",
            argv=(
                "claude",
                "-p",
                "--effort",
                model.effort_requested,
                "--model",
                model.canonical_string,
            ),
        )
    if model.provider_cli == "claude-cli" and model.effort_mechanism == "none":
        return DispatchPlan(
            kind="subprocess",
            argv=("claude", "-p", "--model", model.canonical_string),
        )
    if model.provider_cli == "codex-cli" and model.effort_mechanism == "cli_config":
        return DispatchPlan(
            kind="subprocess",
            argv=(
                "codex",
                "exec",
                "--skip-git-repo-check",
                "-C",
                str(REPO_ROOT),
                "--color",
                "never",
                "--model",
                model.canonical_string,
                "-c",
                f"model_reasoning_effort={model.effort_requested}",
                "-",
            ),
        )
    if model.provider_cli == "agy-cli" and model.effort_mechanism == "model_name_suffix":
        return DispatchPlan(
            kind="runtime",
            agent_name="agy",
            mode="danger",
            model=model.canonical_string,
        )
    if model.provider_cli == "gemini-cli" and model.effort_mechanism == "model_name_suffix":
        return DispatchPlan(
            kind="runtime",
            agent_name="gemini",
            mode="read-only",
            model=model.canonical_string,
        )
    if model.provider_cli == "hermes" and model.effort_mechanism == "prompt_prefix_hint":
        if model.family == "deepseek":
            agent_name = "deepseek"
        elif model.family == "alibaba":
            agent_name = "qwen"
        else:
            raise NotImplementedError(
                "hermes prompt-prefix dispatch is not implemented for "
                f"family={model.family!r}, model={model.canonical_string!r}"
            )
        return DispatchPlan(
            kind="runtime",
            agent_name=agent_name,
            mode="read-only",
            model=model.canonical_string,
            prompt_prefix=(
                f"[Reasoning effort hint: {model.effort_requested}]\n\n"
            ),
        )
    raise NotImplementedError(
        "unsupported calibration dispatch combination: "
        f"provider_cli={model.provider_cli}, "
        f"effort_mechanism={model.effort_mechanism}"
    )


def dispatch_prompt(
    model: CalibrationModel,
    prompt: str,
    cwd: Path,
    timeout_s: int,
) -> DispatchResult:
    plan = build_dispatch_plan(model)
    task_id = f"calibration-{model.canonical_string}-{int(time.time())}"
    prompt = f"{plan.prompt_prefix}{prompt}"
    start = time.monotonic()

    if plan.kind == "subprocess":
        proc = subprocess.run(
            list(plan.argv),
            input=prompt,
            text=True,
            capture_output=True,
            cwd=cwd,
            timeout=timeout_s,
            check=False,
        )
        latency_s = time.monotonic() - start
        response = (proc.stdout or "").strip()
        stderr_excerpt = (proc.stderr or "").strip()[:500] or None
        if proc.returncode != 0 or not response:
            raise RuntimeError(
                f"dispatch failed for {model.canonical_string} "
                f"(rc={proc.returncode}): {stderr_excerpt or 'empty response'}"
            )
        return DispatchResult(
            response=response,
            task_id=task_id,
            latency_s=latency_s,
            returncode=proc.returncode,
            stderr_excerpt=stderr_excerpt,
        )

    if plan.kind == "runtime" and plan.agent_name:
        result = runner.invoke(
            plan.agent_name,
            prompt,
            mode=plan.mode,
            cwd=cwd,
            model=plan.model,
            task_id=task_id,
            entrypoint="calibration",
            hard_timeout=timeout_s,
            tool_config={"isolated": True},
        )
        return DispatchResult(
            response=result.response,
            task_id=task_id,
            latency_s=result.duration_s,
            cost_usd=result.usage_record.get("cost_usd"),
            returncode=result.returncode,
            stderr_excerpt=result.stderr_excerpt,
        )

    raise NotImplementedError(f"unknown dispatch plan kind: {plan.kind}")


def _paths_for_cell(
    *,
    output_root: Path,
    run_date: str,
    cell_id: str,
) -> tuple[Path, Path]:
    run_dir = output_root / run_date
    response_dir = run_dir / "responses"
    response_dir.mkdir(parents=True, exist_ok=True)
    response_path = response_dir / f"{cell_id}.md"
    results_path = run_dir / "results.jsonl"
    return response_path, results_path


def _append_jsonl(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(payload, sort_keys=True) + "\n")


def run_cell(
    *,
    lane: str,
    canonical_string: str,
    fixture_id: str,
    run_date: str | None = None,
    db_path: Path = DEFAULT_DB_PATH,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    timeout_s: int = 3600,
    dispatch_fn: DispatchFn = dispatch_prompt,
) -> str:
    if lane not in LANES:
        raise ValueError(f"unknown calibration lane: {lane}")

    run_date = run_date or schema.today_iso()
    model = model_by_canonical(canonical_string)
    prompt = load_fixture_prompt(lane, fixture_id)
    cell_row = schema.build_cell_row(
        lane=lane,
        fixture_id=fixture_id,
        model=model,
        run_date=run_date,
    )
    cell_id = str(cell_row["cell_id"])

    schema.init_db(db_path)
    with schema.connect(db_path) as conn:
        schema.insert_cell(conn, cell_row)

    response_path, results_path = _paths_for_cell(
        output_root=output_root,
        run_date=run_date,
        cell_id=cell_id,
    )

    try:
        result = dispatch_fn(model, prompt, REPO_ROOT, timeout_s)
    except subprocess.TimeoutExpired:
        with schema.connect(db_path) as conn:
            schema.insert_score(
                conn,
                cell_id=cell_id,
                gate_name="dispatch_completed",
                gate_pass=False,
                score_value=0.0,
            )
        raise
    except AgentTimeoutError:
        with schema.connect(db_path) as conn:
            schema.insert_score(
                conn,
                cell_id=cell_id,
                gate_name="dispatch_completed",
                gate_pass=False,
                score_value=0.0,
            )
        raise

    response_path.write_text(result.response, encoding="utf-8")
    try:
        relative_response_path = str(response_path.relative_to(REPO_ROOT))
    except ValueError:
        relative_response_path = str(response_path)
    with schema.connect(db_path) as conn:
        schema.insert_dispatch(
            conn,
            cell_id=cell_id,
            task_id=result.task_id,
            response_path=relative_response_path,
            latency_s=result.latency_s,
            cost_usd=result.cost_usd,
            returncode=result.returncode,
            stderr_excerpt=result.stderr_excerpt,
        )

    _append_jsonl(
        results_path,
        {
            "cell_id": cell_id,
            "lane": lane,
            "fixture_id": fixture_id,
            "canonical_string": canonical_string,
            "effort_requested": model.effort_requested,
            "run_date": run_date,
            "task_id": result.task_id,
            "response_path": relative_response_path,
            "latency_s": result.latency_s,
            "cost_usd": result.cost_usd,
        },
    )
    return cell_id


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run one calibration cell")
    parser.add_argument("--lane", required=True, choices=LANES)
    parser.add_argument("--canonical-string", required=True)
    parser.add_argument("--fixture-id", required=True)
    parser.add_argument("--run-date")
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--timeout-s", type=int, default=3600)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    cell_id = run_cell(
        lane=args.lane,
        canonical_string=args.canonical_string,
        fixture_id=args.fixture_id,
        run_date=args.run_date,
        db_path=args.db_path,
        output_root=args.output_root,
        timeout_s=args.timeout_s,
    )
    print(cell_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
