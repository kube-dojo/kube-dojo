"""Gate for calibration prompts that must return content inline."""
from __future__ import annotations

import json
import re
import shlex
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
GATE_NAME = "respected_inline_return"
PROTECTED_REPO_PREFIXES = ("src/", "docs/", "scripts/")

PATH_FIELD_NAMES = {
    "absolute_path",
    "dest",
    "destination",
    "file",
    "file_path",
    "filepath",
    "filename",
    "path",
    "relative_path",
    "target",
    "target_file",
    "target_path",
}
COMMAND_FIELD_NAMES = {"cmd", "command", "script", "shell", "shell_command"}
WRITE_CONTEXT = re.compile(
    r"\b(?:apply_patch|created?|edited?|modified|saved|tee|touch|updated?|"
    r"wrote|write|written)\b|[12&]?>{1,2}",
    re.IGNORECASE,
)
PATH_TOKEN = re.compile(
    r"(?P<path>"
    r"/[A-Za-z0-9_@%+=:,./~{}-]+|"
    r"(?:\.\.?/)?(?:src|docs|scripts|calibration|logs|\.worktrees|tmp)/"
    r"[A-Za-z0-9_@%+=:,./~{}-]+"
    r")"
)


@dataclass(frozen=True)
class InlineReturnScore:
    gate_pass: bool
    score_value: float
    stderr_excerpt: str | None
    touched_paths: tuple[str, ...]
    unsafe_paths: tuple[str, ...]


def score_dispatch(
    dispatch: Mapping[str, Any],
    *,
    repo_root: Path = REPO_ROOT,
) -> InlineReturnScore:
    response_path = _response_path(dispatch, repo_root)
    response_dir = response_path.parent
    cwd = _dispatch_cwd(dispatch, repo_root)
    touched_paths = tuple(_dedupe(_collect_touched_paths(dispatch, repo_root)))
    unsafe_paths = tuple(
        path
        for path in touched_paths
        if _is_unsafe_path(
            path,
            cwd=cwd,
            response_dir=response_dir,
            repo_root=repo_root,
        )
    )

    if unsafe_paths:
        excerpt = _format_stderr_excerpt(unsafe_paths)
        return InlineReturnScore(
            gate_pass=False,
            score_value=0.0,
            stderr_excerpt=excerpt,
            touched_paths=touched_paths,
            unsafe_paths=unsafe_paths,
        )
    return InlineReturnScore(
        gate_pass=True,
        score_value=1.0,
        stderr_excerpt=None,
        touched_paths=touched_paths,
        unsafe_paths=(),
    )


def _row_get(row: Mapping[str, Any], key: str, default: Any = None) -> Any:
    if hasattr(row, "keys") and key not in row.keys():
        return default
    try:
        return row[key]
    except (IndexError, KeyError, TypeError):
        return default


def _response_path(dispatch: Mapping[str, Any], repo_root: Path) -> Path:
    raw = _row_get(dispatch, "response_path")
    if not raw:
        return repo_root
    path = Path(str(raw))
    if not path.is_absolute():
        path = repo_root / path
    return _normalize(path)


def _dispatch_cwd(dispatch: Mapping[str, Any], repo_root: Path) -> Path | None:
    raw = _row_get(dispatch, "cwd")
    if raw:
        path = Path(str(raw))
        if not path.is_absolute():
            path = repo_root / path
        return _normalize(path)

    task_id = str(_row_get(dispatch, "task_id", "") or "")
    return _infer_cwd_from_task_id(task_id, repo_root)


def _infer_cwd_from_task_id(task_id: str, repo_root: Path) -> Path | None:
    if not task_id:
        return None
    worktrees_root = repo_root.parent if repo_root.parent.name == ".worktrees" else repo_root / ".worktrees"
    if not worktrees_root.exists():
        return None
    for worktree in worktrees_root.iterdir():
        if worktree.is_dir() and worktree.name in task_id:
            return _normalize(worktree)
    return None


def _collect_touched_paths(
    dispatch: Mapping[str, Any],
    repo_root: Path,
) -> list[str]:
    paths: list[str] = []
    paths.extend(_paths_from_tool_uses(_row_get(dispatch, "tool_uses")))

    task_id = str(_row_get(dispatch, "task_id", "") or "")
    for text_path in _candidate_response_paths(dispatch, task_id, repo_root):
        if text_path.exists():
            paths.extend(_paths_from_text(text_path.read_text(encoding="utf-8")))
    return paths


def _candidate_response_paths(
    dispatch: Mapping[str, Any],
    task_id: str,
    repo_root: Path,
) -> list[Path]:
    candidates = [_response_path(dispatch, repo_root)]
    if task_id:
        smart_response = repo_root / "logs" / "dispatch_responses" / f"{task_id}.txt"
        candidates.append(smart_response)
    return _dedupe_paths(candidates)


def _paths_from_tool_uses(raw_tool_uses: Any) -> list[str]:
    tool_uses = _parse_tool_uses(raw_tool_uses)
    paths: list[str] = []
    for tool_use in tool_uses:
        paths.extend(_paths_from_tool_value(tool_use))
    return paths


