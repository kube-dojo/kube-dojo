from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "quality" / "fix_uk_calques.py"


def _load_fix_uk_calques():
    spec = importlib.util.spec_from_file_location("fix_uk_calques_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


fix_uk_calques = _load_fix_uk_calques()


def _fix(text: str) -> str:
    return fix_uk_calques.process_text(text).text


def _flags(text: str) -> list[tuple[int, str, str]]:
    return fix_uk_calques.process_text(text).flags


def test_auto_fix_v_tsilomu() -> None:
    assert _fix("в цілому це працює") == "загалом це працює"


def test_auto_fix_na_protyazi() -> None:
    assert _fix("на протязі дня") == "протягом дня"


def test_auto_fix_po_krayniy_miri() -> None:
    assert _fix("по крайній мірі один раз") == "принаймні один раз"


def test_auto_fix_v_zalezhnosti_vid() -> None:
    assert _fix("в залежності від версії") == "залежно від версії"


def test_auto_fix_u_zalezhnosti_vid() -> None:
    assert _fix("у залежності від модуля") == "залежно від модуля"


def test_auto_fix_po_miri() -> None:
    assert _fix("по мірі зростання") == "у міру зростання"


def test_auto_fix_u_vidpovidnosti_do() -> None:
    assert _fix("у відповідності до політики") == "відповідно до політики"


def test_auto_fix_v_vidpovidnosti_do() -> None:
    assert _fix("в відповідності до документа") == "відповідно до документа"


def test_auto_fix_pryjmaly_uchast() -> None:
    assert _fix("приймати участь у роботі") == "брати участь у роботі"


def test_auto_fix_pryynyaty_uchast() -> None:
    assert _fix("прийняти участь у зустрічі") == "взяти участь у зустрічі"


def test_case_preservation_v_tsilomu() -> None:
    assert _fix("В цілому, це нормально.") == "Загалом, це нормально."


def test_zalezhnist_noun_guard_unchanged() -> None:
    assert _fix("циклічна залежність") == "циклічна залежність"
    assert _fix("залежність від модуля") == "залежність від модуля"


def test_zalezhnist_phrase_is_auto_fixed() -> None:
    assert _fix("в залежності від версії") == "залежно від версії"


def test_rahuvaty_is_flagged_not_auto_edited() -> None:
    text = "Я рахую, що це правильно. Він рахує кроки."
    assert _fix(text) == text
    flagged_tokens = {token for _line, token, _note in _flags(text)}
    assert "рахую" in flagged_tokens
    assert "рахує" in flagged_tokens


def test_calque_in_fenced_code_unchanged() -> None:
    text = """Пояснення.

```bash
echo "в цілому це тест"
```

Після блоку.
"""
    assert _fix(text) == text


def test_calque_in_frontmatter_unchanged() -> None:
    text = """---
title: в цілому огляд
description: на протязі року
---

Тіло без кальків.
"""
    assert _fix(text) == text


def test_calque_in_inline_code_unchanged() -> None:
    text = "Використайте `в цілому` лише як приклад."
    assert _fix(text) == text
