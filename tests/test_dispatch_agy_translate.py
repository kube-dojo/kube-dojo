from __future__ import annotations

import sys
from pathlib import Path
from subprocess import CompletedProcess
from types import SimpleNamespace
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import dispatch


_TRANSLATION_BODY = (
    "## Заголовок\n\n"
    "Переклад.\n\n"
    "Додатковий український текст для перевірки мінімальної довжини виводу."
)


def _completed(stdout: str, *, returncode: int = 0) -> CompletedProcess[str]:
    return CompletedProcess(args=["agy"], returncode=returncode, stdout=stdout, stderr="")


def test_dispatch_agy_translate_captures_stdout(monkeypatch: pytest.MonkeyPatch) -> None:
    plan = SimpleNamespace(cmd=["agy", "-p", "prompt"], cwd=Path("."))

    with patch.object(dispatch.AgyAdapter, "build_invocation", return_value=plan) as build_mock, patch(
        "dispatch.subprocess.run", return_value=_completed(_TRANSLATION_BODY)
    ) as run_mock, patch("dispatch._log"):
        ok, output = dispatch.dispatch_agy_translate("translate X")

    assert ok is True
    assert output == _TRANSLATION_BODY
    assert run_mock.call_count == 1

    prompt = build_mock.call_args.kwargs["prompt"]
    assert "printed to stdout" in prompt
    assert "Do NOT write any files" in prompt
    assert "absolute file path" not in prompt
    assert "{out_path}" not in prompt


def test_dispatch_agy_translate_empty_stdout_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    plan = SimpleNamespace(cmd=["agy", "-p", "prompt"], cwd=Path("."))

    with patch.object(dispatch.AgyAdapter, "build_invocation", return_value=plan), patch(
        "dispatch.subprocess.run", return_value=_completed("")
    ), patch("dispatch._log"):
        ok, err = dispatch.dispatch_agy_translate("translate X")

    assert ok is False
    assert err


def test_extract_agy_translation_from_stdout_unwraps_markdown_fence() -> None:
    wrapped = "Here is the translation:\n\n```markdown\n## Title\n\nBody.\n```"
    assert dispatch._extract_agy_translation_from_stdout(wrapped) == "## Title\n\nBody."
