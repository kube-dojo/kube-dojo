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


def _words(n: int) -> str:
    return " ".join(f"w{i}" for i in range(n))


def test_split_markdown_round_trip_byte_for_byte() -> None:
    md = (
        "---\n"
        "title: Example\n"
        "---\n"
        "\n"
        "Intro paragraph before headings.\n"
        "\n"
        "## Section One\n\n"
        f"{_words(100)}\n\n"
        "## Section Two\n\n"
        f"{_words(200)}\n\n"
        "## Section Three\n\n"
        "Short tail.\n"
    )
    chunks = dispatch.split_markdown_for_translation(md, max_words=150)
    assert "".join(chunks) == md


def test_split_markdown_chunk_zero_holds_frontmatter() -> None:
    md = (
        "---\n"
        "title: Test\n"
        "sidebar:\n"
        "  order: 1\n"
        "---\n"
        "\n"
        "Preamble only.\n"
        "\n"
        "## First\n\n"
        "Body.\n"
    )
    chunks = dispatch.split_markdown_for_translation(md, max_words=800)
    assert chunks[0].startswith("---\n")
    assert "## First" not in chunks[0]
    assert "Preamble only." in chunks[0]


def test_split_markdown_never_splits_inside_fence() -> None:
    md = (
        "## Before\n\n"
        "```bash\n"
        "# not a heading\n"
        "## also not a heading\n"
        "```\n\n"
        "## After\n\n"
        "Done.\n"
    )
    chunks = dispatch.split_markdown_for_translation(md, max_words=5)
    assert "".join(chunks) == md
    before_chunk = next(c for c in chunks if "## Before" in c)
    assert "```bash\n# not a heading\n## also not a heading\n```" in before_chunk
    assert not any(
        c.strip() == "## also not a heading" for c in chunks
    )


def test_split_markdown_respects_max_words_except_oversized_section() -> None:
    big = _words(900)
    md = f"---\ntitle: X\n---\n\n## Huge\n\n{big}\n\n## Small\n\nTail.\n"
    chunks = dispatch.split_markdown_for_translation(md, max_words=800)
    for chunk in chunks[1:-1]:
        assert dispatch._markdown_word_count(chunk) <= 800 or big in chunk
    assert dispatch._markdown_word_count(chunks[-1]) <= 800


def test_dispatch_agy_translate_chunked_echoes_and_concatenates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    md = (
        "---\n"
        "title: Chunked\n"
        "---\n"
        "\n"
        "## One\n\n"
        f"{_words(500)}\n\n"
        "## Two\n\n"
        f"{_words(500)}\n"
    )
    header = "HEADER"
    calls: list[str] = []

    def fake_translate(prompt: str, *, timeout: int = 600) -> tuple[bool, str]:
        calls.append(prompt)
        return True, prompt.removeprefix(f"{header}\n")

    monkeypatch.setattr(dispatch, "dispatch_agy_translate", fake_translate)
    ok, output = dispatch.dispatch_agy_translate_chunked(md, header, timeout=900)

    assert ok is True
    assert len(calls) >= 2
    assert all(call.startswith(f"{header}\n") for call in calls)
    assert output == "\n".join(
        call.removeprefix(f"{header}\n") for call in calls
    )


def test_dispatch_agy_translate_chunked_fails_when_chunk_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    md = (
        "---\n"
        "title: Fail\n"
        "---\n"
        "\n"
        "## One\n\n"
        f"{_words(500)}\n\n"
        "## Two\n\n"
        f"{_words(500)}\n"
    )
    call_count = 0

    def fake_translate(prompt: str, *, timeout: int = 600) -> tuple[bool, str]:
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            return False, "boom"
        return True, "ok"

    monkeypatch.setattr(dispatch, "dispatch_agy_translate", fake_translate)
    ok, err = dispatch.dispatch_agy_translate_chunked(md, "HDR", timeout=900)

    assert ok is False
    assert "chunk 2/" in err
    assert "boom" in err
