"""Redact token-shaped secrets before logs, brokers, or GitHub egress."""
from __future__ import annotations

import json
import re
from typing import Any

REDACTION = "[REDACTED_SECRET]"

_SENSITIVE_KEY_RE = re.compile(
    r"(TOKEN|SECRET|PASSWORD|PASSWD|PRIVATE|CREDENTIAL|API[_-]?KEY|"
    r"ACCESS[_-]?KEY|AUTH|COOKIE)",
    re.IGNORECASE,
)

_PRIVATE_KEY_RE = re.compile(
    r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----.*?"
    r"-----END [A-Z0-9 ]*PRIVATE KEY-----",
    re.DOTALL,
)

_ASSIGNMENT_RE = re.compile(
    r"(?i)\b([A-Z0-9_-]*(?:TOKEN|SECRET|PASSWORD|PASSWD|PRIVATE|"
    r"CREDENTIAL|API[_-]?KEY|ACCESS[_-]?KEY|AUTH|COOKIE)[A-Z0-9_-]*)"
    r"\s*([:=])\s*(?:\"[^\r\n\"]*\"|'[^\r\n']*'|[^\s;,]+)"
)

_TOKEN_PATTERNS = (
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bsk-proj-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{20,}\b"),
    re.compile(r"\bhf_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bnpm_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
)


def redact_text(value: Any) -> str:
    """Return ``value`` as text with common secret formats redacted."""
    text = "" if value is None else str(value)
    text = _PRIVATE_KEY_RE.sub(REDACTION, text)
    text = _ASSIGNMENT_RE.sub(lambda m: f"{m.group(1)}{m.group(2)}{REDACTION}", text)
    for pattern in _TOKEN_PATTERNS:
        text = pattern.sub(REDACTION, text)
    return text


def redact_jsonable(value: Any) -> Any:
    """Recursively redact string leaves in JSON-like data structures."""
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [redact_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [redact_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {
            str(key): (
                REDACTION
                if _SENSITIVE_KEY_RE.search(str(key))
                else redact_jsonable(item)
            )
            for key, item in value.items()
        }
    return value


def redact_json_string(value: str) -> str:
    """Redact a JSON string while preserving JSON when possible."""
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return redact_text(value)
    return json.dumps(redact_jsonable(parsed), ensure_ascii=False)
