"""Canonical calibration model registry for v1.1."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Family = Literal["anthropic", "openai", "google", "deepseek", "alibaba", "xai"]
ProviderCli = Literal["claude-cli", "codex-cli", "agy-cli", "gemini-cli", "hermes"]
EffortMechanism = Literal[
    "native_flag",
    "cli_config",
    "model_name_suffix",
    "prompt_prefix_hint",
    "none",
]
EffortConfidence = Literal["high", "medium", "low", "unknown"]
Wave = Literal["A", "B", "C", "D"]


@dataclass(frozen=True)
class CalibrationModel:
    family: Family
    provider_cli: ProviderCli
    model_id: str
    version: str
    effort_requested: str
    effort_mechanism: EffortMechanism
    effort_confidence: EffortConfidence
    wave: Wave
    canonical_string: str


ANCHORS: tuple[CalibrationModel, ...] = (
    CalibrationModel(
        "anthropic",
        "claude-cli",
        "claude-opus",
        "4-7",
        "max",
        "native_flag",
        "high",
        "A",
        "claude-opus-4-7",
    ),
    CalibrationModel(
        "openai",
        "codex-cli",
        "gpt-5",
        "5.5",
        "xhigh",
        "cli_config",
        "high",
        "A",
        "gpt-5.5",
    ),
    CalibrationModel(
        "google",
        "agy-cli",
        "gemini-3.5-flash",
        "3.5-flash",
        "high",
        "model_name_suffix",
        "high",
        "A",
        "gemini-3.5-flash-high",
    ),
    CalibrationModel(
        "deepseek",
        "hermes",
        "deepseek-v4-pro",
        "v4-pro",
        "xhigh",
        "prompt_prefix_hint",
        "low",
        "A",
        "deepseek-v4-pro",
    ),
    CalibrationModel(
        "alibaba",
        "hermes",
        "qwen3.6-plus",
        "3.6-plus",
        "xhigh",
        "prompt_prefix_hint",
        "low",
        "A",
        "qwen3.6-plus",
    ),
    CalibrationModel(
        "anthropic",
        "claude-cli",
        "claude-sonnet",
        "4-6",
        "max",
        "native_flag",
        "high",
        "B",
        "claude-sonnet-4-6",
    ),
    CalibrationModel(
        "google",
        "gemini-cli",
        "gemini-3.1-pro",
        "3.1-pro-preview",
        "high",
        "model_name_suffix",
        "high",
        "B",
        "gemini-3.1-pro-preview",
    ),
    CalibrationModel(
        "deepseek",
        "hermes",
        "deepseek-v4-flash",
        "v4-flash",
        "xhigh",
        "prompt_prefix_hint",
        "low",
        "B",
        "deepseek-v4-flash",
    ),
    CalibrationModel(
        "xai",
        "hermes",
        "grok",
        "4.3",
        "xhigh",
        "prompt_prefix_hint",
        "unknown",
        "C",
        "grok-4.3",
    ),
    CalibrationModel(
        "anthropic",
        "claude-cli",
        "claude-haiku",
        "4-5",
        "default",
        "none",
        "high",
        "D",
        "claude-haiku-4-5",
    ),
    CalibrationModel(
        "openai",
        "codex-cli",
        "gpt-5-codex-spark",
        "5.3",
        "xhigh",
        "cli_config",
        "medium",
        "D",
        "gpt-5.3-codex-spark",
    ),
    CalibrationModel(
        "openai",
        "codex-cli",
        "gpt-5-mini",
        "5.4",
        "xhigh",
        "cli_config",
        "low",
        "D",
        "gpt-5.4-mini",
    ),
    CalibrationModel(
        "google",
        "agy-cli",
        "gemini-3.1-flash-lite",
        "3.1-flash-lite-preview",
        "high",
        "model_name_suffix",
        "low",
        "D",
        "gemini-3.1-flash-lite-preview",
    ),
    CalibrationModel(
        "alibaba",
        "hermes",
        "qwen3.6",
        "3.6",
        "xhigh",
        "prompt_prefix_hint",
        "low",
        "D",
        "qwen3.6",
    ),
)

LANES = (
    "code-writing",
    "code-review",
    "content-writing-long",
    "content-review",
    "fact-check",
    "architecting",
    "orchestrating",
    "debugging",
    "refactoring",
    "summarization",
)


def models_by_family() -> dict[Family, list[CalibrationModel]]:
    grouped: dict[Family, list[CalibrationModel]] = {}
    for model in ANCHORS:
        grouped.setdefault(model.family, []).append(model)
    return grouped


def model_by_canonical(canonical_string: str) -> CalibrationModel:
    for model in ANCHORS:
        if model.canonical_string == canonical_string:
            return model
    raise KeyError(f"unknown calibration model: {canonical_string}")

