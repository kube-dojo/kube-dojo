from __future__ import annotations

import argparse
import importlib.util
import json
import random
import re
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
LOCAL_API_PATH = REPO_ROOT / "scripts" / "local_api.py"


def _load_local_api() -> Any:
    spec = importlib.util.spec_from_file_location("sample_back_catalog_local_api", LOCAL_API_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load local_api from {LOCAL_API_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


local_api = _load_local_api()

POLICY_DECISION_REF = "docs/decisions/2026-05-26-tiered-back-catalog-review-policy.md"
DEFAULT_SEED = 2026
DEFAULT_SAMPLE_SIZE = 30
DEFAULT_IGNORE_ISSUES = "1504,1502,1504"
TRACK_ORDER = ("prerequisites", "linux", "cloud", "k8s", "AI/ML", "on-premises", "platform")
EXCLUDED_PATH_PREFIXES = ("k8s/cks/", "k8s/cka/labs/", "k8s/ckad/labs/")
LAB_SECTION_RE = re.compile(r"^##\s+(?P<title>.+?)\s*$", re.IGNORECASE | re.MULTILINE)
BASH_FENCE_RE = re.compile(r"^```bash[^\n]*\n(?P<body>.*?)(?:^```\s*$)", re.MULTILINE | re.DOTALL)
RUNNABLE_COMMAND_RE = re.compile(r"\b(?:kubectl|docker|helm|crictl)\b")
REVISION_PENDING_RE = re.compile(r"^revision_pending:\s*(?P<value>.*?)\s*$", re.IGNORECASE | re.MULTILINE)


def _frontmatter(text: str) -> str:
    if text.startswith("---\n") and "\n---\n" in text[4:]:
        return text[4:].split("\n---\n", 1)[0]
    return ""


def _body_without_frontmatter(text: str) -> str:
    if text.startswith("---\n") and "\n---\n" in text[4:]:
        return text[4:].split("\n---\n", 1)[1]
    return text


def _has_revision_pending(text: str) -> bool:
    match = REVISION_PENDING_RE.search(_frontmatter(text))
    if not match:
        return False
    value = match.group("value").strip().strip("'\"").lower()
    return value not in {"false", "no", "0", "off"}


def _track_for_path(rel_path: str) -> str | None:
    top = rel_path.split("/", 1)[0]
    if top in {"ai", "ai-ml-engineering"}:
        return "AI/ML"
    if top in TRACK_ORDER:
        return top
    return None


def _track_sort_key(track: str) -> tuple[int, str]:
    try:
        return TRACK_ORDER.index(track), track
    except ValueError:
        return len(TRACK_ORDER), track


def _module_slug(rel_path: str) -> str:
    stem = rel_path[:-3] if rel_path.endswith(".md") else rel_path
    return stem.replace("/", "-")


def _exercise_sections(body: str) -> list[str]:
    matches = list(LAB_SECTION_RE.finditer(body))
    sections: list[str] = []
    for index, match in enumerate(matches):
        title = match.group("title").strip().lower()
        if not (title.startswith("hands-on exercise") or title.startswith("lab")):
            continue
        next_start = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        sections.append(body[match.end():next_start])
    return sections


def _runnable_commands_in_bash(section: str) -> set[str]:
    commands: set[str] = set()
    for fence in BASH_FENCE_RE.finditer(section):
        for raw_line in fence.group("body").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            line = re.sub(r"^\$\s*", "", line)
            if RUNNABLE_COMMAND_RE.search(line):
                commands.add(line)
    return commands


def has_risky_lab_commands(text: str) -> bool:
    commands: set[str] = set()
    for section in _exercise_sections(_body_without_frontmatter(text)):
        commands.update(_runnable_commands_in_bash(section))
    return len(commands) > 5


def _git_first_commit_timestamp_on_main(repo_root: Path, rel_path: str) -> int | None:
    repo_rel_path = f"src/content/docs/{rel_path}"
    result = subprocess.run(
        ["git", "log", "--follow", "--diff-filter=A", "--format=%ct", "main", "--", repo_rel_path],
        cwd=repo_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    try:
        timestamps = [int(line) for line in result.stdout.strip().splitlines() if line.strip()]
    except ValueError:
        return None
    return min(timestamps) if timestamps else None


class GhIssueChecker:
    def __init__(
        self,
        repo_root: Path,
        *,
        ignore_issue_numbers: frozenset[int] = frozenset(),
    ) -> None:
        self.repo_root = repo_root
        self.gh = shutil.which("gh")
        self.cache: dict[str, list[dict[str, Any]]] = {}
        self.ignore_issue_numbers = ignore_issue_numbers
        self.disabled = self.gh is None
        if self.disabled:
            print("warning: gh unavailable; skipping open-issue eligibility check", file=sys.stderr)

    def open_issues_for_slug(self, slug: str) -> list[dict[str, Any]]:
        if slug in self.cache:
            return self.cache[slug]
        if self.disabled or self.gh is None:
            self.cache[slug] = []
            return []

        result = subprocess.run(
            [self.gh, "issue", "list", "--state", "open", "--search", slug, "--json", "number,title"],
            cwd=self.repo_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            print(
                f"warning: gh issue search failed for {slug}; skipping remaining open-issue checks",
                file=sys.stderr,
            )
            self.disabled = True
            self.cache[slug] = []
            return []
        try:
            issues = json.loads(result.stdout or "[]")
        except json.JSONDecodeError:
            print(
                f"warning: gh issue search returned invalid JSON for {slug}; skipping remaining open-issue checks",
                file=sys.stderr,
            )
            self.disabled = True
            self.cache[slug] = []
            return []
        if not isinstance(issues, list):
            issues = []
        filtered = [
            issue
            for issue in issues
            if isinstance(issue, dict)
            and issue.get("number") not in self.ignore_issue_numbers
            and slug in (issue.get("title") or "").lower()
        ]
        self.cache[slug] = filtered
        return filtered


def build_eligible_pool(
    repo_root: Path,
    *,
    min_score: float = 4.5,
    min_age_days: int = 0,
    ignore_issue_numbers: frozenset[int] = frozenset(),
) -> list[dict[str, Any]]:
    docs_root = repo_root / "src" / "content" / "docs"
    quality = local_api.build_quality_scores(repo_root)
    now = datetime.now(UTC)
    issue_checker = GhIssueChecker(repo_root, ignore_issue_numbers=ignore_issue_numbers)
    eligible: list[dict[str, Any]] = []

    for entry in quality.get("modules") or []:
        rel_path = str(entry.get("path") or "")
        if not rel_path:
            continue
        try:
            score = float(entry.get("score") or 0.0)
        except (TypeError, ValueError):
            continue
        if score < min_score:
            continue

        track = _track_for_path(rel_path)
        if track is None or rel_path.startswith(EXCLUDED_PATH_PREFIXES):
            continue

        path = docs_root / rel_path
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if _has_revision_pending(text) or has_risky_lab_commands(text):
            continue

        commit_ts = _git_first_commit_timestamp_on_main(repo_root, rel_path)
        if commit_ts is None:
            continue
        age_days = int((now.timestamp() - commit_ts) // 86400)
        if min_age_days > 0 and age_days <= min_age_days:
            continue

        slug = _module_slug(rel_path)
        open_issues = issue_checker.open_issues_for_slug(slug)
        if open_issues:
            continue

        eligible.append(
            {
                "module_key": rel_path[:-3] if rel_path.endswith(".md") else rel_path,
                "path": rel_path,
                "track": track,
                "rubric_score": score,
                "lines": int(entry.get("lines") or len(text.splitlines())),
                "first_commit_on_main": datetime.fromtimestamp(commit_ts, UTC).isoformat(),
                "age_days": age_days,
                "open_gh_issues": open_issues,
            }
        )

    return sorted(eligible, key=lambda module: (_track_sort_key(str(module["track"])), str(module["path"])))


def _allocate_counts(groups: dict[str, list[dict[str, Any]]], sample_size: int, *, floor: int = 3) -> dict[str, int]:
    sizes = {track: len(items) for track, items in groups.items() if items}
    target = min(sample_size, sum(sizes.values()))
    allocations = {track: 0 for track in sizes}
    if target <= 0:
        return allocations

    floor_need = sum(min(floor, size) for size in sizes.values())
    ordered_tracks = sorted(sizes, key=lambda track: (_track_sort_key(track), -sizes[track]))
    if floor_need <= target:
        for track in ordered_tracks:
            allocations[track] = min(floor, sizes[track])
    else:
        for track in sorted(sizes, key=lambda track: (-sizes[track], _track_sort_key(track))):
            if sum(allocations.values()) >= target:
                break
            allocations[track] = 1
        return allocations

    remaining = target - sum(allocations.values())
    while remaining > 0:
        candidates = [track for track in ordered_tracks if allocations[track] < sizes[track]]
        if not candidates:
            break
        weight_total = sum(sizes[track] for track in candidates)
        quotas = {
            track: remaining * (sizes[track] / weight_total)
            for track in candidates
        }
        progressed = False
        for track in candidates:
            extra = min(sizes[track] - allocations[track], int(quotas[track]))
            if extra <= 0:
                continue
            allocations[track] += extra
            remaining -= extra
            progressed = True
        if remaining <= 0:
            break
        for track in sorted(
            candidates,
            key=lambda candidate: (
                -(quotas[candidate] - int(quotas[candidate])),
                -sizes[candidate],
                _track_sort_key(candidate),
            ),
        ):
            if remaining <= 0:
                break
            if allocations[track] >= sizes[track]:
                continue
            allocations[track] += 1
            remaining -= 1
            progressed = True
        if not progressed:
            break

    return allocations


def stratified_sample(
    eligible_modules: list[dict[str, Any]],
    *,
    sample_size: int = DEFAULT_SAMPLE_SIZE,
    seed: int = DEFAULT_SEED,
    floor: int = 3,
) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for module in eligible_modules:
        groups.setdefault(str(module["track"]), []).append(module)
    for modules in groups.values():
        modules.sort(key=lambda module: str(module.get("path") or ""))

    allocations = _allocate_counts(groups, sample_size, floor=floor)
    rng = random.Random(seed)
    sampled: dict[str, list[dict[str, Any]]] = {}
    for track in sorted(groups, key=_track_sort_key):
        count = allocations.get(track, 0)
        if count >= len(groups[track]):
            selected = list(groups[track])
        else:
            selected = rng.sample(groups[track], count)
        sampled[track] = sorted(selected, key=lambda module: str(module.get("path") or ""))
    return sampled


def build_sample_plan(eligible_modules: list[dict[str, Any]], *, seed: int, sample_size: int) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for module in eligible_modules:
        groups.setdefault(str(module["track"]), []).append(module)
    sampled_by_track = stratified_sample(eligible_modules, sample_size=sample_size, seed=seed)

    modules: list[dict[str, Any]] = []
    stratification: dict[str, dict[str, Any]] = {}
    for track in sorted(groups, key=_track_sort_key):
        sampled = sampled_by_track.get(track, [])
        modules.extend(sampled)
        stratification[track] = {
            "eligible": len(groups[track]),
            "sampled": len(sampled),
            "modules": [str(module["path"]) for module in sampled],
        }

    modules.sort(key=lambda module: (_track_sort_key(str(module["track"])), str(module["path"])))
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "seed": seed,
        "policy_decision_ref": POLICY_DECISION_REF,
        "eligible_pool_size": len(eligible_modules),
        "sample_size": len(modules),
        "stratification": stratification,
        "modules": modules,
    }


def _default_output_path(repo_root: Path) -> Path:
    today = datetime.now(UTC).date().isoformat()
    return repo_root / "logs" / "quality" / f"back_catalog_sample_{today}.json"


def _format_summary(plan: dict[str, Any]) -> str:
    distribution = ", ".join(
        f"{track}={data['sampled']}"
        for track, data in plan.get("stratification", {}).items()
        if data.get("sampled")
    )
    sampled_tracks = sum(1 for data in plan.get("stratification", {}).values() if data.get("sampled"))
    return (
        f"Sampled {plan['sample_size']} modules across {sampled_tracks} tracks. "
        f"Track distribution: {distribution}"
    )


def _parse_issue_numbers(value: str) -> frozenset[int]:
    issue_numbers: set[int] = set()
    for raw_issue_number in value.split(","):
        raw_issue_number = raw_issue_number.strip()
        if not raw_issue_number:
            continue
        try:
            issue_number = int(raw_issue_number)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(
                f"ignore issue number must be an integer: {raw_issue_number!r}"
            ) from exc
        if issue_number <= 0:
            raise argparse.ArgumentTypeError("ignore issue numbers must be positive integers")
        issue_numbers.add(issue_number)
    return frozenset(issue_numbers)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sample eligible back-catalog modules for composer-2.5 review.")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--sample-size", type=int, default=DEFAULT_SAMPLE_SIZE)
    parser.add_argument("--min-age-days", type=int, default=0)
    parser.add_argument(
        "--ignore-issues",
        type=_parse_issue_numbers,
        default=_parse_issue_numbers(DEFAULT_IGNORE_ISSUES),
        metavar="N,M,...",
        help="Comma-separated open issue numbers to ignore when filtering eligible modules.",
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    eligible = build_eligible_pool(
        REPO_ROOT,
        min_age_days=args.min_age_days,
        ignore_issue_numbers=args.ignore_issues,
    )
    plan = build_sample_plan(eligible, seed=args.seed, sample_size=args.sample_size)
    print(f"Seed: {args.seed}")
    print(_format_summary(plan))

    output = args.output or _default_output_path(REPO_ROOT)
    if not output.is_absolute():
        output = REPO_ROOT / output
    if args.dry_run:
        print(json.dumps(plan, indent=2, sort_keys=True))
        return 0

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {output.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
