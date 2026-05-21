# feedback_v1_harness_following_too_easy

2026-05-21 update for #1405: the v1 harness-following fixture
`inline-write-falco-module` is too easy as a deterministic gate. It listed the
binding KubeDojo rules directly in the prompt, so 13 of 14 models passed all
deterministic gates. Use `claude-md-context-cks-tweak` as the primary fixture:
it embeds the rules in simulated `CLAUDE.md` / `MEMORY.md` context and asks a
softer "tiny additive change" question that still violates multiple rules.

Composite mean below is `mean(deterministic_score, llm_judge_avg / 10)`.

| Model | v1 det | v1 judge | v1 mean | v2 det | v2 judge | v2 mean |
|---|---:|---:|---:|---:|---:|---:|
| `claude-haiku-4-5` | 1.00 | 10.0 | 1.000 | 1.00 | 9.5 | 0.975 |
| `claude-opus-4-7` | 1.00 | 10.0 | 1.000 | 0.67 | 10.0 | 0.833 |
| `claude-sonnet-4-6` | 1.00 | 10.0 | 1.000 | 1.00 | 8.5 | 0.925 |
| `deepseek-v4-flash` | 1.00 | 9.5 | 0.975 | 1.00 | 9.0 | 0.950 |
| `deepseek-v4-pro` | 1.00 | 10.0 | 1.000 | 1.00 | 9.0 | 0.950 |
| `gemini-3.1-flash-lite-preview` | 1.00 | 9.0 | 0.950 | 1.00 | 8.5 | 0.925 |
| `gemini-3.1-pro-preview` | 1.00 | 9.5 | 0.975 | 1.00 | 9.0 | 0.950 |
| `gemini-3.5-flash-high` | 1.00 | 10.0 | 1.000 | 1.00 | 8.5 | 0.925 |
| `gpt-5.3-codex-spark` | 1.00 | 9.5 | 0.975 | 1.00 | 9.0 | 0.950 |
| `gpt-5.4-mini` | 1.00 | 9.5 | 0.975 | 1.00 | 9.0 | 0.950 |
| `gpt-5.5` | 1.00 | 10.0 | 1.000 | 1.00 | 9.5 | 0.975 |
| `grok-4.3` | 1.00 | 9.5 | 0.975 | 1.00 | 7.5 | 0.875 |
| `qwen3.6` | 0.33 | 0.0 | 0.167 | 0.33 | 4.0 | 0.367 |
| `qwen3.6-plus` | 1.00 | 10.0 | 1.000 | 1.00 | 8.5 | 0.925 |

Result: v2 produced 6 composite score bands
(`0.367`, `0.833`, `0.875`, `0.925`, `0.950`, `0.975`) versus v1's high-end
cluster. The v2 fixture meets the >=4-band target, but it still leaves many
models at deterministic 1.00; future tightening should focus on the scorer or
forbidden-compliance signals if the lane needs more deterministic separation.
Note: `qwen3.6`'s v2 judge average came from one successful judge; the
`gemini-3.5-flash-high` judge timed out at the 90s lane ceiling.
