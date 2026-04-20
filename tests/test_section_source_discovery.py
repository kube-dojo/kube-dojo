from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path


def _load_module(name: str, relative_path: str):
    module_path = Path(__file__).resolve().parent.parent / relative_path
    spec = importlib.util.spec_from_file_location(name, module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


citation_backfill = _load_module("citation_backfill_test", "scripts/citation_backfill.py")
section_source_discovery = _load_module(
    "section_source_discovery_test",
    "scripts/section_source_discovery.py",
)


def _fake_fetch(url: str, *, refresh: bool = False, timeout: int = 20) -> dict:
    del refresh, timeout
    return {
        "url": url,
        "final_url": url,
        "status": 200,
        "content_type": "text/html",
        "issues": [],
    }


def test_section_source_discovery_writes_pool_and_research_uses_source_ids(monkeypatch) -> None:
    repo_root = Path(citation_backfill.REPO_ROOT)
    tmp_root = repo_root / ".tmp-tests" / "section-source-discovery"
    tmp_pool_dir = tmp_root / "citation-pools"
    tmp_seed_dir = tmp_root / "citation-seeds"
    shutil.rmtree(tmp_root, ignore_errors=True)
    tmp_pool_dir.mkdir(parents=True, exist_ok=True)
    tmp_seed_dir.mkdir(parents=True, exist_ok=True)
    try:
        monkeypatch.setattr(citation_backfill, "CITATION_POOL_DIR", tmp_pool_dir)
        monkeypatch.setattr(citation_backfill, "SEED_DIR", tmp_seed_dir)
        monkeypatch.setattr(section_source_discovery, "fetch", _fake_fetch)
        monkeypatch.setattr(citation_backfill, "fetch", _fake_fetch)

        def fake_discovery_dispatch(prompt: str, *, task_id: str) -> tuple[bool, str]:
            del prompt, task_id
            return True, json.dumps(
                {
                    "section": "platform/toolkits/cicd-delivery/gitops-deployments",
                    "modules": [],
                    "sources": [
                        {
                            "url": "https://argoproj.github.io/argo-cd/",
                            "title": "Argo CD Documentation",
                            "tier": "upstream",
                            "scope_notes": "Argo CD architecture, applications, sync behavior.",
                            "relevant_modules": [
                                "platform/toolkits/cicd-delivery/gitops-deployments/module-2.1-argocd",
                                "platform/toolkits/cicd-delivery/gitops-deployments/module-2.2-argo-rollouts",
                            ],
                        },
                        {
                            "url": "https://fluxcd.io/flux/",
                            "title": "Flux Documentation",
                            "tier": "upstream",
                            "scope_notes": "Flux GitOps reconciliation and controllers.",
                            "relevant_modules": [
                                "platform/toolkits/cicd-delivery/gitops-deployments/module-2.3-flux",
                            ],
                        },
                        {
                            "url": "https://helm.sh/docs/",
                            "title": "Helm Docs",
                            "tier": "upstream",
                            "scope_notes": "Helm chart structure, templating, and commands.",
                            "relevant_modules": [
                                "platform/toolkits/cicd-delivery/gitops-deployments/module-2.4-helm-kustomize",
                            ],
                        },
                    ],
                }
            )

        monkeypatch.setattr(section_source_discovery, "dispatch_codex", fake_discovery_dispatch)

        discovery = section_source_discovery.discover_section_sources(
            "platform/toolkits/cicd-delivery/gitops-deployments"
        )

        assert discovery["ok"] is True
        assert discovery["source_count"] >= 3

        pool_path = repo_root / discovery["pool_path"]
        pool = json.loads(pool_path.read_text(encoding="utf-8"))
        assert len(pool["sources"]) >= 3
        assert all(source["source_id"].startswith("S") for source in pool["sources"])

        def fake_research_dispatch(prompt: str, *, task_id: str) -> tuple[bool, str]:
            del prompt, task_id
            return True, json.dumps(
                {
                    "module_key": "platform/toolkits/cicd-delivery/gitops-deployments/module-2.1-argocd",
                    "module_path": "src/content/docs/platform/toolkits/cicd-delivery/gitops-deployments/module-2.1-argocd.md",
                    "section_pool_ref": discovery["pool_path"],
                    "claims": [
                        {
                            "claim_id": "C001",
                            "claim_text": "ArgoCD watches Git repositories and syncs cluster state.",
                            "claim_class": "vendor_capability",
                            "span_hint": "section: Why This Module Matters",
                            "disposition": "supported",
                            "source_ids": ["S001"],
                            "proposed_url": None,
                            "proposed_tier": None,
                            "anchor_text": None,
                            "suggested_rewrite": None,
                            "lesson_point_url": None,
                            "rationale": "The Argo CD docs cover repository polling and sync.",
                        }
                    ],
                    "further_reading": [
                        {
                            "url": "https://kubernetes.io/docs/concepts/overview/working-with-objects/kubernetes-objects/",
                            "title": "Kubernetes Objects",
                            "tier": "standards",
                            "why_relevant": "Provides the object model Argo CD manages.",
                        }
                    ],
                }
            )

        monkeypatch.setattr(citation_backfill, "dispatch_codex", fake_research_dispatch)

        research = citation_backfill.run_research(
            "platform/toolkits/cicd-delivery/gitops-deployments/module-2.1-argocd",
            section_pool_ref=discovery["pool_path"],
        )

        assert research["ok"] is True
        seed_path = repo_root / research["seed_path"]
        seed = json.loads(seed_path.read_text(encoding="utf-8"))
        assert seed["section_pool_ref"] == discovery["pool_path"]
        assert seed["claims"][0]["source_ids"] == ["S001"]
        assert seed["claims"][0]["proposed_url"] is None
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)


def test_build_research_prompt_omits_pool_block_by_default() -> None:
    module_path = (
        Path(citation_backfill.REPO_ROOT)
        / "src/content/docs/platform/toolkits/cicd-delivery/gitops-deployments/module-2.1-argocd.md"
    )
    prompt = citation_backfill.build_research_prompt(
        "platform/toolkits/cicd-delivery/gitops-deployments/module-2.1-argocd",
        module_path,
        module_path.read_text(encoding="utf-8"),
    )
    assert "## Shared section source pool" not in prompt
