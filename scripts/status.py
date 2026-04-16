#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pipeline_v2.cli import _build_status_report as build_v2_status_report
from translation_v2 import build_status as build_translation_v2_status
from ztt_status import build_status as build_ztt_status

ACTIVE_MODULE_GROUPS = (
    {
        "key": "ai_ml_learner_path",
        "issue": 244,
        "label": "AI/ML learner-path",
        "paths": (
            "src/content/docs/ai-ml-engineering/prerequisites/module-1.2-home-ai-workstation-fundamentals.md",
            "src/content/docs/ai-ml-engineering/prerequisites/module-1.3-reproducible-python-cuda-rocm-environments.md",
            "src/content/docs/ai-ml-engineering/prerequisites/module-1.4-notebooks-scripts-project-layouts.md",
            "src/content/docs/ai-ml-engineering/vector-rag/module-1.6-home-scale-rag-systems.md",
            "src/content/docs/ai-ml-engineering/mlops/module-1.11-notebooks-to-production-for-ml-llms.md",
            "src/content/docs/ai-ml-engineering/mlops/module-1.12-small-team-private-ai-platform.md",
            "src/content/docs/ai-ml-engineering/advanced-genai/module-1.10-single-gpu-local-fine-tuning.md",
            "src/content/docs/ai-ml-engineering/advanced-genai/module-1.11-multi-gpu-home-lab-fine-tuning.md",
            "src/content/docs/ai-ml-engineering/ai-infrastructure/module-1.4-local-inference-stack-for-learners.md",
            "src/content/docs/ai-ml-engineering/ai-infrastructure/module-1.5-home-ai-operations-cost-model.md",
        ),
    },
    {
        "key": "cert_prep",
        "issue": 182,
        "label": "Certification prep",
        "paths": (
            "src/content/docs/k8s/lfcs/module-1.1-exam-strategy-and-workflow.md",
            "src/content/docs/k8s/lfcs/module-1.2-essential-commands-practice.md",
            "src/content/docs/k8s/lfcs/module-1.3-running-systems-and-networking-practice.md",
            "src/content/docs/k8s/lfcs/module-1.4-storage-services-and-users-practice.md",
            "src/content/docs/k8s/lfcs/module-1.5-full-mock-exam.md",
            "src/content/docs/k8s/cnpe/module-1.1-exam-strategy-and-environment.md",
            "src/content/docs/k8s/cnpe/module-1.2-gitops-and-delivery-lab.md",
            "src/content/docs/k8s/cnpe/module-1.3-platform-apis-and-self-service-lab.md",
            "src/content/docs/k8s/cnpe/module-1.4-observability-security-and-operations-lab.md",
            "src/content/docs/k8s/cnpe/module-1.5-full-mock-exam.md",
            "src/content/docs/k8s/cnpa/module-1.1-exam-strategy-and-blueprint-review.md",
            "src/content/docs/k8s/cnpa/module-1.2-core-platform-fundamentals-review.md",
            "src/content/docs/k8s/cnpa/module-1.3-delivery-apis-and-observability-review.md",
            "src/content/docs/k8s/cnpa/module-1.4-practice-questions-set-1.md",
            "src/content/docs/k8s/cnpa/module-1.5-practice-questions-set-2.md",
            "src/content/docs/k8s/cgoa/module-1.1-exam-strategy-and-blueprint-review.md",
            "src/content/docs/k8s/cgoa/module-1.2-gitops-principles-review.md",
            "src/content/docs/k8s/cgoa/module-1.3-patterns-and-tooling-review.md",
            "src/content/docs/k8s/cgoa/module-1.4-practice-questions-set-1.md",
            "src/content/docs/k8s/cgoa/module-1.5-practice-questions-set-2.md",
        ),
    },
)

DEFERRED_MODULE_GROUPS = (
    {
        "key": "cka_mock_exams",
        "issue": 183,
        "label": "CKA mock exams",
        "directory": "src/content/docs/k8s/cka/part6-mock-exams",
        "expected_min": 3,
        "expected_max": 5,
    },
)


def _iter_en_modules(docs_root: Path) -> list[Path]:
    return sorted(
        [
            path
            for path in docs_root.glob("**/module-*.md")
            if "/uk/" not in path.as_posix()
            and ".staging." not in path.name
        ]
    )


def _iter_uk_modules(docs_root: Path) -> list[Path]:
    uk_root = docs_root / "uk"
    if not uk_root.exists():
        return []
    return sorted(
        path
        for path in uk_root.glob("**/module-*.md")
        if ".staging." not in path.name
    )


