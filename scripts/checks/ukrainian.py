"""Ukrainian quality checks — Russicism detection, Russian characters, basic grammar."""

from __future__ import annotations

import re
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
    "відноситися": "стосуватися (to relate to)",
    "приймати участь": "брати участь (to participate)",
    "слідуючий": "наступний (next/following)",
    "любий": "будь-який (any) — любий means 'dear'",
    "являється": "є (is) — являється is bureaucratic Russian calque",
    "остановка": "зупинка (stop)",
    "строїти": "будувати (to build)",
}

# Standard Ukrainian words that are only *sometimes* register-marked (e.g. as a
# colloquial filler). VESUM-confirmed real words — surfaced as an advisory for
# human review, but NEVER a hard CI failure. Keeps the gate from false-failing
# every translation batch that legitimately uses them.
CONTEXTUAL_RUSSICISMS = {
    "нормально": (
        "standard for 'normally/properly' and «це нормально» (that's fine); "
        "prefer гаразд / добре only as a colloquial 'OK' filler"
    ),
    # СУМ-11 defines рахувати as "to count" (standard). The russicism is the
    # *consider* sense (рахую/рахує, що… = считать), which uses conjugated forms
    # this gate does not match — the bare infinitive is almost always counting.
    # Advisory only, so legit "рахувати репліки/Поди" no longer hard-fails.
    "рахувати": (
        "standard for 'to count' (СУМ-11); only the 'consider that…' sense "
        "(calque of считать, usually conjugated) is a russicism — review in context"
    ),
    # r2u lists «у цілості (у цілому)» as an accepted rendering of «в целом»
    # (the "as a whole" sense). загалом is a stylistic alternative, not a fix.
    "в цілому": (
        "accepted for 'as a whole' (e.g. «систему в цілому»); prefer загалом "
        "only for the 'in general' sense — stylistic, not a correctness failure"
    ),
}

# Word-boundary character class: Ukrainian letters + apostrophe variants. Ukrainian
# joins morphemes with an apostrophe — ASCII ' (U+0027), typographic ’ (U+2019) and
# modifier ʼ (U+02BC) all appear in real text (з’являється, п’ять). Including them
# in the boundary class means a Russicism is matched only as a standalone token, so
# e.g. «являється» inside «з’являється» (correct Ukrainian "appears") is not flagged.
_UA_LETTERS = "а-яґєіїА-ЯҐЄІЇ"
_APOSTROPHES = "'’ʼ"  # ' ’ ʼ
_WORD_CHAR = _UA_LETTERS + _APOSTROPHES

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

    # Context patterns that make a word NOT a Russicism.
    # "самий" after той/та/те/ті etc. means "the same" — correct Ukrainian.
    FALSE_POSITIVE_PATTERNS: dict[str, re.Pattern[str]] = {
        # "той/цей/такий + самий" all mean "the/this/such same" — correct Ukrainian.
        "самий": re.compile(
            r"(?:той|та|те|ті|тій|того|тому|тих|тими|тією|тої"
            r"|цей|ця|ці|цього|цьому|цих|цими|цією|цієї"
            r"|такий|така|такі|такого|такому|таких|такими|такою|такої)"
            r"\s+самий",  # literal token only: aligns 1:1 with the hard detector
            re.IGNORECASE,
        ),
    }

    found = []
    for russian, fix in RUSSICISMS.items():
        # Word boundary: not adjacent to Ukrainian letters or apostrophes, so
        # apostrophe-joined morphemes are treated as a single token.
        pattern = rf"(?<![{_WORD_CHAR}]){re.escape(russian.lower())}(?![{_WORD_CHAR}])"
        matches = re.findall(pattern, content_lower)
        if matches:
            # Subtract false positives from context-aware patterns
            fp_pattern = FALSE_POSITIVE_PATTERNS.get(russian)
            if fp_pattern:
                false_positives = len(fp_pattern.findall(content_lower))
                real_count = len(matches) - false_positives
                if real_count <= 0:
                    continue
                found.append((russian, fix, real_count))
            else:
                found.append((russian, fix, len(matches)))

    if found:
        for russian, fix, count in found:
            results.append(CheckResult(
                "RUSSICISM", False,
                f"Possible Russicism: '{russian}' ({count}x) — use: {fix}",
            ))
    else:
        results.append(CheckResult("RUSSICISM", True, "No known Russicisms found"))

    # Contextual/advisory words — standard Ukrainian that is only register-marked.
    # Surfaced for human review (severity INFO) but never a hard CI failure.
    for russian, note in CONTEXTUAL_RUSSICISMS.items():
        pattern = rf"(?<![{_WORD_CHAR}]){re.escape(russian.lower())}(?![{_WORD_CHAR}])"
        count = len(re.findall(pattern, content_lower))
        if count:
            results.append(CheckResult(
                "RUSSICISM_CONTEXTUAL", True,
                f"Contextual (advisory, not a failure): '{russian}' ({count}x) — {note}",
                severity="INFO",
            ))

    return results


def run_all(content: str, path: Path) -> list[CheckResult]:
    """Run all Ukrainian checks."""
    results = []
    results.extend(check_russian_characters(content))
    results.extend(check_russicisms(content))
    return results
