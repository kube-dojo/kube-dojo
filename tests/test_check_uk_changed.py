from __future__ import annotations

import subprocess
import shutil
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "quality" / "check_uk_changed.py"
_PYTHON = REPO_ROOT / ".venv" / "bin" / "python"
if not _PYTHON.exists():
    _PYTHON = Path(shutil.which("python") or "python")
PYTHON = _PYTHON


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
