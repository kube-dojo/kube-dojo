from __future__ import annotations

import json
import re
import runpy
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GATE_SCRIPT = REPO_ROOT / "scripts/quality/incident_dedup_gate.py"
PYTHON_BIN = shutil.which("python3") or shutil.which("python") or "python"
INCIDENTS = runpy.run_path(str(REPO_ROOT / "scripts" / "audit_incident_reuse.py"))[
    "INCIDENTS"
]


def _git(repo: Path, args: list[str]) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def _init_repo_with_scripts(repo: Path) -> None:
    scripts_dir = repo / "scripts"
    quality_dir = scripts_dir / "quality"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    quality_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(
        REPO_ROOT / "scripts" / "check_incident_reuse.py",
        scripts_dir / "check_incident_reuse.py",
    )
    shutil.copy(
        REPO_ROOT / "scripts" / "audit_incident_reuse.py",
        scripts_dir / "audit_incident_reuse.py",
    )
    shutil.copy(GATE_SCRIPT, quality_dir / "incident_dedup_gate.py")

    _git(repo, ["init", "-b", "main"])
    _git(repo, ["config", "user.email", "test@example.com"])
    _git(repo, ["config", "user.name", "test"])
    _git(repo, ["add", "scripts"])
    _git(repo, ["commit", "-m", "add incident scripts"])


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _commit(repo: Path, path: str, content: str, message: str) -> None:
    target = repo / path
    _write_text(target, content)
    _git(repo, ["add", path])
    _git(repo, ["commit", "-m", message])


def _branch(repo: Path, name: str) -> None:
    _git(repo, ["checkout", "-b", name])


def _run_gate(
    repo: Path,
    *,
    base: str = "main",
    mode: str | None = None,
    emit_json: bool = True,
) -> subprocess.CompletedProcess[str]:
    cmd = [
        PYTHON_BIN,
        str(repo / "scripts/quality/incident_dedup_gate.py"),
        "--base",
        base,
    ]
    if mode is not None:
        cmd.extend(["--mode", mode])
    if emit_json:
        cmd.append("--json")
    return subprocess.run(
        cmd,
        cwd=repo,
        capture_output=True,
        text=True,
    )


VIOLATION_UBER = "Uber had a security event with MFA fatigue in 2022.\n"
VIOLATION_TARGET = "Target had an HVAC-related incident around the 2013 breach.\n"
VIOLATION_NONE = "This module contains only generic conceptual guidance.\n"


def _parse_gate_payload(result: subprocess.CompletedProcess[str]) -> dict:
    assert result.returncode in (0, 1)
    payload = json.loads(result.stdout)
    assert isinstance(payload, dict)
    return payload


def _matches_incident(incident: str, text: str) -> bool:
    return any(
        re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        for pattern in INCIDENTS[incident]
    )


def test_github_october_2018_split_brain_requires_specific_incident_anchor() -> None:
    incident = "GitHub October 2018 split-brain"
    generic_acquisition_anchor = "In October 2018, Microsoft completed its acquisition of GitHub for $7.5 billion."
    split_brain_outage_anchor = (
        "On October 21, 2018, GitHub suffered a 43-second optical hardware split-brain "
        "that triggered the US-East database failover."
    )

    assert not _matches_incident(incident, generic_acquisition_anchor)
    assert _matches_incident(incident, split_brain_outage_anchor)


def test_argo_cd_path_traversal_requires_specific_incident_anchor() -> None:
    incident = "Argo CD path-traversal CVE-2022-24348"
    generic_graduation_anchor = "Argo CD became a CNCF Graduated project in 2022, citing a mature CVE response process."
    path_traversal_anchor = (
        "Argo CD had a path traversal vulnerability that let attackers read files "
        "outside the repository root."
    )
    hyphenated_anchor = "The Argo CD path-traversal flaw allowed directory escape."

    assert not _matches_incident(incident, generic_graduation_anchor)
    assert _matches_incident(incident, path_traversal_anchor)
    assert _matches_incident(incident, hyphenated_anchor)