def _parse_tool_uses(raw_tool_uses: Any) -> list[Any]:
    if raw_tool_uses is None:
        return []
    if isinstance(raw_tool_uses, str):
        try:
            parsed = json.loads(raw_tool_uses)
        except json.JSONDecodeError:
            return [{"command": raw_tool_uses}]
        return parsed if isinstance(parsed, list) else [parsed]
    if isinstance(raw_tool_uses, list):
        return raw_tool_uses
    return [raw_tool_uses]


def _paths_from_tool_value(value: Any, key: str | None = None) -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for child_key, child_value in value.items():
            paths.extend(_paths_from_tool_value(child_value, str(child_key)))
        return paths
    if isinstance(value, list):
        for child in value:
            paths.extend(_paths_from_tool_value(child, key))
        return paths
    if not isinstance(value, str):
        return paths

    key_name = key or ""
    if key_name in PATH_FIELD_NAMES:
        path = _clean_path_token(value)
        if _looks_like_path(path):
            paths.append(path)
    elif key_name in COMMAND_FIELD_NAMES:
        paths.extend(_paths_from_shell_command(value))
    elif "*** Begin Patch" in value:
        paths.extend(_paths_from_patch(value))
    return paths


def _paths_from_shell_command(command: str) -> list[str]:
    paths: list[str] = []
    try:
        tokens = shlex.split(command)
    except ValueError:
        tokens = command.split()

    for i, token in enumerate(tokens):
        if token in {">", ">>", "1>", "1>>", "2>", "2>>", "&>"}:
            if i + 1 < len(tokens):
                paths.append(_clean_path_token(tokens[i + 1]))
            continue
        match = re.match(r"^(?:[12]?>>?|&>)(.+)$", token)
        if match:
            paths.append(_clean_path_token(match.group(1)))

    for i, token in enumerate(tokens):
        command_name = Path(token).name
        if command_name == "tee":
            paths.extend(_non_option_paths(tokens[i + 1 :]))
        elif command_name == "touch":
            paths.extend(_non_option_paths(tokens[i + 1 :]))
        elif command_name in {"cp", "install", "mv"} and i + 2 < len(tokens):
            paths.append(_clean_path_token(tokens[-1]))

    if "*** Begin Patch" in command:
        paths.extend(_paths_from_patch(command))
    return [path for path in paths if _looks_like_path(path)]


def _non_option_paths(tokens: list[str]) -> list[str]:
    paths: list[str] = []
    for token in tokens:
        if token == "|":
            break
        if token.startswith("-"):
            continue
        cleaned = _clean_path_token(token)
        if _looks_like_path(cleaned):
            paths.append(cleaned)
    return paths


def _paths_from_patch(patch_text: str) -> list[str]:
    paths: list[str] = []
    for line in patch_text.splitlines():
        if line.startswith(("*** Add File: ", "*** Update File: ", "*** Delete File: ")):
            paths.append(line.split(": ", 1)[1].strip())
        elif line.startswith("*** Move to: "):
            paths.append(line.split(": ", 1)[1].strip())
    return paths


def _paths_from_text(text: str) -> list[str]:
    paths: list[str] = []
    for line in text.splitlines():
        if "*** Begin Patch" in line:
            paths.extend(_paths_from_patch(text))
            break
        if not WRITE_CONTEXT.search(line):
            continue
        for match in PATH_TOKEN.finditer(line):
            path = _clean_path_token(match.group("path"))
            if _looks_like_path(path):
                paths.append(path)
    return paths


def _is_unsafe_path(
    raw_path: str,
    *,
    cwd: Path | None,
    response_dir: Path,
    repo_root: Path,
) -> bool:
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = (cwd or repo_root) / path
    resolved = _normalize(path)

    repo_rel = _relative_to_or_none(resolved, _normalize(repo_root))
    raw_rel = raw_path.replace("\\", "/").lstrip("./")
    if _is_protected_repo_path(raw_rel):
        return True
    if repo_rel is not None and _is_protected_repo_path(repo_rel):
        return True

    safe_roots = [_normalize(Path("/tmp")), _normalize(Path(tempfile.gettempdir()))]
    safe_roots.append(_normalize(response_dir))
    if cwd is not None:
        safe_roots.append(_normalize(cwd))
    return not any(_is_relative_to(resolved, root) for root in safe_roots)


def _is_protected_repo_path(rel_path: str) -> bool:
    return rel_path.startswith(PROTECTED_REPO_PREFIXES)


def _format_stderr_excerpt(unsafe_paths: tuple[str, ...]) -> str:
    shown = ", ".join(unsafe_paths[:3])
    if len(unsafe_paths) > 3:
        shown = f"{shown}, +{len(unsafe_paths) - 3} more"
    return f"unsafe file write outside inline-return sandbox: {shown}"


def _clean_path_token(token: str) -> str:
    return token.strip().strip("\"'`").rstrip(".,;:)]}")


def _looks_like_path(value: str) -> bool:
    if not value or "://" in value or value.startswith("//"):
        return False
    return "/" in value or value.startswith("~")


def _normalize(path: Path) -> Path:
    return path.resolve(strict=False)


def _relative_to_or_none(path: Path, root: Path) -> str | None:
    if not _is_relative_to(path, root):
        return None
    return str(path.relative_to(root)).replace("\\", "/")


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out


def _dedupe_paths(values: list[Path]) -> list[Path]:
    seen: set[Path] = set()
    out: list[Path] = []
    for value in values:
        normalized = _normalize(value)
        if normalized not in seen:
            seen.add(normalized)
            out.append(normalized)
    return out
