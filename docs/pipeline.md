# Module Quality Pipeline

This document describes the v1 workflow and its numeric rubric. The manual rubric has 8 dimensions, a passing sum of 33/40, and a floor of 4 in every dimension; see [the quality rubric](quality-rubric.md). Current v1 execution uses binary review/check gates, retaining the numeric check for legacy score-bearing state. The workflow and provider examples below are historical descriptions, not current routing instructions.

For the `4/5` and `5/5` upgrade program, **citations are a hard precondition**:
- every war story must have a citation
- important factual claims must be backed by sources
- every upgraded module must include a `## Sources` section
- a module without citations is **not review-passed**, even if the prose is strong

## Quick Start

```bash
# 1. Check for scaffolding gaps in a track (run FIRST)
python scripts/v1_pipeline.py gap-check prerequisites/zero-to-terminal --track prerequisites

# 2. Audit a section (deterministic checks, no LLM cost)
python scripts/v1_pipeline.py audit-all --section prerequisites/zero-to-terminal

# 3. Run a single module through the full pipeline
python scripts/v1_pipeline.py run src/content/docs/prerequisites/zero-to-terminal/module-0.1-what-is-a-computer.md

# 4. Run an entire section
python scripts/v1_pipeline.py run-section prerequisites/zero-to-terminal

# 5. Check progress
python scripts/v1_pipeline.py status

# 6. Resume after interruption
python scripts/v1_pipeline.py resume
```

## Pipeline Steps

```
Existing module → AUDIT+PLAN → WRITE → REVIEW → CHECK → CITE → SCORE → done
                      ↑            ↓        ↓
                      └── rejected ←┘   (max 2 retries)
```

| Step | Who | What | Cost |
|------|-----|------|------|
| **GAP-CHECK** | Python | Detect scaffolding gaps across a track (run once per track) | Free |
| **AUDIT+PLAN** | Claude Opus | Score all 8 dimensions, generate improvement plan | ~$0.10/module |
| **WRITE** | Gemini Pro | Draft improvements based on the plan (full file output) | ~$0.05/module |
| **REVIEW** | Claude Opus | Strict rubric review — approve or reject with feedback | ~$0.10/module |
| **CHECK** | Python | Deterministic quality gates (structure, content, Ukrainian) | Free |
| **CITE** | Python + reviewer | Verify `## Sources`, war-story citations, and evidence hygiene | Free |
| **SCORE** | Python | v1 completion gate: clean binary review, or legacy scores meeting 33/40 with every dimension >= 4 | Free |

If REVIEW rejects, the pipeline loops back to WRITE with the feedback (max 2 retries). If CITE or SCORE fails, the module is also rejected back into manual improvement. If it still fails, the module is flagged for manual intervention.

## Scoring System

8 dimensions, each scored 1-5 (max 40):

| # | Dimension | What a 4 looks like |
|---|-----------|---------------------|
| D1 | Learning Outcomes | Clear, measurable, Bloom's Level 3+ |
| D2 | Scaffolding & Structure | Each section builds on the last, explicit bridges |
| D3 | Active Learning | Multiple inline prompts, scenario quizzes |
| D4 | Real-World Connection | War stories with specific impact, common mistakes table |
| D5 | Assessment Alignment | Tests analysis not recall, explains WHY |
| D6 | Cognitive Load Management | Good chunking, diagrams with text, worked examples |
| D7 | Engagement & Motivation | Conversational tone, strong hook, good analogies |
| D8 | Practitioner Depth | Complexity-scaled: patterns, anti-patterns, decision guidance for higher tiers |

This numeric rubric is distinct from the binary deterministic gates in the
CHECK/CITE steps: those gates pass or fail outright per track, while the
rubric assigns a 1-5 score per dimension. A module must satisfy both.

### Pass criteria (BOTH required)

