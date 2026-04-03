"""Ukrainian quality checks — Russicism detection, Russian characters, basic grammar."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .structural import CheckResult

# Known Russicisms — ported from learn-ukrainian/scripts/audit/check_plan.py
# Format: {russian_form: "proper_ukrainian (explanation)"}
RUSSICISMS = {
    "хорошо": "добре (well/good)",
    "получати": "отримувати (to receive)",
    "получається": "виходить (it works out)",
    "кушати": "їсти (to eat)",
    "самий": "найкращий or найбільший",
    "зеркало": "дзеркало (mirror)",
    "ковёр": "килим (carpet)",
    "обязательно": "обов'язково (necessarily)",
    "вообще": "взагалі (in general)",
    "луна": "місяць (moon)",
    "сандвіч": "бутерброд (sandwich — calque)",
    "конєчно": "звичайно / звісно (of course)",
    "імєнно": "саме (exactly)",
    "воєнний": "військовий (military)",
    "щас": "зараз (now)",
    "тоже": "також / теж (also)",
    "нада": "потрібно / треба (need to)",
    "всьо": "все (everything)",
    "чо": "що (what)",
    "короче": "коротше / загалом (in short)",
    "тіпа": "типу / наче (like/sort of)",
    "пока": "поки / бувай (bye/while)",
    "нормально": "гаразд / добре (OK/fine) — contextual",
    "відноситися": "стосуватися (to relate to)",
    "в цілому": "загалом (in general)",
    "рахувати": "вважати (to consider) — рахувати is only for counting numbers",
    "приймати участь": "брати участь (to participate)",
    "слідуючий": "наступний (next/following)",
    "любий": "будь-який (any) — любий means 'dear'",
    "являється": "є (is) — являється is bureaucratic Russian calque",
    "остановка": "зупинка (stop)",
    "строїти": "будувати (to build)",
}

# Russian-only characters (never appear in proper Ukrainian)
RUSSIAN_CHARS = {
    "ы": "и (Ukrainian equivalent)",
    "ё": "е or йо (Ukrainian equivalent)",
    "ъ": "remove or use ь (hard sign doesn't exist in Ukrainian)",
    "э": "е (Ukrainian equivalent)",
}


def check_russian_characters(content: str) -> list[CheckResult]:
    """Scan for characters that exist in Russian but not Ukrainian."""
    results = []
    for char, fix in RUSSIAN_CHARS.items():
        occurrences = content.count(char) + content.count(char.upper())
        if occurrences > 0:
            results.append(CheckResult(
                "RUSSIAN_CHAR", False,
                f"Russian character '{char}' found {occurrences} time(s) — fix: {fix}",
            ))

    if not any(r.check == "RUSSIAN_CHAR" for r in results):
        results.append(CheckResult("RUSSIAN_CHAR", True, "No Russian characters found"))

    return results


def check_russicisms(content: str) -> list[CheckResult]:
    """Scan for known Russicisms using word-boundary matching."""
    results = []
    content_lower = content.lower()

    found = []
    for russian, fix in RUSSICISMS.items():
        # Word boundary: surrounded by non-Cyrillic characters
        pattern = rf"(?<![а-яґєіїА-ЯҐЄІЇ']){re.escape(russian.lower())}(?![а-яґєіїА-ЯҐЄІЇ'])"
        matches = re.findall(pattern, content_lower)
        if matches:
            found.append((russian, fix, len(matches)))

    if found:
        for russian, fix, count in found:
            results.append(CheckResult(
                "RUSSICISM", False,
                f"Possible Russicism: '{russian}' ({count}x) — use: {fix}",
            ))
    else:
        results.append(CheckResult("RUSSICISM", True, "No known Russicisms found"))

    return results


def run_all(content: str, path: Path) -> list[CheckResult]:
    """Run all Ukrainian checks."""
    results = []
    results.extend(check_russian_characters(content))
    results.extend(check_russicisms(content))
    return results
