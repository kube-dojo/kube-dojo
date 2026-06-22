from __future__ import annotations

import importlib.util
import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "checks" / "uk_calque_v2.py"


def _load_fresh():
    if "uk_calque_v2_test" in sys.modules:
        del sys.modules["uk_calque_v2_test"]
    spec = importlib.util.spec_from_file_location("uk_calque_v2_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _run_main_on_files(files: list[Path]) -> tuple[int, str]:
    uk_calque = _load_fresh()
    buf = io.StringIO()
    argv = [str(f) for f in files]
    with redirect_stdout(buf):
        code = uk_calque.main(argv)
    return code, buf.getvalue()


def test_participle_positive(tmp_path: Path) -> None:
    uk_dir = tmp_path / "src" / "content" / "docs" / "uk" / "part"
    uk_dir.mkdir(parents=True, exist_ok=True)
    p = uk_dir / "test.md"
    p.write_text("На існуючій системі працює.\nКонфліктуючий процес.\n", encoding="utf-8")
    code, out = _run_main_on_files([p])
    assert "[PARTICIPLE/WARN] існуючій" in out
    assert "[PARTICIPLE/WARN] Конфліктуючий" in out
    assert code == 0


def test_znakodytsya_positive(tmp_path: Path) -> None:
    uk_dir = tmp_path / "src" / "content" / "docs" / "uk" / "znak"
    uk_dir.mkdir(parents=True, exist_ok=True)
    p = uk_dir / "test.md"
    p.write_text("Файл знаходиться у директорії.\n", encoding="utf-8")
    code, out = _run_main_on_files([p])
    assert "[ZNAKHODYTSYA/WARN] знаходиться" in out
    assert code == 0


def test_the_following_positive(tmp_path: Path) -> None:
    uk_dir = tmp_path / "src" / "content" / "docs" / "uk" / "follow"
    uk_dir.mkdir(parents=True, exist_ok=True)
    p = uk_dir / "test.md"
    p.write_text("Виконайте наступні команди:\n1. ...\nНаступні три рядки коду:\n", encoding="utf-8")
    code, out = _run_main_on_files([p])
    assert "[THE_FOLLOWING/WARN]" in out
    assert "рядк" in out.lower()
    assert code == 0


def test_duplicate_heading_fail(tmp_path: Path) -> None:
    uk_dir = tmp_path / "src" / "content" / "docs" / "uk" / "dup"
    uk_dir.mkdir(parents=True, exist_ok=True)
    p = uk_dir / "test.md"
    p.write_text("## Вступ\n\nТекст.\n\n## Вступ\n\n", encoding="utf-8")
    code, out = _run_main_on_files([p])
    assert "[DUPLICATE_HEADING/FAIL] ## Вступ" in out
    assert code == 1


def test_mojibake_fail(tmp_path: Path) -> None:
    uk_dir = tmp_path / "src" / "content" / "docs" / "uk" / "moji"
    uk_dir.mkdir(parents=True, exist_ok=True)
    p = uk_dir / "test.md"
    p.write_text("свою酌свою значення\n", encoding="utf-8")
    code, out = _run_main_on_files([p])
    assert "[MOJIBAKE/FAIL]" in out
    assert code == 1


def test_gerund_not_flagged(tmp_path: Path) -> None:
    p = tmp_path / "test.md"
    p.write_text("Виконуючи дію, конфліктуючи з правилами.\nДіючи правильно.\n", encoding="utf-8")
    code, out = _run_main_on_files([p])
    assert "PARTICIPLE" not in out
    assert code == 0


def test_nastupne_pytannya_not_flagged(tmp_path: Path) -> None:
    p = tmp_path / "test.md"
    p.write_text("Наступне питання: як це працює?\nНаступний крок — один.\n", encoding="utf-8")
    code, out = _run_main_on_files([p])
    assert "THE_FOLLOWING" not in out
    assert code == 0


def test_yavlyayetsya_guard_not_flagged(tmp_path: Path) -> None:
    p = tmp_path / "test.md"
    p.write_text("Цей існуючий являється прикладом.\n", encoding="utf-8")
    code, out = _run_main_on_files([p])
    assert "PARTICIPLE" not in out
    assert code == 0


def test_skips_non_uk_files(tmp_path: Path) -> None:
    p = tmp_path / "en.md"
    p.write_text("This is English with знаходиться.\n", encoding="utf-8")
    code, out = _run_main_on_files([p])
    assert out == ""
    assert code == 0


def test_mixed_findings_exit_code(tmp_path: Path) -> None:
    uk_dir = tmp_path / "src" / "content" / "docs" / "uk" / "mix"
    uk_dir.mkdir(parents=True, exist_ok=True)
    p = uk_dir / "uk-test.md"
    p.write_text(
        "## Foo\n\n## Foo\n\n"
        "Наступні команди:\n"
        "свою酌свою\n"
        "файл знаходиться тут.\n",
        encoding="utf-8"
    )
    code, out = _run_main_on_files([p])
    assert "DUPLICATE_HEADING/FAIL" in out
    assert "MOJIBAKE/FAIL" in out
    assert "THE_FOLLOWING/WARN" in out
    assert "ZNAKHODYTSYA/WARN" in out
    assert code == 1


def test_technical_punctuation_not_flagged_as_mojibake(tmp_path: Path) -> None:
    """Legitimate inline punctuation between Cyrillic letters must not FAIL (#2078).

    main already contains 395 such slash-pairs across 167 merged files; the gate
    previously false-positived on every one.
    """
    uk_dir = tmp_path / "src" / "content" / "docs" / "uk" / "punct"
    uk_dir.mkdir(parents=True, exist_ok=True)
    p = uk_dir / "test.md"
    p.write_text(
        "Режим читання/запис у моделі клієнт/сервер.\n"
        "Змінна простір_імен та пара ключ=значення.\n"
        "Збираємо метрик+трейсів і споживання МВт\u00b7год.\n",
        encoding="utf-8",
    )
    code, out = _run_main_on_files([p])
    assert "MOJIBAKE" not in out
    assert code == 0


def test_combining_diacritic_not_flagged_as_mojibake(tmp_path: Path) -> None:
    """Unicode combining stress marks (U+0300-U+036F) are valid, not corruption."""
    uk_dir = tmp_path / "src" / "content" / "docs" / "uk" / "stress"
    uk_dir.mkdir(parents=True, exist_ok=True)
    p = uk_dir / "test.md"
    p.write_text("Ставте найва\u0301жчу роботу на початок.\n", encoding="utf-8")
    code, out = _run_main_on_files([p])
    assert "MOJIBAKE" not in out
    assert code == 0


def test_soft_hyphen_still_flagged(tmp_path: Path) -> None:
    """Invisible soft hyphen (U+00AD) wedged in a word is genuine corruption."""
    uk_dir = tmp_path / "src" / "content" / "docs" / "uk" / "sh"
    uk_dir.mkdir(parents=True, exist_ok=True)
    p = uk_dir / "test.md"
    p.write_text("Складіть одно\u00adсторінкову нотатку.\n", encoding="utf-8")
    code, out = _run_main_on_files([p])
    assert "MOJIBAKE/FAIL" in out
    assert code == 1


def test_zero_width_and_box_drawing_still_flagged(tmp_path: Path) -> None:
    """Zero-width chars and box-drawing wedged in Cyrillic are genuine corruption."""
    uk_dir = tmp_path / "src" / "content" / "docs" / "uk" / "zw"
    uk_dir.mkdir(parents=True, exist_ok=True)
    p = uk_dir / "test.md"
    p.write_text("сло\u200bво та ц\u2502К.\n", encoding="utf-8")
    code, out = _run_main_on_files([p])
    assert "MOJIBAKE/FAIL" in out
    assert code == 1
