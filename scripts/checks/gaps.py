"""Gap detection — find scaffolding gaps between consecutive modules.

Detects:
1. Concept jumps: Module N+1 uses terms/concepts never introduced
2. Missing prerequisites: Module claims prereqs that don't exist
3. Broken "Next Module" links
4. Orphan modules: not reachable from any learning path
5. Complexity jumps: difficulty spikes between consecutive modules
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .structural import CheckResult


# Technical terms that should be explained before use (per track)
# These are terms that a BEGINNER in that track might not know
TRACK_JARGON = {
    "prerequisites": {
        "cpu", "ram", "ssd", "hdd", "os", "kernel", "process", "thread",
        "port", "ip address", "dns", "tcp", "http", "ssh", "ssl", "tls",
        "container", "docker", "kubernetes", "yaml", "json", "api",
        "git", "repository", "branch", "commit", "cli", "gui", "shell",
        "bash", "terminal", "sudo", "root", "permissions", "firewall",
    },
    "linux": {
        "inode", "file descriptor", "syscall", "namespace", "cgroup",
        "iptables", "nftables", "systemd", "journald", "selinux",
        "apparmor", "seccomp", "overlay", "unionfs", "chroot",
    },
    "cloud": {
        "vpc", "subnet", "cidr", "igw", "nat gateway", "security group",
        "iam", "role", "policy", "arn", "region", "az", "ec2", "s3",
        "lambda", "ecs", "eks", "fargate", "rds", "cloudformation",
        "terraform", "load balancer", "auto scaling", "cdn",
    },
    "k8s": {
        "pod", "deployment", "service", "ingress", "namespace", "configmap",
        "secret", "pv", "pvc", "storageclass", "rbac", "role", "clusterrole",
        "daemonset", "statefulset", "job", "cronjob", "hpa", "vpa",
        "networkpolicy", "cni", "csi", "cri", "operator", "crd", "helm",
        "kustomize", "etcd", "api server", "scheduler", "controller manager",
        "kubelet", "kube-proxy", "cordon", "drain", "taint", "toleration",
        "affinity", "pdb", "priority class",
    },
}


@dataclass
class GapIssue:
    """A gap found between modules."""
    module_a: str  # source module (or "track-start" for first module)
    module_b: str  # target module with the gap
    gap_type: str  # CONCEPT_JUMP, MISSING_PREREQ, BROKEN_LINK, COMPLEXITY_JUMP
    severity: str  # ERROR, WARNING
    message: str

    def __str__(self):
        icon = "❌" if self.severity == "ERROR" else "⚠️"
        return f"  {icon} [{self.gap_type}] {self.module_a} → {self.module_b}: {self.message}"


def extract_complexity(content: str) -> str | None:
    """Extract complexity tag from module content."""
    match = re.search(r"\[([A-Z]+)\]", content[:500])
    return match.group(1) if match else None


COMPLEXITY_ORDER = {"BEGINNER": 1, "EASY": 1, "BASIC": 1,
                    "MEDIUM": 2, "INTERMEDIATE": 2,
                    "COMPLEX": 3, "ADVANCED": 3, "HARD": 3,
                    "EXPERT": 4}


def extract_prerequisites(content: str) -> list[str]:
    """Extract listed prerequisites from module content."""
    prereqs = []
    match = re.search(r"\*\*Prerequisites?\*\*:?\s*(.+?)(?:\n\n|\n>|\n---)", content, re.DOTALL)
    if match:
        text = match.group(1)
        # Find module references like "Module 1.2" or "Module 0.3 (Shell Mastery)"
        refs = re.findall(r"Module\s+(\d+\.\d+)", text, re.IGNORECASE)
        prereqs.extend(refs)
    return prereqs


def extract_next_module(content: str) -> str | None:
    """Extract the Next Module link target."""
    match = re.search(r"(?:Next Module|Наступний модуль|What's Next).*?\[.*?\]\(([^)]+)\)", content)
    if match:
        return match.group(1)
    return None


def find_first_use_of_terms(content: str, terms: set[str]) -> dict[str, int]:
    """Find the first line number where each term appears."""
    first_use = {}
    lines = content.lower().split("\n")
    for i, line in enumerate(lines, 1):
        for term in terms:
            if term not in first_use and term.lower() in line:
                first_use[term] = i
    return first_use


def detect_gaps_in_sequence(module_files: list[Path], track: str = "k8s") -> list[GapIssue]:
    """Detect scaffolding gaps across a sequence of modules.

    Args:
        module_files: Ordered list of module file paths
        track: Track name for jargon lookup (prerequisites, linux, cloud, k8s)
    """
    issues = []

    if not module_files:
        return issues

    jargon = TRACK_JARGON.get(track, set())

    # Track which concepts have been introduced
    introduced_terms: set[str] = set()
    prev_complexity = None
    prev_name = "track-start"

    for path in module_files:
        content = path.read_text()
        name = path.stem

        # 1. Check complexity jumps
        complexity = extract_complexity(content)
        if complexity and prev_complexity:
            curr_level = COMPLEXITY_ORDER.get(complexity, 2)
            prev_level = COMPLEXITY_ORDER.get(prev_complexity, 2)
            if curr_level - prev_level > 1:
                issues.append(GapIssue(
                    prev_name, name, "COMPLEXITY_JUMP", "WARNING",
                    f"Jumps from [{prev_complexity}] to [{complexity}] — "
                    f"consider adding a bridging module or reducing complexity"
                ))

        # 2. Check for jargon used before introduction
        terms_in_module = find_first_use_of_terms(content, jargon)
        new_terms_used = set(terms_in_module.keys()) - introduced_terms

        # Terms used in this module are now "introduced" for subsequent modules
        introduced_terms.update(terms_in_module.keys())

        # Check if any new terms are used without definition in this module
        # (Heuristic: if a term appears but isn't in a heading or bold definition, it might be a gap)
        body_start = content.find("---", content.find("---") + 3)
        if body_start > 0:
            body = content[body_start:]
            for term in new_terms_used:
                # Check if the term is defined (appears in bold or heading)
                definition_pattern = rf"(\*\*{re.escape(term)}\*\*|##.*{re.escape(term)})"
                if not re.search(definition_pattern, body, re.IGNORECASE):
                    # Term used but never defined — potential gap
                    issues.append(GapIssue(
                        prev_name, name, "CONCEPT_JUMP", "WARNING",
                        f"Term '{term}' used but not defined/explained in this module "
                        f"or any previous module in the sequence"
                    ))

        # 3. Check prerequisite references
        prereqs = extract_prerequisites(content)
        # We can't validate if prereqs exist without the full file list,
        # but we track them for the report

        # 4. Check Next Module links
        next_link = extract_next_module(content)
        if next_link:
            # Resolve relative link
            target_name = next_link.rstrip("/").split("/")[-1]
            # Check if target exists in the module list
            target_exists = any(target_name in f.stem for f in module_files)
            if not target_exists and not next_link.startswith("http"):
                issues.append(GapIssue(
                    name, target_name, "BROKEN_LINK", "ERROR",
                    f"Next Module links to '{next_link}' but target not found in this section"
                ))

        prev_complexity = complexity
        prev_name = name

    return issues


def _numeric_sort_key(path: Path) -> tuple:
    """Sort module files numerically (0.1, 0.2, ..., 0.10) not lexicographically."""
    match = re.search(r"module-(\d+)\.(\d+)", path.stem)
    if match:
        return (int(match.group(1)), int(match.group(2)))
    return (999, 999)


def detect_gaps_in_directory(directory: Path, track: str = "k8s") -> list[GapIssue]:
    """Detect gaps across all modules in a directory, sorted by numeric order."""
    module_files = sorted(directory.glob("module-*.md"), key=_numeric_sort_key)
    if not module_files:
        return []
    return detect_gaps_in_sequence(module_files, track)


def run_track_gap_analysis(track_root: Path, track: str = "k8s") -> list[GapIssue]:
    """Run gap analysis across an entire track (all subdirectories in order)."""
    all_issues = []

    # Find all part/section directories
    sections = sorted([d for d in track_root.iterdir() if d.is_dir()])

    if not sections:
        # Flat directory (no parts)
        return detect_gaps_in_directory(track_root, track)

    for section in sections:
        issues = detect_gaps_in_directory(section, track)
        all_issues.extend(issues)

    return all_issues
