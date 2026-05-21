"""Dispatch one calibration cell and persist the ledger rows."""
from __future__ import annotations

import argparse
import contextlib
import json
import subprocess
import sys
import tempfile
import time
from collections.abc import Iterator
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
    cwd: str | None = None
    tool_uses: list[dict[str, object]] | None = None


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
        elif model.family == "xai":
            # No dedicated grok adapter exists yet, so route Wave C xai traffic
            # through the openrouter-backed hermes adapter.
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


@contextlib.contextmanager
def _effective_cwd(model: CalibrationModel, default_cwd: Path) -> Iterator[Path]:
    """Yield the working directory the model's CLI should run from.

    agy-cli scans its `cwd` aggressively on startup (project context, conversation
    history). Pointing it at REPO_ROOT during judge-only dispatches makes the call
    hang past 1800s. A throwaway tempdir gives agy an empty workspace and keeps
    its latency in the expected sub-minute range. Other CLIs continue to run from
    `default_cwd` (REPO_ROOT) where they can reach the verifier scripts.
    """
    if model.provider_cli == "agy-cli":
        with tempfile.TemporaryDirectory(prefix="calibration-agy-") as tmp:
            yield Path(tmp)
    else:
        yield default_cwd


def dispatch_prompt(
    model: CalibrationModel,
    prompt: str,
    cwd: Path,
    timeout_s: int,
) -> DispatchResult:
    plan = build_dispatch_plan(model)
    task_id = f"calibration-{model.canonical_string}-{time.time_ns()}"
    prompt = f"{plan.prompt_prefix}{prompt}"
    start = time.monotonic()

    with _effective_cwd(model, cwd) as effective_cwd:
        if plan.kind == "subprocess":
            proc = subprocess.run(
                list(plan.argv),
                input=prompt,
                text=True,
                capture_output=True,
                cwd=effective_cwd,
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
                cwd=str(effective_cwd),
            )

        if plan.kind == "runtime" and plan.agent_name:
            result = runner.invoke(
                plan.agent_name,
                prompt,
                mode=plan.mode,
                cwd=effective_cwd,
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
                cwd=str(effective_cwd),
            )

    raise NotImplementedError(f"unknown dispatch plan kind: {plan.kind}")


def _paths_for_cell(
    *,
    output_root: Path,
    run_date: str,
    cell_id: str,
    replicate_seq: int = 0,
) -> tuple[Path, Path]:
    run_dir = output_root / run_date
    response_dir = run_dir / "responses"
    response_dir.mkdir(parents=True, exist_ok=True)
    suffix = f".replicate-{replicate_seq}" if replicate_seq else ""
    response_path = response_dir / f"{cell_id}{suffix}.md"
    results_path = run_dir / "results.jsonl"
    return response_path, results_path


def _append_jsonl(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(payload, sort_keys=True) + "\n")


def _git_dirty_paths(repo_root: Path) -> set[str]:
    result = subprocess.run(
        [
            "git",
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
        ],
        cwd=repo_root,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return set()

    paths: set[str] = set()
    parts = result.stdout.split(b"\0")
    i = 0
    while i < len(parts):
        entry = parts[i]
        if not entry:
            i += 1
            continue
        status = entry[:2].decode("utf-8", errors="replace")
        path = entry[3:].decode("utf-8", errors="replace")
        if path:
            paths.add(path)
        i += 1
        if "R" in status or "C" in status:
            if i < len(parts) and parts[i]:
                paths.add(parts[i].decode("utf-8", errors="replace"))
            i += 1
    return paths


def run_cell(
    *,
    lane: str,
    canonical_string: str,
    fixture_id: str,
    run_date: str | None = None,
    db_path: Path = DEFAULT_DB_PATH,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    timeout_s: int = 3600,
    replicate_seq: int = 0,
    dispatch_fn: DispatchFn = dispatch_prompt,
) -> str:
    if lane not in LANES:
        raise ValueError(f"unknown calibration lane: {lane}")
    if replicate_seq < 0:
        raise ValueError("replicate_seq must be >= 0")

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
        replicate_seq=replicate_seq,
    )

    dirty_before = _git_dirty_paths(REPO_ROOT)
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
                replicate_seq=replicate_seq,
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
                replicate_seq=replicate_seq,
            )
        raise
    dirty_after = _git_dirty_paths(REPO_ROOT)
    touched_paths = sorted(dirty_after - dirty_before)
    git_tool_uses = [
        {"path": path, "source": "git_status_after_dispatch"}
        for path in touched_paths
    ]
    tool_uses = [*(result.tool_uses or []), *git_tool_uses]

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
            cwd=result.cwd or str(REPO_ROOT),
            tool_uses=tool_uses or None,
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
            "replicate_seq": replicate_seq,
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
    parser.add_argument("--replicate-seq", type=int, default=0)
    parser.add_argument(
        "--no-render",
        action="store_true",
        help="Skip rendering calibration HTML reports after scoring.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    run_date = args.run_date or schema.today_iso()
    cell_id = run_cell(
        lane=args.lane,
        canonical_string=args.canonical_string,
        fixture_id=args.fixture_id,
        run_date=run_date,
        db_path=args.db_path,
        output_root=args.output_root,
        timeout_s=args.timeout_s,
        replicate_seq=args.replicate_seq,
    )
    from . import report, score_cell

    # score inserts are upserts, so explicit score_cell reruns do not duplicate rows.
    score_cell.score_cell(
        cell_id=cell_id,
        db_path=args.db_path,
        replicate_seq=args.replicate_seq,
    )
    if not args.no_render:
        out_dir = report.report_dir_for_run(run_date, output_root=args.output_root)
        print(f"rendering calibration reports to {out_dir}", file=sys.stderr)
        written = report.render_reports(
            db_path=args.db_path,
            out_dir=out_dir,
            run_date=run_date,
        )
        print(
            f"rendered calibration reports: {len(written)} file(s)",
            file=sys.stderr,
        )
    print(cell_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