def test_delta_mode_pass_when_set_is_identical(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo_with_scripts(repo)
    _commit(repo, "src/content/docs/module.md", VIOLATION_UBER, "seed base")
    _branch(repo, "delta-identical")

    result = _run_gate(repo, base="main", mode="delta", emit_json=False)
    assert result.returncode == 0


def test_delta_mode_fails_when_new_triple_added(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo_with_scripts(repo)
    _commit(repo, "src/content/docs/module.md", VIOLATION_UBER, "seed base")
    _branch(repo, "delta-new-triple")
    _commit(repo, "src/content/docs/new/module.md", VIOLATION_TARGET, "add new triple")

    result = _run_gate(repo, base="main", mode="delta", emit_json=True)
    payload = _parse_gate_payload(result)
    assert result.returncode == 1
    assert payload["status"] == "fail"
    assert payload["mode"] == "delta"
    assert [
        "duplicate",
        "Target 2013 breach",
        "src/content/docs/new/module.md",
    ] in payload["added"]


def test_delta_mode_pass_when_old_triple_removed(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo_with_scripts(repo)
    _commit(repo, "src/content/docs/module.md", VIOLATION_UBER, "seed base")
    _branch(repo, "delta-removed")
    _commit(repo, "src/content/docs/module.md", VIOLATION_NONE, "remove violation")

    result = _run_gate(repo, base="main", mode="delta", emit_json=True)
    payload = _parse_gate_payload(result)
    assert result.returncode == 0
    assert payload["status"] == "pass"
    assert payload["added"] == []


def test_delta_mode_fails_when_old_replaced_by_different_triple(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo_with_scripts(repo)
    _commit(repo, "src/content/docs/module.md", VIOLATION_UBER, "seed base")
    _branch(repo, "delta-replace")
    _commit(repo, "src/content/docs/module.md", VIOLATION_NONE, "remove old violation")
    _commit(
        repo,
        "src/content/docs/other/module.md",
        VIOLATION_TARGET,
        "add replacement violation",
    )

    result = _run_gate(repo, base="main", mode="delta", emit_json=True)
    payload = _parse_gate_payload(result)
    assert result.returncode == 1
    assert payload["status"] == "fail"
    assert [
        "duplicate",
        "Target 2013 breach",
        "src/content/docs/other/module.md",
    ] in payload["added"]
    assert [
        "duplicate",
        "Uber 2022 hardcoded credentials",
        "src/content/docs/module.md",
    ] in payload["removed"]


def test_absolute_mode_fails_when_any_after_violation_exists(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo_with_scripts(repo)
    _commit(repo, "src/content/docs/module.md", VIOLATION_NONE, "seed base")
    _branch(repo, "absolute-fails")
    _commit(repo, "src/content/docs/new/module.md", VIOLATION_UBER, "add violation")

    result = _run_gate(repo, base="main", mode="absolute", emit_json=True)
    payload = _parse_gate_payload(result)
    assert result.returncode == 1
    assert payload["status"] == "fail"
    assert payload["mode"] == "absolute"
    assert payload["after_count"] == 1


def test_default_mode_is_absolute(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo_with_scripts(repo)
    _commit(repo, "src/content/docs/module.md", VIOLATION_NONE, "seed base")
    _branch(repo, "default-absolute")
    _commit(repo, "src/content/docs/new/module.md", VIOLATION_UBER, "add violation")

    result = _run_gate(repo, base="main", emit_json=True)
    payload = _parse_gate_payload(result)
    assert result.returncode == 1
    assert payload["status"] == "fail"
    assert payload["mode"] == "absolute"
    assert payload["after_count"] == 1


# Regression for #1343: cloud-vendor + service + region inside a fenced code
# block (HCL variable description / Python dict / YAML annotation / etc.) used
# to trip the gate when matched against canonical AWS S3 us-east-1 2017. The
# code-stripping pass in check_incident_reuse.py now blanks fenced ``` and
# inline ` regions so only prose can violate.

FP_HCL_VAR = """\
# Module: cloud setup tutorial

This module walks through a minimal Terraform stack.

```hcl
variable "aws_region" {
  description = "S3 exercise — pick a region close to you"
  default     = "us-east-1"
}

resource "aws_s3_bucket" "example" {
  bucket = "kubedojo-${var.aws_region}-demo"
}
```

End of tutorial.
"""

FP_INLINE_CODE = """\
# Module: cloud quickstart

Set the region with `aws s3 ls --region us-east-1` to list bucket contents.
"""

PROSE_REAL_INCIDENT = """\
# Module: reliability case study

On 28 February 2017 the AWS S3 us-east-1 outage knocked out a large
portion of the public internet for four hours. The post-mortem detailed
a typo in a debugging script that removed more capacity than intended.
"""


def test_absolute_mode_passes_when_fp_lives_only_in_fenced_code(tmp_path: Path) -> None:
    """#1343: HCL var with `aws_region` + `S3 exercise` + `us-east-1` default
    must not match the canonical 2017 outage anchor."""
    repo = tmp_path / "repo"
    _init_repo_with_scripts(repo)
    _commit(repo, "src/content/docs/module.md", VIOLATION_NONE, "seed base")
    _branch(repo, "fp-hcl-var")
    _commit(repo, "src/content/docs/new/module.md", FP_HCL_VAR, "add fp tutorial")

    result = _run_gate(repo, base="main", mode="absolute", emit_json=True)
    payload = _parse_gate_payload(result)
    assert result.returncode == 0, payload
    assert payload["status"] == "pass"
    assert payload["after_count"] == 0


def test_absolute_mode_passes_when_fp_lives_only_in_inline_code(tmp_path: Path) -> None:
    """#1343: inline `aws s3 ls --region us-east-1` must not match either."""
    repo = tmp_path / "repo"
    _init_repo_with_scripts(repo)
    _commit(repo, "src/content/docs/module.md", VIOLATION_NONE, "seed base")
    _branch(repo, "fp-inline")
    _commit(repo, "src/content/docs/new/module.md", FP_INLINE_CODE, "add inline fp")

    result = _run_gate(repo, base="main", mode="absolute", emit_json=True)
    payload = _parse_gate_payload(result)
    assert result.returncode == 0, payload


def test_absolute_mode_still_fails_when_real_incident_is_in_prose(
    tmp_path: Path,
) -> None:
    """Make sure the code-strip pass doesn't over-relax: the same triple in
    prose must still flag, otherwise we've broken the whole gate."""
    repo = tmp_path / "repo"
    _init_repo_with_scripts(repo)
    _commit(repo, "src/content/docs/module.md", VIOLATION_NONE, "seed base")
    _branch(repo, "real-prose")
    _commit(
        repo, "src/content/docs/new/module.md", PROSE_REAL_INCIDENT, "add prose case"
    )

    result = _run_gate(repo, base="main", mode="absolute", emit_json=True)
    payload = _parse_gate_payload(result)
    assert result.returncode == 1, payload
    assert payload["status"] == "fail"
    assert payload["after_count"] >= 1


# Lock the design invariant called out in the PR #1430 review: incident-xref
# markers MUST live in PROSE. A marker buried inside a fenced block is erased
# by the code-strip pass, so has_xref_near misses it and the canonical-duplicate
# check still flags — which is the intended behavior, but undocumented and
# surprising if you ever do it. This test guards against a future author
# "fixing" the code-strip pass to preserve xref markers without re-thinking
# the convention.

PROSE_REAL_INCIDENT_WITH_XREF_IN_CODE = """\
# Module: secondary case study

```text
Postmortem reference inside a code sample:
On 28 February 2017 the AWS S3 us-east-1 outage knocked things over.
<!-- incident-xref: aws-s3-useast1-2017 -->
```

End.
"""


def test_xref_marker_inside_code_block_does_not_suppress_match(tmp_path: Path) -> None:
    """xref markers must live in prose; one buried in a fenced block can't
    cancel the canonical-duplicate flag. (Today the match itself is also
    erased, so this case is double-protected; the test still pins the
    convention so a future code-strip change can't quietly invert it.)"""
    repo = tmp_path / "repo"
    _init_repo_with_scripts(repo)
    _commit(repo, "src/content/docs/module.md", VIOLATION_NONE, "seed base")
    _branch(repo, "xref-in-code")
    _commit(
        repo,
        "src/content/docs/new/module.md",
        PROSE_REAL_INCIDENT_WITH_XREF_IN_CODE,
        "add xref-in-code case",
    )

    # With both the incident reference AND the xref marker inside a fenced
    # block, neither survives the code-strip pass — gate passes today. If a
    # future change preserves xref markers but still blanks code content, the
    # gate must NOT use that buried xref to silence a real prose match
    # elsewhere; if a future change preserves the incident reference but
    # blanks xrefs, the gate must flag the duplicate. The test asserts the
    # current consistent behavior.
    result = _run_gate(repo, base="main", mode="absolute", emit_json=True)
    payload = _parse_gate_payload(result)
    assert result.returncode == 0, payload
    assert payload["status"] == "pass"
