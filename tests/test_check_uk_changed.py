from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "quality" / "check_uk_changed.py"


def _venv_python() -> Path:
    candidates = [REPO_ROOT / ".venv" / "bin" / "python"]
    if REPO_ROOT.parent.name == ".worktrees":
        candidates.append(REPO_ROOT.parent.parent / ".venv" / "bin" / "python")
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


PYTHON = _venv_python()


def _load_check_uk_changed():
    spec = importlib.util.spec_from_file_location("check_uk_changed_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


check_uk_changed = _load_check_uk_changed()


def _run(paths: list[Path]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(PYTHON), str(SCRIPT)] + [str(path) for path in paths],
        text=True,
        capture_output=True,
        check=False,
    )


def test_check_uk_changed_reports_russicism(tmp_path: Path) -> None:
    path = tmp_path / "module.md"
    path.write_text(
        """# Переклад

Цей текст містить слово вообще, яке є відомим русизмом.
""",
        encoding="utf-8",
    )

    result = _run([path])
    assert result.returncode == 1
    assert "Possible Russicism" in result.stdout
    assert "вообще" in result.stdout


def test_check_uk_changed_reports_russian_only_character_position(tmp_path: Path) -> None:
    path = tmp_path / "module.md"
    path.write_text(
        """# Переклад

Тут є заборонена літера ы.
""",
        encoding="utf-8",
    )

    result = _run([path])
    assert result.returncode == 1
    assert "forbidden Russian-only character" in result.stdout
    assert f"{path}:3:" in result.stdout


def test_check_uk_changed_reports_uppercase_russian_only_character_position(
    tmp_path: Path,
) -> None:
    assert check_uk_changed.RUSSIAN_ONLY_CHARS_RE.search("ЫЁЪЭ") is not None
    path = tmp_path / "module.md"
    path.write_text(
        """# Переклад

Ы тут не має проходити.
""",
        encoding="utf-8",
    )

    result = _run([path])
    assert result.returncode == 1
    assert f"{path}:3:1: forbidden Russian-only character 'Ы'" in result.stdout


def test_check_uk_changed_clean_file_passes(tmp_path: Path) -> None:
    path = tmp_path / "module.md"
    path.write_text(
        """# Переклад

Цей текст виглядає чистим і не має відомих русизмів.
""",
        encoding="utf-8",
    )

    result = _run([path])
    assert result.returncode == 0
    assert result.stdout == ""


def test_zyavlyayetsya_typographic_apostrophe_not_flagged(tmp_path: Path) -> None:
    # «з’являється» (U+2019 apostrophe) is correct Ukrainian ("appears") and must
    # NOT trip the standalone «являється» bureaucratic-calque rule.
    path = tmp_path / "module.md"
    path.write_text(
        """# Переклад

Коли з’являється зв’язок, клієнт синхронізує дані з сервером.
""",
        encoding="utf-8",
    )

    result = _run([path])
    assert result.returncode == 0, result.stdout
    assert "являється" not in result.stdout


def test_normalno_is_contextual_not_a_failure(tmp_path: Path) -> None:
    # «нормально» is standard Ukrainian (VESUM adverb); it is advisory-only and
    # must never hard-fail the gate.
    path = tmp_path / "module.md"
    path.write_text(
        """# Переклад

Ваша версія може відрізнятися, і це нормально. Сервер може працювати нормально.
""",
        encoding="utf-8",
    )

    result = _run([path])
    assert result.returncode == 0, result.stdout


def test_standalone_yavlyayetsya_still_flagged(tmp_path: Path) -> None:
    # The genuine standalone bureaucratic calque «являється» (= "is") must still fail.
    path = tmp_path / "module.md"
    path.write_text(
        """# Переклад

Цей підхід являється найкращим рішенням для команди.
""",
        encoding="utf-8",
    )

    result = _run([path])
    assert result.returncode == 1
    assert "являється" in result.stdout


def test_rahuvaty_counting_not_flagged(tmp_path: Path) -> None:
    # «рахувати» = "to count" (СУМ-11), standard Ukrainian. Only the "consider"
    # calque (conjugated «рахую, що…») is a russicism; the bare infinitive must
    # not hard-fail (#2080).
    path = tmp_path / "module.md"
    path.write_text(
        "# Переклад\n\nПравило змушує планувальник рахувати репліки на домен.\n",
        encoding="utf-8",
    )
    result = _run([path])
    assert result.returncode == 0, result.stdout
    assert "рахувати" not in result.stdout


def test_v_tsilomu_as_a_whole_not_flagged(tmp_path: Path) -> None:
    # «систему в цілому» = "the system as a whole"; r2u lists «у цілому» as an
    # accepted rendering of «в целом». Advisory, not a hard fail (#2080).
    path = tmp_path / "module.md"
    path.write_text(
        "# Переклад\n\nЗрілий дизайн розглядає систему в цілому, а не одну метрику.\n",
        encoding="utf-8",
    )
    result = _run([path])
    assert result.returncode == 0, result.stdout
    assert "в цілому" not in result.stdout


def test_tsej_samyj_this_same_not_flagged(tmp_path: Path) -> None:
    # «цей/ця/ці самий» = "this/these same" — correct Ukrainian, like «той самий».
    path = tmp_path / "module.md"
    path.write_text(
        "# Переклад\n\nЦей самий привілей слід переглядати та обмежувати.\n",
        encoding="utf-8",
    )
    result = _run([path])
    assert result.returncode == 0, result.stdout
    assert "самий" not in result.stdout


def test_bare_superlative_samyj_still_flagged(tmp_path: Path) -> None:
    # The genuine russicism: «самий» + adjective as a superlative intensifier
    # (= "the most …", calque of самый) must still fail — use най-.
    path = tmp_path / "module.md"
    path.write_text(
        "# Переклад\n\nЦе самий кращий варіант для команди.\n",
        encoding="utf-8",
    )
    result = _run([path])
    assert result.returncode == 1
    assert "самий" in result.stdout