def _extract_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    _, _, rest = text.partition("---\n")
    frontmatter, _, _ = rest.partition("\n---\n")
    try:
        data = yaml.safe_load(frontmatter) or {}
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def _git_head_for_file(repo_root: Path, path: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%H", "--", str(path)],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _build_translation_summary(repo_root: Path) -> dict[str, Any]:
    docs_root = repo_root / "src" / "content" / "docs"
    en_modules = _iter_en_modules(docs_root)
    uk_root = docs_root / "uk"

    modules: list[dict[str, Any]] = []
    counts = {"synced": 0, "missing": 0, "stale": 0, "unknown": 0}

    for en_path in en_modules:
        rel = en_path.relative_to(docs_root)
        uk_path = uk_root / rel
        module_key = rel.as_posix()[:-3]
        if not uk_path.exists():
            status = "missing"
            counts[status] += 1
            modules.append(
                {
                    "module_key": module_key,
                    "status": status,
                    "uk_path": uk_path.as_posix(),
                }
            )
            continue

        uk_frontmatter = _extract_frontmatter(uk_path)
        tracked_en_file = uk_frontmatter.get("en_file")
        tracked_en_commit = str(uk_frontmatter.get("en_commit", "")).strip().strip('"')
        en_head = _git_head_for_file(repo_root, en_path)
        expected_en_file = en_path.relative_to(repo_root).as_posix()

        if tracked_en_file != expected_en_file:
            status = "stale"
        elif tracked_en_commit and en_head and tracked_en_commit == en_head:
            status = "synced"
        elif not tracked_en_commit or not en_head:
            status = "unknown"
        else:
            status = "stale"

        counts[status] += 1
        modules.append(
            {
                "module_key": module_key,
                "status": status,
                "en_commit": en_head,
                "uk_en_commit": tracked_en_commit,
                "uk_path": uk_path.as_posix(),
            }
        )

    return {
        "total_english_modules": len(en_modules),
        "uk_module_files_present": len(_iter_uk_modules(docs_root)),
        "synced": counts["synced"],
        "missing": counts["missing"],
        "stale": counts["stale"],
        "unknown": counts["unknown"],
        "sync_clean": counts["missing"] == 0 and counts["stale"] == 0 and counts["unknown"] == 0,
        "writer": "gemini-3.1-pro-preview via uk_sync.py",
        "modules": modules,
    }


def _build_lab_summary(repo_root: Path) -> dict[str, Any]:
    lab_state = _load_yaml(repo_root / ".pipeline" / "lab-state.yaml").get("labs", {})
    counts = {
        "tracked": 0,
        "done_clean": 0,
        "done_nonclean": 0,
        "pending": 0,
    }
    items: list[dict[str, Any]] = []
    for lab_id, raw in lab_state.items():
        if not isinstance(raw, dict):
            continue
        phase = str(raw.get("phase", "pending"))
        severity = str(raw.get("severity", "-"))
        counts["tracked"] += 1
        if phase == "done" and severity == "clean":
            counts["done_clean"] += 1
        elif phase == "done":
            counts["done_nonclean"] += 1
        else:
            counts["pending"] += 1
        items.append(
            {
                "lab_id": lab_id,
                "phase": phase,
                "severity": severity,
                "module": raw.get("module"),
            }
        )
    items.sort(key=lambda item: item["lab_id"])
    return {**counts, "items": items}


def _build_missing_modules_summary(repo_root: Path) -> dict[str, Any]:
    active_groups: list[dict[str, Any]] = []
    active_total = 0
    active_present = 0
    active_missing = 0

    for group in ACTIVE_MODULE_GROUPS:
        items = []
        present = 0
        missing = 0
        for rel_path in group["paths"]:
            exists = (repo_root / rel_path).exists()
            present += int(exists)
            missing += int(not exists)
            items.append({"path": rel_path, "exists": exists})
        total = len(group["paths"])
        active_total += total
        active_present += present
        active_missing += missing
        active_groups.append(
            {
                "key": group["key"],
                "issue": group["issue"],
                "label": group["label"],
                "total_expected": total,
                "present": present,
                "missing": missing,
                "complete": missing == 0,
                "items": items,
            }
        )

    deferred_groups: list[dict[str, Any]] = []
    deferred_min = 0
    deferred_max = 0
    for group in DEFERRED_MODULE_GROUPS:
        directory = repo_root / group["directory"]
        present = len(list(directory.glob("module-*.md"))) if directory.exists() else 0
        missing_min = max(group["expected_min"] - present, 0)
        missing_max = max(group["expected_max"] - present, 0)
        deferred_min += missing_min
        deferred_max += missing_max
        deferred_groups.append(
            {
                "key": group["key"],
                "issue": group["issue"],
                "label": group["label"],
                "directory": group["directory"],
                "present": present,
                "expected_min": group["expected_min"],
                "expected_max": group["expected_max"],
                "missing_min": missing_min,
                "missing_max": missing_max,
            }
        )

    return {
        "active_exact": {
            "total_expected": active_total,
            "present": active_present,
            "missing": active_missing,
            "complete": active_missing == 0,
            "groups": active_groups,
        },
        "deferred": {
            "missing_min": deferred_min,
            "missing_max": deferred_max,
            "groups": deferred_groups,
        },
    }


def build_repo_status(repo_root: Path) -> dict[str, Any]:
    docs_root = repo_root / "src" / "content" / "docs"
    translations = _build_translation_summary(repo_root)
    labs = _build_lab_summary(repo_root)
    missing_modules = _build_missing_modules_summary(repo_root)
    ztt = build_ztt_status(repo_root)

    v2_db = repo_root / ".pipeline" / "v2.db"
    v2 = build_v2_status_report(v2_db) if v2_db.exists() else None
    translation_v2_db = repo_root / ".pipeline" / "translation_v2.db"
    translation_v2 = (
        build_translation_v2_status(repo_root, db_path=translation_v2_db)
        if translation_v2_db.exists()
        else None
    )

    return {
        "repo_root": str(repo_root),
        "english_modules": len(_iter_en_modules(docs_root)),
        "uk_modules_present": len(_iter_uk_modules(docs_root)),
        "v2_pipeline": v2,
        "translation_v2_pipeline": translation_v2,
        "translations": translations,
        "labs": labs,
        "missing_modules": missing_modules,
        "zero_to_terminal": ztt,
        "ownership": {
            "v2_pipeline": "english content write/review/patch",
            "translation": (
                "translation v2 queue + uk_sync worker"
                if translation_v2 is not None
                else "gemini-3.1-pro-preview via uk_sync.py"
            ),
        },
    }


def _print_status(data: dict[str, Any]) -> None:
    v2 = data["v2_pipeline"]
    translation_v2 = data["translation_v2_pipeline"]
    translations = data["translations"]
    labs = data["labs"]
    missing_modules = data["missing_modules"]
    ztt = data["zero_to_terminal"]

    print("KubeDojo Status")
    print()
    print(f"English modules: {data['english_modules']}")
    print(f"Ukrainian module files present: {data['uk_modules_present']}")
    print()
    print("Ownership")
    print(f"  v2 pipeline: {data['ownership']['v2_pipeline']}")
    print(f"  translation: {data['ownership']['translation']}")
    print()

    if v2 is None:
        print("V2 Pipeline")
        print("  status: missing .pipeline/v2.db")
    else:
        print("V2 Pipeline")
        print(f"  total modules: {v2['total_modules']}")
        print(f"  convergence: {v2['convergence_rate']:.1f}%")
        print(
            "  counts:"
            f" review={v2['counts']['pending_review']}"
            f" write={v2['counts']['pending_write']}"
            f" patch={v2['counts']['pending_patch']}"
            f" done={v2['counts']['done']}"
            f" dead_letter={v2['counts']['dead_letter']}"
            f" in_progress={v2['counts']['in_progress']}"
        )
    print()

    if translation_v2 is None:
        print("Translation v2")
        print("  status: missing .pipeline/translation_v2.db")
    else:
        freshness = translation_v2["freshness"]
        queue = translation_v2["queue"]
        print("Translation v2")
        print(
            f"  freshness: synced={freshness['synced']} missing={freshness['missing']}"
            f" stale={freshness['stale']} unknown={freshness['unknown']}"
        )
        print(
            f"  queue: total={queue['total_modules']} convergence={queue['convergence_rate']:.1f}%"
        )
        print(
            f"  counts: review={queue['counts']['pending_review']}"
            f" write={queue['counts']['pending_write']}"
            f" done={queue['counts']['done']}"
            f" dead_letter={queue['counts']['dead_letter']}"
            f" in_progress={queue['counts']['in_progress']}"
        )
    print()

    print("Translations")
    print(
        f"  synced={translations['synced']}"
        f" missing={translations['missing']}"
        f" stale={translations['stale']}"
        f" unknown={translations['unknown']}"
        f" clean={'YES' if translations['sync_clean'] else 'NO'}"
    )
    print()

    print("Labs")
    print(
        f"  tracked={labs['tracked']}"
        f" clean={labs['done_clean']}"
        f" done_nonclean={labs['done_nonclean']}"
        f" pending={labs['pending']}"
    )
    print()

    print("Missing Modules")
    print(
        f"  active exact: present={missing_modules['active_exact']['present']}"
        f" total={missing_modules['active_exact']['total_expected']}"
        f" missing={missing_modules['active_exact']['missing']}"
        f" complete={'YES' if missing_modules['active_exact']['complete'] else 'NO'}"
    )
    print(
        f"  deferred: min={missing_modules['deferred']['missing_min']}"
        f" max={missing_modules['deferred']['missing_max']}"
    )
    print()

    print("Zero to Terminal")
    print(
        f"  english production bar: {'YES' if ztt['ready']['english_production_bar'] else 'NO'}"
    )
    print(
        f"  ukrainian sync clean: {'YES' if ztt['ready']['ukrainian_sync_clean'] else 'NO'}"
    )
    print(
        f"  theory={ztt['theory']['audited']}/{ztt['theory']['present']} audited"
        f" labs={ztt['labs']['clean']}/{ztt['labs']['total']} clean"
        f" uk_synced={ztt['ukrainian']['synced']}/{ztt['ukrainian']['total']}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Show unified KubeDojo repo status")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of human output")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args(argv)

    data = build_repo_status(args.repo_root.resolve())
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        _print_status(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
