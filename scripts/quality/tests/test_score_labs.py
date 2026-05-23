from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.quality import score_labs


def test_extract_section_finds_setup_heading_with_prefix() -> None:
    body = """
## Setup

Run these commands.
"""
    assert score_labs._extract_section(body, "Setup", "Prerequisites").strip() == "Run these commands."


def test_extract_section_finds_lab_setup_compound_heading() -> None:
    body = """
## Lab Setup

Use this setup section.
"""
    assert (
        "Use this setup section." in score_labs._extract_section(body, "Setup", "Prerequisites")
    )


def test_extract_section_finds_setup_prerequisites_heading() -> None:
    body = """
## Setup & Prerequisites

Run everything from here.
"""
    assert (
        "Run everything from here."
        in score_labs._extract_section(body, "Setup", "Prerequisites")
    )


def test_extract_section_skips_h1_headings() -> None:
    body = """
# Setup

This section should not match.
"""
    assert score_labs._extract_section(body, "Setup", "Prerequisites") == ""


def test_extract_section_returns_empty_for_empty_body() -> None:
    assert score_labs._extract_section("", "Setup", "Prerequisites") == ""


def test_parse_duration_minutes_integer_minute_duration() -> None:
    assert score_labs._parse_duration_minutes("45 min") == 45


def test_parse_duration_minutes_integer_hour_duration() -> None:
    assert score_labs._parse_duration_minutes("1 hour") == 60


def test_parse_duration_minutes_decimal_hour_duration() -> None:
    assert score_labs._parse_duration_minutes("1.5 hour") == 90


def test_parse_duration_minutes_decimal_minute_duration() -> None:
    parsed = score_labs._parse_duration_minutes("2.5 minutes")
    assert 2 <= parsed < 4


def test_parse_duration_minutes_half_hour_short_unit() -> None:
    assert score_labs._parse_duration_minutes("0.5 hr") == 30


def test_parse_duration_minutes_compound() -> None:
    assert score_labs._parse_duration_minutes("1 hour 15 min") == 75


def test_parse_duration_minutes_empty_input_returns_none() -> None:
    assert score_labs._parse_duration_minutes("") is None


def test_parse_duration_minutes_nonsense_returns_none() -> None:
    assert score_labs._parse_duration_minutes("nonsense") is None
