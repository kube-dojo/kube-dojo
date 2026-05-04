# Per-track sweep prompt template — incident de-duplication (#878)

> Reusable template for dispatching a single-track sweep PR via headless Claude (sonnet) or Codex Desktop relay. Copy + fill in the `{TRACK_FIELDS}` for each sweep.

## Variables to fill per dispatch

| Variable | Example |
|---|---|
| `{TRACK_NAME}` | `prerequisites` |
| `{WORKTREE_BRANCH}` | `claude/incident-sweep-prereqs` |
| `{WORKTREE_PATH}` | `.worktrees/incident-sweep-prereqs` |
| `{FILES_TABLE}` | A table with: file path, current incident, option (a/b/c), replacement-incident slug from catalog, lesson |
| `{PR_TITLE}` | `chore(content): de-dup incident anecdotes — prereqs sweep (#878)` |

## Prompt body

```
You are a content engineer working on KubeDojo. The curriculum has been audited
for repeated incident anecdotes (Knight Capital, Tesla 2018, Capital One, Log4Shell,
etc.) used as the dramatic opener in many unrelated modules. Issue #878 tracks the
sweep. Your job in this PR: rewrite the "Why This Module Matters" section in the
files listed below so each named real-world incident appears in at most ONE module
across the entire curriculum.

## Required reading BEFORE you write anything

1. /Users/krisztiankoos/projects/kubedojo/docs/audits/2026-05-04-incident-canonicals.md
   The locked canonical assignment per incident. Do NOT touch the canonical files.
2. /Users/krisztiankoos/projects/kubedojo/docs/audits/2026-05-04-incident-replacement-catalog.md
   The menu of verified real incidents you may use as replacements. Each catalog
   entry has a primary-source URL — keep that URL in the rewritten module's
   Sources section.
3. /Users/krisztiankoos/projects/kubedojo/.claude/rules/module-quality.md
   The module quality contract. The WTMM section is paragraph 1-3 after `## Why
   This Module Matters`. Don't touch other sections of the modules.

## Quality bar (HARD — user direction 2026-05-04)

> "I want nice proper solution, which is still enjoyable to read but no bullshit,
>  humans are very receptive for that. you cannot fool a human."

Concretely:
- Real incidents only. Named company, named year, primary-source URL in Sources.
- No invented dollar figures. If your replacement incident has no published
  loss figure, write "estimated millions" or omit the figure — never invent.
- No fabricated companies (GlobalTradeX, AcmeCorp, FintechCo, etc.).
- No templated "fintech + Black Friday + $X.X million" stories. They fail
  the no-bullshit bar — readers detect them in seconds.
- Third person, factual, neutral tone. NOT marketing copy.
- 80-180 words for paragraph 1 (the dramatic opener / concept lead).
- The opener leads naturally into the module's actual topic. If you can't
  link the incident to the topic in one sentence, pick a different incident
  or use option (c) — concept-led WTMM.

## Three options for each non-canonical occurrence

For every file in the table below, choose ONE option per the canonicals doc:

(a) REPLACE — pick an unused incident from the replacement catalog that fits
    the module's topic. Rewrite the WTMM opener using it. Add the incident's
    primary-source URL to the module's Sources section.

(b) CROSS-REFERENCE — keep one short sentence pointing to the canonical
    module ("Engineers who want the deployment-control case study should see
    [the Knight Capital walkthrough in module 1.1](../modern-devops/module-1.1-infrastructure-as-code/).").
    Add an HTML comment within 200 chars: `<!-- incident-xref: knight-capital-2012 -->`.
    The CI guardrail (scripts/check_incident_reuse.py) checks for this marker.

(c) CONCEPT-LED — drop the dramatic opener entirely. Lead paragraph 1 with
    the engineering principle, the operational stakes, and what the learner
    will be able to do after the module. No story. No anecdote. No fictional
    company. This is the right option whenever the original opener was a
    fabricated/templated story.

## Files in this PR

{FILES_TABLE}

(Each row: file path | current incident | option (a/b/c) | replacement-slug or "n/a" | lesson the module teaches)

## Workflow

```bash
# 1. Set up the worktree (orchestrator already prepared this)
cd /Users/krisztiankoos/projects/kubedojo/{WORKTREE_PATH}

