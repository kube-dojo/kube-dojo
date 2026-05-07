from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from ai_agent_bridge import _gemini_session_link


def _session_filename(start_time: datetime, suffix: str) -> str:
    safe = start_time.astimezone(UTC).strftime("%Y-%m-%dT%H-%M-%S.%fZ")
    return f"session-{safe}-{suffix}.json"


def _write_session(
    chats_root: Path,
    *,
    start_time: datetime,
    session_id: str,
    project_name: str,
    messages: list[dict[str, object]],
) -> None:
    chats_dir = chats_root / project_name / "chats"
    chats_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "sessionId": session_id,
        "startTime": start_time.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "messages": messages,
    }
    path = chats_dir / _session_filename(start_time, session_id[-4:])
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_find_session_recovery_prefers_explicit_session_id(tmp_path: Path):
    started_at = datetime.now(UTC)
    _write_session(
        tmp_path,
        start_time=started_at,
        session_id="session-current",
        project_name="kubedojo-session",
        messages=[
            {"type": "user", "content": [{"text": "please handle issue"}]},
            {"type": "gemini", "model": "gemini-2.5-pro", "content": [{"text": "old reply"}]},
        ],
    )
    _write_session(
        tmp_path,
        start_time=started_at,
        session_id="session-reused",
        project_name="kubedojo-session",
        messages=[
            {"type": "user", "content": [{"text": "different brief"}]},
            {"type": "gemini", "model": "gemini-2.5-pro", "content": [{"text": "reused reply"}]},
        ],
    )

    with patch("ai_agent_bridge._gemini_session_link._GEMINI_TMP_ROOT", tmp_path):
        recovery = _gemini_session_link.find_session_recovery(
            delivery_brief="explicitly requesting this should still prefer session id",
            started_at=started_at,
            session_id="session-reused",
            project_name="kubedojo-session",
            chats_root=tmp_path,
        )

    assert recovery is not None
    assert recovery.session_id == "session-reused"
    assert recovery.text == "reused reply"
    assert recovery.model == "gemini-2.5-pro"
