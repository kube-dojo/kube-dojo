## EXPANSION TASK — existing high-quality but THIN Azure module

You are expanding an EXISTING, already-good KubeDojo module that is below the
5000-word prose floor. Goal: raise it to >= 5000 body words so
`scripts/quality/verify_module.py` reports `body_words_floor_met: true`, by adding
GENUINE teaching depth — never filler, padding, or restated sentences.

### HARD RULES (violating any = NEEDS_CHANGES)
1. PRESERVE all existing correct content: every code block, table, mermaid/ASCII
   diagram, source link, and the existing real-incident references. Do NOT delete,
   shorten, or weaken existing material. You only ADD and DEEPEN.
2. ADD the two standard sections this module is missing (required for [MEDIUM]+ by
   the module-writer standard, currently absent):
   - **Patterns & Anti-Patterns** — >=3 proven patterns (when to use, why it works,
     scaling note) and >=3 anti-patterns (what goes wrong, why teams fall into it,
     better alternative). Table or structured form.
   - **Decision Framework** — a decision matrix or mermaid flowchart for choosing
     between the key options the module covers, with tradeoffs. (If the module
     already has one, DEEPEN it rather than duplicate.)
3. DEEPEN 2-3 existing core sections with substantive, accurate, NEW material
   (see the per-module list below). Prose must explain WHY before HOW.
4. COST LENS: ensure the cost dimension is covered (what it costs at moderate
   scale, which knobs reduce cost, what makes cost spike unexpectedly).
5. ANTI-FABRICATION: do NOT invent incidents/anecdotes. Do NOT introduce any NEW
   named real-world incident (a CI incident-dedup gate blocks reusing a named
   incident across modules). Any illustrative story MUST start with
   `Hypothetical scenario:`. Keep the module's existing incident references
   exactly as they are.
   **OPENER RULE**: the "Why This Module Matters" opener must NOT be a specific
   dated/$-quantified/company-shaped incident unless real AND cited; default to
   `Hypothetical scenario:` or generic stakes.
6. WEB-VERIFY every NEW factual claim (service limits, IOPS/throughput numbers,
   pricing rates, API names, `az` CLI flags, SKU names, GA/Preview status)
   against official **learn.microsoft.com** (or azure.microsoft.com/pricing) docs
   before writing it. If you cite a new page, add it to the Sources list. Reach
   >= 10 reachable learn.microsoft.com / azure.microsoft.com docs links. Use
   CURRENT facts (2026); do not invent quotas — if unsure of an exact number,
   describe the behavior without a fabricated figure.
   **Azure-specific `az` gotchas to get right**: role assignment is
   `az role assignment create --assignee <id> --role "<RoleName>" --scope <id>`;
   managed identity is `az identity create` (user-assigned) vs system-assigned via
   `--assign-identity`; resource groups precede most resources
   (`az group create -n <rg> -l <region>`); the current standard Kubernetes
   version for this curriculum is 1.35 (never flag 1.35 as future/invalid).
7. KEEP all structure gates intact:
   - Did You Know? = EXACTLY 4 facts.
   - Common Mistakes = 6-8 table rows.
   - Quiz = 6-8 questions in `<details><summary>...</summary>...</details>`, >=4
     scenario-based, answers 3-5 sentences explaining WHY. (Do NOT add more than 8.)
   - Hands-On Exercise with `- [ ]` success-criteria checkboxes.
   - Next Module link present.
   - NO source `# H1` heading after the frontmatter (Starlight renders the title
     from frontmatter; a `# ...` line trips the gate).
   - If the frontmatter has a `revision_pending: true` line, REMOVE it.
8. DENSITY: write full teaching paragraphs (median words-per-paragraph >= 28,
   mean >= 30, short-paragraph-rate <= 20%). Do not expand by adding bullet
   fragments or one-line paragraphs. Watch the `sentence_length_12_28` gate:
   keep mean sentence length in the 12-28 word band (several modules fail this by
   running long, comma-spliced sentences — break them up).

### CODE-FENCE HYGIENE (verifier + render gates)
- Never fuse a language onto the opening fence text (e.g. ` ```bashaz` is
  WRONG — it must be ` ```bash` on its own line, command on the next line).
- Use ` ```yaml` for manifests, ` ```bash` for shell, ` ```text`/` ```json` for
  display-only output.

### OUTPUT
Edit the target file IN PLACE. Then run, in the worktree:
  git add -A && git commit -m "chore(content): expand <MODULE> to 5000w floor (cloud Azure wave)"
Report the final `verify_module.py` body_words number for the file.