1. **Every dimension >= 4** — a 3 anywhere is a fail, no matter the sum
2. **Sum >= 33** — all 4s (32) isn't enough; must excel in at least one dimension

```bash
# Score a module manually
.venv/bin/python scripts/score_module.py 4 4 4 4 4 4 4 5          # PASS (33/40)
.venv/bin/python scripts/score_module.py 3 5 5 5 5 5 5 5          # FAIL (floor violated)
.venv/bin/python scripts/score_module.py 4 4 4 4 4 4 4 4          # FAIL (32 < 33)
.venv/bin/python scripts/score_module.py 4 5 4 4 5 4 4 4 --json   # machine-readable output
```

`score_module.py` is a standalone manual scorer; v1 defines its path but does
not invoke it. v4 reads a scalar score and gaps through
`local_api.build_quality_scores`, a separate contract from this eight-score
vector. These documentation changes do not rescore existing modules or change
runtime gates. See `scripts/v1_pipeline.py` (SCORE phase) and
`scripts/pipeline_v4.py` (`_rescore_module`) for those runtime contracts.

## Gap Detection

Run **before** processing modules to find scaffolding problems at the track level:

```bash
python scripts/v1_pipeline.py gap-check prerequisites/zero-to-terminal --track prerequisites
python scripts/v1_pipeline.py gap-check linux --track linux
python scripts/v1_pipeline.py gap-check cloud/aws-essentials --track cloud
python scripts/v1_pipeline.py gap-check k8s/cka --track k8s
```

Detects:
- **CONCEPT_JUMP** — a term used before it's been defined/explained
- **COMPLEXITY_JUMP** — difficulty spike between consecutive modules (e.g., BEGINNER → ADVANCED)
- **BROKEN_LINK** — Next Module points to a nonexistent target

Track types determine the jargon dictionary: `prerequisites`, `linux`, `cloud`, `k8s`.

## Deterministic Checks

The CHECK step runs these without any LLM:

### Structural (`scripts/checks/structural.py`)

| Check | What | Fail condition |
|-------|------|----------------|
| FRONTMATTER | title, sidebar.order | Missing title |
| SECTION_OUTCOMES | Learning Outcomes section exists | Missing |
| SECTION_QUIZ | Quiz section exists | Missing |
| INLINE_PROMPTS | "Pause and predict" / "Stop and think" blockquotes | < 2 found |
| QUIZ_FORMAT | `<details>` tags in quiz | < 4 found |
| LINE_COUNT | Content lines excluding code blocks | < 250 |
| CODE_LANG | Code blocks have language specifier | Any bare ``` found |
| NO_EMOJI | No emoji characters | Any found |
| K8S_API | Deprecated API versions | extensions/v1beta1, apps/v1beta, etc. |

### Citation (`scripts/check_citations.py`)

| Check | What | Fail condition |
|-------|------|----------------|
| SOURCES_SECTION | `## Sources` exists | Missing |
| EXTERNAL_SOURCES | Sources section contains external references | None found |
| WAR_STORY_SOURCE | Each `War Story` block has a nearby `Source:` line | Missing for any war story |
| FOOTNOTE_OR_LINK | Module contains at least one traceable citation marker or link | None found |

### Ukrainian (`scripts/checks/ukrainian.py`)

Only runs on files under `uk/`:

| Check | What | Fail condition |
|-------|------|----------------|
| RUSSIAN_CHAR | Characters ы, ё, ъ, э | Any found |
| RUSSICISM | Dictionary of known Russicisms | Word-boundary match |

The Russicism dictionary includes ~35 common entries (хорошо→добре, получати→отримувати, являється→є, etc.).

## Model Configuration

Default models (chosen for quality):

| Step | Model | Why |
|------|-------|-----|
| AUDIT+PLAN | `claude-opus-4-6` | Nuanced rubric evaluation needs strong reasoning |
| WRITE | `gemini-3.1-pro-preview` | Pro produces better real-world examples and engagement |
| REVIEW | `claude-opus-4-6` | Strict reviewing catches more issues |
| TRANSLATE | `gemini-3.1-pro-preview` | Good Ukrainian + MCP RAG tools for verification |

