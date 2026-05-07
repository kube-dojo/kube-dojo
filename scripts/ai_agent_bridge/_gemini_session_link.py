"""Locate Gemini CLI session files and recover the final reply text."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

_GEMINI_TMP_ROOT = Path.home() / ".gemini" / "tmp"
_MAX_DRIFT_SECONDS = 30.0


@dataclass(frozen=True)
class GeminiSessionRecovery:
    """Minimal session payload needed to recover a channel reply."""

    path: Path
    session_id: str
    start_time: datetime | None
    model: str | None
    text: str


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _extract_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        return str(content.get("text", ""))
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if text:
                    parts.append(str(text))
            elif isinstance(item, str):
                parts.append(item)
        return "".join(parts)
    return str(content)


def _brief_match_score(first_user_text: str, delivery_brief: str) -> int:
    """Prefer sessions whose first user prompt contains the delivery brief."""
    user_text = " ".join(first_user_text.lower().split())
    brief = " ".join(delivery_brief.lower().split())
    if not user_text or not brief:
        return 0

    for size, score in ((160, 4), (120, 3), (80, 2), (40, 1)):
        prefix = brief[:size].strip()
        if prefix and prefix in user_text:
            return score
    return 0


def _iter_candidates(
    *,
    delivery_brief: str,
    started_at: datetime | None,
    session_id: str | None,
    project_name: str,
    chats_root: Path | None,
) -> list[tuple[int, float, GeminiSessionRecovery]]:
    root = chats_root or _GEMINI_TMP_ROOT
    chats_dir = root / project_name / "chats"
    if not chats_dir.is_dir():
        return []

    candidates: list[tuple[int, float, GeminiSessionRecovery]] = []
    for path in chats_dir.glob("session-*.json"):
        try:
            data = json.loads(path.read_text("utf-8"))
        except (OSError, json.JSONDecodeError):
            continue

        messages = data.get("messages")
        if not isinstance(messages, list):
            continue

        first_user_text = ""
        last_gemini_text = ""
        last_gemini_model: str | None = None
        for message in messages:
            if not isinstance(message, dict):
                continue
            message_type = str(message.get("type", ""))
            text = _extract_text(message.get("content")).strip()
            if message_type == "user" and text and not first_user_text:
                first_user_text = text
            if message_type == "gemini" and text:
                last_gemini_text = text
                raw_model = message.get("model")
                last_gemini_model = str(raw_model) if raw_model else None

        if not last_gemini_text:
            continue

        candidate_session_id = str(data.get("sessionId", ""))
        candidate_start = _parse_iso(data.get("startTime"))
        session_id_match = bool(session_id and candidate_session_id == session_id)
        drift_s = float("inf")
        if not session_id_match:
            if (
                started_at is None
                or started_at.tzinfo is None
                or candidate_start is None
                or candidate_start.tzinfo is None
            ):
                continue
            drift_s = abs((candidate_start - started_at).total_seconds())
            if drift_s > _MAX_DRIFT_SECONDS:
                continue

        candidates.append(
            (
                100 if session_id_match else _brief_match_score(first_user_text, delivery_brief),
                drift_s,
                GeminiSessionRecovery(
                    path=path,
                    session_id=candidate_session_id,
                    start_time=candidate_start,
                    model=last_gemini_model,
                    text=last_gemini_text,
                ),
            )
        )
    return candidates


def find_session_recovery(
    *,
    delivery_brief: str,
    started_at: datetime | None,
    session_id: str | None = None,
    project_name: str = "learn-ukrainian",
    chats_root: Path | None = None,
) -> GeminiSessionRecovery | None:
    """Return the best matching Gemini session with a non-empty final reply."""
    candidates = _iter_candidates(
        delivery_brief=delivery_brief,
        started_at=started_at,
        session_id=session_id,
        project_name=project_name,
        chats_root=chats_root,
    )
    if not candidates:
        return None

    candidates.sort(
        key=lambda item: (
            -item[0],
            item[1],
            item[2].path.stat().st_mtime if item[2].path.exists() else 0.0,
        ),
        reverse=False,
    )
    best_score = candidates[0][0]
    best_group = [item for item in candidates if item[0] == best_score]
    best_group.sort(
        key=lambda item: (
            item[1],
            -(item[2].path.stat().st_mtime if item[2].path.exists() else 0.0),
        )
    )
    return best_group[0][2]


def format_recovered_reply(recovery: GeminiSessionRecovery, *, fallback_model: str) -> str:
    model = recovery.model or fallback_model
    return f"[source=session-recovery, model={model}]\n\n{recovery.text}"
