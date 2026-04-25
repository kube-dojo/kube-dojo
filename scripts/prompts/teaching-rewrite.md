# KubeDojo Teaching Rewrite

You are rewriting an existing KubeDojo module. The current draft is technically correct but the **prose does not teach** — it pads, lists, or hand-waves. Your job is to rewrite the prose so it actually teaches a working engineer.

This is a **rewrite**, not a fresh write. Preserve the module's scope, ordering, frontmatter, code blocks, tables, callouts, diagrams, quiz, and exercise. Change only the prose between those structural elements.

## What "teaching" means here

Every prose paragraph in the rewrite must do at least one of these things:

1. **Ground a concept in a concrete scenario** — name a tool version, a specific failure mode, a real number, or a named component (e.g. "a 30 GB LLM weight pulling slowly from MinIO" — not "a large model"). Generic statements like "this matters in production" are forbidden.
2. **Reach for an analogy when introducing an unfamiliar abstraction** — the way 1.1 uses GPS for AI ("can drive you into traffic, onto a closed road, or somewhere technically reachable but strategically wrong"). Use the analogy once, then drop back to the technical thing.
3. **Lead with the why, then the what** — the reader should understand why a constraint exists before they read its definition. "Without a memory limit, a runaway training job starves every other pod on the node — so Gatekeeper enforces it at admission time" beats "Gatekeeper enforces memory limits at admission time."
4. **Correct a likely misconception** — what mental model does the typical reader bring that this paragraph corrects? "You might assume scaling to zero is always good for cost — but for a 30 GB model with a 90-second cold start, it makes the first request unusable."

A paragraph that does none of those four is filler. Cut it or rewrite it.

## Forbidden patterns (these are the failure modes we are explicitly fixing)

1. **One-sentence-per-paragraph padding.** Never write a sequence of single-sentence paragraphs separated by blank lines. A paragraph is a 3–6 sentence unit of teaching. If you find yourself writing two short sentences in a row, join them or develop them.
2. **Generic LLM-essay prose.** Sentences like *"In transformer-based architectures, your input acts as a set of initial conditions that bias the model's self-attention mechanism… persona-setting is a way to bias the model toward a specific subset of its weights that represent high-quality professional output rather than generic internet chatter"* are technically-flavored noise. They sound competent and teach nothing. If a sentence could appear unchanged in any AI blog post in any context, delete it.
3. **Bullet lists where prose would teach better.** Bullets are for parallel enumeration of options, trade-offs, or steps. They are not a substitute for the connective reasoning that explains *why* the items belong together. Aim for at most one bullet block per major section, and only when the items are genuinely parallel.
4. **Padding to hit a line count.** The 600-line floor is a *byproduct* of teaching depth, not a target to game. Do not insert blank lines, split sentences, or add hedging clauses to inflate length. A 540-line module that teaches well beats a 720-line module that pads.
5. **Hand-wavy mechanism claims.** If you describe a mechanism ("the scheduler uses node affinity to balance pods across zones"), the next sentence must give a concrete consequence the reader will see ("which is why a single zone outage will cascade if your topologySpreadConstraints have `whenUnsatisfiable: ScheduleAnyway`").

## What to preserve verbatim

- Frontmatter (everything between the `---` fences at the top, including `title`, `slug`, `sidebar.order`)
- All headings and their order
- All fenced code blocks (`` ```yaml ``, `` ```bash ``, `` ```mermaid ``, etc.) — content unchanged
- All tables — content unchanged
- All `:::tip`, `:::caution`, `:::note` callout blocks — content unchanged
- All `<details>` / `<summary>` blocks (quiz answers, lab solutions) — content unchanged
- All `> **Pause and predict:**` / `> **Stop and think:**` blockquote prompts and their answers
- The Quiz section, the Hands-on Exercise section, and the Next Module link — structurally unchanged
- Any `<!-- v4:generated -->` markers — strip these and the content between them; the new rewrite replaces them entirely

## What to rewrite

The connective prose between the structural elements above. Specifically:

- The "Why This Module Matters" narrative
- The lead-in paragraph(s) under each `##` heading
- The interstitial prose between code blocks and tables
- Any short bulleted "definition" lists that should be a paragraph

## Calibration examples from the corpus

**Good — keep this style** (from `ai/foundations/module-1.1-what-is-ai.md`):

> AI is often like a navigation app. It can be extremely useful, faster than your own memory, and good at proposing routes. But if you stop thinking entirely, it can still drive you into traffic, onto a closed road, or somewhere technically reachable but strategically wrong.

Concrete (navigation app), analogical (the GPS frame), corrective (challenges the "AI is always smart" mental model), and ends with a vivid consequence.

**Bad — rewrite this style** (from `ai/foundations/module-1.3-prompting-basics.md` v4 expansion):

> To a practitioner, a prompt is a mechanism for "context steering." In transformer-based architectures, your input acts as a set of initial conditions that bias the model's self-attention mechanism. By providing specific constraints, you are effectively narrowing the probability distribution of the next token from the entire training set down to a specific technical domain.

Plausible-sounding but teaches nothing. No example, no consequence, no misconception corrected. The reader leaves with the same mental model they arrived with, plus three new buzzwords.

**Bad — also rewrite this style** (from `on-premises/ai-ml-infrastructure/module-9.1-gpu-nodes-accelerated.md`):

> Kubernetes would not scale as an open ecosystem if every hardware vendor had to merge device-specific code into the core scheduler or kubelet.
>
> Instead, Kubernetes exposes extension points.
>
> Hardware vendors and platform teams use those extension points to translate host-level hardware into scheduler-visible resources.
>
> For classic GPU scheduling, the most important extension point is the device plugin framework.

Four sentences, four paragraphs, one idea. Should be a single paragraph that develops the idea: *why* the extension-point pattern, *what* the device plugin specifically does, *what consequence* this has for someone debugging a missing GPU.

## Output

Return only the rewritten module as a single Markdown document. No preamble, no postscript, no fenced wrapper around the output. The rewrite should be a drop-in replacement for the input file.

## Module to rewrite

**Path**: `{{MODULE_PATH}}`

```markdown
{{MODULE_CONTENT}}
```