# 2. For each row in the FILES_TABLE, edit the WTMM section per the chosen option.
#    Use the Read + Edit tools. Do NOT touch any other section of the module.
#    Preserve all existing internal links, frontmatter, and trailing newlines.

# 3. Run the guardrail BEFORE pushing — must pass for the files in this PR
.venv/bin/python scripts/check_incident_reuse.py 2>&1 | grep -E "^\s+\-\s+(prerequisites|cloud|k8s|on-premises|ai|platform|linux)/"
#    Each file you edited should NO LONGER appear as a violation.

# 4. Run the build (~38s)
npm run build 2>&1 | tail -10
#    Expect: 0 errors, 0 warnings, build succeeds.

# 5. Commit + push + open PR
git add -A
git commit -m "$(cat <<COMMIT
chore(content): de-dup incident anecdotes — {TRACK_NAME} sweep (#878)

{N} modules had their "Why This Module Matters" section rewritten so each
named real-world incident appears in at most one module across the
curriculum. Per locked canonicals (docs/audits/2026-05-04-incident-canonicals.md):

{PER_FILE_SUMMARY}

Guardrail (scripts/check_incident_reuse.py) passes for all files in this PR.

Refs #878.

Co-Authored-By: Claude Sonnet 4.6 (headless dispatch) <noreply@anthropic.com>
COMMIT
)"
git push -u origin {WORKTREE_BRANCH}
gh pr create --title "{PR_TITLE}" --body "$(cat <<BODY
## Summary

Closes a track-scoped portion of #878.

{TRACK_NAME} sweep — {N} modules rewritten so that each named real-world
incident appears in at most one module across the curriculum. Per the
locked canonicals at \`docs/audits/2026-05-04-incident-canonicals.md\`.

{PER_FILE_SUMMARY_MARKDOWN}

## Verification

- [x] \`scripts/check_incident_reuse.py\` passes for files in this PR
- [x] \`npm run build\` succeeds (0 errors)
- [x] All replacement incidents have primary-source URLs in the module's Sources section
- [x] No fabricated companies, no invented dollar figures
- [ ] Cross-family Gemini-OAuth review (next step)

Refs #878.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
BODY
)"
```

## Cross-family review dispatch (orchestrator runs this AFTER the agent reports done)

```bash
KUBEDOJO_GEMINI_SUBSCRIPTION=1 .venv/bin/python scripts/dispatch.py gemini --review --github {PR_NUM} --timeout 900 - <<EOF
Review PR #{PR_NUM} ({TRACK_NAME} sweep for incident de-duplication, refs #878).

Quality bar (verbatim from user 2026-05-04):
> "I want nice proper solution, which is still enjoyable to read but no bullshit,
>  humans are very receptive for that. you cannot fool a human."

Check each rewritten "Why This Module Matters" section for:

1. Real incident with primary-source URL in Sources section (not Wikipedia).
2. No invented dollar figures or fabricated company names.
3. The replacement incident topically fits the module's lesson.
4. Concept-led rewrites (option c) lead with the principle, not a fake hook.
5. Cross-references (option b) are short, single-sentence, and contain
   the <!-- incident-xref: SLUG --> marker within 200 chars.
6. Tone matches the rest of the curriculum: third person, factual, neutral.

Verdict: APPROVE / APPROVE_WITH_NITS / NEEDS CHANGES.
EOF
```

## Acceptance criteria for the sweep PR

- Guardrail passes for files in PR (no violations for those file paths)
- `npm run build` succeeds
- Gemini review verdict ≥ APPROVE_WITH_NITS
- All replacement incidents trace to a primary source
- No fictional companies, no invented stats

## Edge cases

- **Module currently uses TWO different parroted incidents** (e.g. Knight Capital + SolarWinds in modern-devops/1.3): the canonical for SolarWinds IS modern-devops/1.3, so SolarWinds stays; Knight Capital must go (replace, cross-ref, or concept-lead).
- **Module is its own canonical for incident X but currently uses incident Y**: keep X (it lives there), rewrite Y per the rule.
- **Module's canonical mention is buried in a Sources section, not the WTMM**: a sweep PR may promote the canonical mention into the WTMM if that improves teaching. Use judgment.
- **Replacement catalog runs out of unused incidents for a bucket**: switch to option (c) concept-led. Don't reuse a catalog incident in a second module — the guardrail will catch it.
