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
    ) as run_mock, patch("dispatch._log"):
        ok, err = dispatch.dispatch_agy_translate("translate X", attempts=4)

    assert ok is False
    assert err
    assert run_mock.call_count == 4


def test_dispatch_agy_translate_retries_until_success() -> None:
    plan = SimpleNamespace(cmd=["agy", "-p", "prompt"], cwd=Path("."))
    call_count = 0

    def fake_run(*_args, **_kwargs) -> CompletedProcess[str]:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            return _completed("")
        return _completed(_TRANSLATION_BODY)

    with patch.object(dispatch.AgyAdapter, "build_invocation", return_value=plan), patch(
        "dispatch.subprocess.run", side_effect=fake_run
    ) as run_mock, patch("dispatch._log"):
        ok, output = dispatch.dispatch_agy_translate("translate X", attempts=4)

    assert ok is True
    assert output == _TRANSLATION_BODY
    assert run_mock.call_count == 3


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
    fence_chunk = next(c for c in chunks if "```bash" in c)
    assert "```bash\n# not a heading\n## also not a heading\n```" in fence_chunk
    assert not any(
        c.strip() == "## also not a heading" for c in chunks
    )


def test_split_markdown_respects_max_words_with_paragraph_split() -> None:
    big = _words(900)
    md = f"---\ntitle: X\n---\n\n## Huge\n\n{big}\n\n## Small\n\nTail.\n"
    chunks = dispatch.split_markdown_for_translation(md, max_words=800)
    cap = int(800 * 1.5)
    for chunk in chunks[1:]:
        assert dispatch._markdown_word_count(chunk) <= cap
    assert "".join(chunks) == md


def test_split_markdown_splits_oversized_section_at_paragraphs() -> None:
    big_para1 = _words(1000)
    big_para2 = _words(1000)
    md = (
        "## Huge\n\n"
        f"{big_para1}\n\n"
        "```bash\n"
        "echo hello\n"
        "```\n\n"
        f"{big_para2}\n"
    )
    chunks = dispatch.split_markdown_for_translation(md, max_words=800)
    cap = int(800 * 1.5)
    assert "".join(chunks) == md
    for chunk in chunks:
        assert dispatch._markdown_word_count(chunk) <= cap
    fence_chunks = [c for c in chunks if "```bash" in c]
    assert len(fence_chunks) == 1
    assert "```bash\necho hello\n```" in fence_chunks[0]


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

    def fake_translate(
        prompt: str, *, timeout: int = 600, attempts: int = 4
    ) -> tuple[bool, str]:
        calls.append(prompt)
        return True, prompt.removeprefix(f"{header}\n")

    monkeypatch.setattr(dispatch, "dispatch_agy_translate", fake_translate)
    ok, output = dispatch.dispatch_agy_translate_chunked(
        md, header, timeout=900, attempts=4
    )

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

    def fake_translate(
        prompt: str, *, timeout: int = 600, attempts: int = 4
    ) -> tuple[bool, str]:
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            return False, "boom"
        return True, "ok"

    monkeypatch.setattr(dispatch, "dispatch_agy_translate", fake_translate)
    ok, err = dispatch.dispatch_agy_translate_chunked(
        md, "HDR", timeout=900, attempts=4
    )

    assert ok is False
    assert "chunk 2/" in err
    assert "boom" in err


def test_dispatch_agy_translate_chunked_sleeps_and_passes_kwargs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    md = (
        "---\n"
        "title: Delay\n"
        "---\n"
        "\n"
        "## One\n\n"
        f"{_words(500)}\n\n"
        "## Two\n\n"
        f"{_words(500)}\n"
    )
    sleep_calls: list[float] = []
    translate_kwargs: list[dict[str, int]] = []

    def fake_sleep(delay: float) -> None:
        sleep_calls.append(delay)

    def fake_translate(
        prompt: str, *, timeout: int = 600, attempts: int = 4
    ) -> tuple[bool, str]:
        translate_kwargs.append({"timeout": timeout, "attempts": attempts})
        return True, "ok"

    monkeypatch.setattr(dispatch.time, "sleep", fake_sleep)
    monkeypatch.setattr(dispatch, "dispatch_agy_translate", fake_translate)
    chunks = dispatch.split_markdown_for_translation(md)
    ok, _ = dispatch.dispatch_agy_translate_chunked(
        md, "HDR", timeout=240, attempts=3, delay=2.5
    )

    assert ok is True
    assert sleep_calls == [2.5] * (len(chunks) - 1)
    assert all(k == {"timeout": 240, "attempts": 3} for k in translate_kwargs)
    assert len(translate_kwargs) == len(chunks)
