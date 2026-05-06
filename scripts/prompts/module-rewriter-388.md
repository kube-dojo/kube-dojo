# #388 Module Rewriter — Density-First Brief Addendum

This addendum is layered on top of `scripts/prompts/module-writer.md`. It is binding for all #388 site-wide rewrite dispatches. The audit gates here are derived from the Codex architectural consult of 2026-05-01 (bridge messages #3384 and #3386) and the empirical baseline established by the density fix-pass batch of the same session (PRs #720-723).

The brief has historically optimized for visible structure and quotas (DYK count, sections, sources, "600+ content lines"). That conditioning produces choppy single-sentence prose and consistent failure on prose-density gates. This addendum reframes the contract.

## PROSE DENSITY IS A HARD GATE

Body teaching prose must pass all paragraph-density checks before final output:

- mean words per paragraph >= 30
- median words per paragraph >= 28
- short paragraph rate <= 20%, where short means <18 words
- no run of 3 or more consecutive short paragraphs

For this audit, count normal body prose paragraphs. Exclude frontmatter, headings, tables, lists, code fences, YAML, quiz answer blocks, sources, and HTML tags.

If the draft fails any density check, revise the prose before reporting completion.

## PARAGRAPH STYLE

Write body sections as flowing instructional prose, not punchy note blocks. Most body paragraphs should be 3-5 sentences and 35-80 words. Single-sentence paragraphs are allowed only for deliberate emphasis, at most 5 times in the whole module, and never adjacent to another short paragraph.

## NO STACCATO RUNS

Do not create sequences of standalone transition lines, thesis lines, warning lines, or recap lines. If two adjacent paragraphs are under 18 words, merge them into the surrounding explanation unless one is a heading, table row, list item, quiz option, code comment, or source entry.

## SYNTHESIZE COVERAGE BULLETS

The topic coverage bullets in the dispatch brief are inputs, not an outline. Do not create one section or one paragraph per bullet. Combine related bullets into a coherent teaching arc with cause, consequence, tradeoff, and operational decision-making in the same paragraphs.

## STRUCTURE IS SECONDARY TO TEACHING FLOW

Meet the required counts for Did You Know, Common Mistakes, quiz questions, hands-on tasks, and sources, but do not let those counts shape the surrounding prose into checklist writing. The main theory sections must read like a continuous lesson written by an expert instructor.

## PRE-FINALIZATION SCAN

Before finalizing, scan every consecutive body-prose paragraph. If three paragraphs in a row each have fewer than 18 words, the module is invalid. Merge, expand, or rewrite those paragraphs until the maximum consecutive short-paragraph run is 2 or less.

## DEPTH TARGET (REPLACES "600+ CONTENT LINES")

Target substantial depth: 5,000-7,000 words of original instructional content. Do not satisfy depth by adding short lines, fragmented paragraphs, or decorative structure. Word count is the floor; density gates are the ceiling on how those words can be packaged.

## RUNNABILITY, FABRICATION, AND PRACTICE QUESTIONS

Do NOT rely on shell aliases in runnable Bash examples. Specifically: do NOT write `alias k=kubectl` or use `k <subcommand>` (e.g., `k get`, `k describe`) inside fenced ```bash / ```sh / ```shell / ```zsh blocks. Aliases do not expand in non-interactive shells, so a learner who copies the block into a script will see `command not found`. Always use the full `kubectl` binary name in copy-paste examples. Prose like "many engineers alias kubectl to k for interactive use" is fine; running `k <cmd>` in a code block is not.

Do NOT invent business incidents, client stories, anonymized companies, or "war story" anecdotes. A scenario is allowed only if (a) it is clearly labeled hypothetical with a `Hypothetical scenario:` or `Exercise scenario:` prefix, OR (b) it is a sourced real incident with enough specific detail to verify against the cited source. Do not imply an event happened with phrasing like "a payments company once...", "a team I worked with...", "a customer reported...", "War story:..." unless the incident is real and sourced. The incident-dedup gate only catches catalog matches; this rule catches the rest.

For practice-question / mock-exam modules, preserve exam-style MCQ structure. Each question must include four visible answer options labeled `1-4` or `A-D` (visible in the rendered question, NOT hidden in `<details>`), followed by answer reasoning that explains why the correct option is correct AND why each distractor is wrong. The reasoning may live in `<details>` blocks; the numbered options must remain visible.

## VERIFICATION GATES (in addition to module-writer.md structural gates)

All must pass before commit. The deterministic verifier (`scripts/quality/verify_module.py`, to be built as Day 1 of #388) computes these:

1. mean_wpp >= 30
2. median_wpp >= 28
3. short_paragraph_rate <= 20%
4. max_consecutive_short_run <= 2
5. body_words >= 5000 (absolute floor — not relative)
6. mean_sentence_length 12-28 words
7. >= 2 inline active-learning prompts in core content (not just in the final hands-on)
8. Each Learning Outcome maps to >= 1 core section AND >= 1 quiz item OR lab task
9. Quiz answers explain reasoning (not just name the fix)
10. `## Sources` is required as the **last H2** section before `## Next Module`. It must contain at least **10** unique URLs, each in either bare form (`- https://...`) or markdown form (`- [title](https://...)`), and all links must point to primary/vendor docs (not marketing fluff or dead redirects). Verifier counting applies only to links under `## Sources` (it does not count citations elsewhere).

Plus the structural gates from `module-writer.md`: section presence + order, exactly 4 DYK, 6-8 Common Mistakes rows, 6-8 scenario quiz with `<details>`, Hands-On with `- [ ]` checkboxes, no emojis, no number 47, no runnable `kubectl` alias shorthand, no unsourced anecdote framing, K8s 1.35+, no anti-leak tokens.

The deterministic verifier counts links inside the Sources section only — citations elsewhere don't count.

## TIER ROUTING

Per the Codex consult, classify each `revision_pending: true` module into one of four tiers:

- **T0** — passes all gates already. Action: clear the `revision_pending: true` flag. No content change.
- **T1** — fails 1-2 structural gates only (missing section, wrong DYK count, wrong quiz format) but passes density. Action: targeted structural patch. Density and alignment must still pass post-patch.
- **T2** — passes structural but fails density (the failure mode of this session's 8 modules). Action: prose expansion + reflow per the gates above.
- **T3** — fails both density AND structure, OR has body_words < 3000. Action: full rewrite preserving salvageable assets (labs, diagrams, code blocks, source URLs) extracted by the deterministic salvage parser.

## REPORTING

After draft, the dispatched agent must report:
- mean_wpp, median_wpp, short_paragraph_rate, max_consecutive_short_run, body_words, paragraph_count, mean_sentence_length
- Which gates passed/failed
- Body-words-before / body-words-after (and confirmation that absolute floor 5000 is met)
- Salvageable assets preserved (count of code blocks, diagrams, tables before/after)
- Forbidden tokens grep result
- Sources verification status (200/redirect/404 + relevance assessment)

If any gate fails, the agent revises before declaring complete. The orchestrator's verifier re-checks before commit.