Override per run:

```bash
python scripts/v1_pipeline.py run module.md --audit-model claude-sonnet-4-6
python scripts/v1_pipeline.py run-section cloud/aws-essentials --write-model gemini-3-flash-preview
```

## State Tracking

Pipeline state is stored in `.pipeline/state.yaml` (gitignored). Each module tracks:

```yaml
modules:
  cloud/aws-essentials/module-1.1-iam:
    phase: done          # pending → audit → write → review → check → score → done
    scores: [4, 4, 4, 4, 4, 4, 4, 5]
    sum: 33
    passes: true
    last_run: "2026-04-03T21:00:00+00:00"
    errors: []
```

The pipeline is **resumable** — if interrupted, `python scripts/v1_pipeline.py resume` picks up from the last successful phase.

## Parallel Processing

For large sections:

```bash
python scripts/v1_pipeline.py run-section cloud/aws-essentials --workers 3
```

State file uses file locking (`fcntl`) to prevent corruption with concurrent workers. Keep workers low (2-3) to avoid rate limits.

## Auto-Commit

When v1's SCORE phase passes, it stages the improved file and any associated
knowledge card or audit record, then attempts a commit. The commit message
records either `all binary checks passed` or `score/40 (legacy rubric)`, plus
the reviewer and any pending-independent-review marker. This automatic commit
is not evidence that independent review or deployment has completed.

This creates a clean git history with one commit per improved module.

## Workflow

### For a new track

```bash
# 1. Gap check — find scaffolding problems
python scripts/v1_pipeline.py gap-check cloud/aws-essentials --track cloud

# 2. Fix any BROKEN_LINK errors manually

# 3. Review CONCEPT_JUMP warnings — decide which need addressing

# 4. Audit — quick deterministic check across all modules
python scripts/v1_pipeline.py audit-all --section cloud/aws-essentials

# 5. Process — run the full pipeline module by module
python scripts/v1_pipeline.py run-section cloud/aws-essentials

# 6. Check status
python scripts/v1_pipeline.py status

# 7. Push when satisfied
git push
```

### For a single module fix

```bash
python scripts/v1_pipeline.py run src/content/docs/k8s/cka/part1-cluster-architecture/module-1.1-control-plane.md
```

## LLM Dispatch

All LLM calls go through `scripts/dispatch.py` which provides:
- **Rate limit detection** — exponential backoff on 429s
- **Inter-call pacing** — 3s minimum between Gemini calls
- **Fallback model** — auto-retry with cheaper model on non-rate-limit failure
- **Structured logging** — every call logged to `.dispatch-logs/`
- **MCP tools** — `--mcp` flag enables RAG tools for Ukrainian (requires learn-ukrainian server on :8766)

```bash
# View recent dispatch logs
python scripts/dispatch.py logs
python scripts/dispatch.py logs -n 20 --full
```

## Files

| File | Purpose |
|------|---------|
| `scripts/v1_pipeline.py` | Main pipeline orchestrator + CLI |
| `scripts/score_module.py` | Scoring tool (33/40 + floor 4) |
| `scripts/dispatch.py` | LLM dispatch (Gemini/Claude) with rate limiting |
| `scripts/checks/structural.py` | Deterministic structure/content checks |
| `scripts/checks/ukrainian.py` | Russicism detection + Russian char scan |
| `scripts/checks/gaps.py` | Scaffolding gap detection across tracks |
| `.pipeline/state.yaml` | Per-module state (gitignored) |
| `.pipeline/audit-report.json` | Latest audit-all results (gitignored) |
| `.mcp.json` | MCP server config for RAG tools |
| `docs/quality-rubric.md` | Full 8-dimension rubric with scoring criteria |
