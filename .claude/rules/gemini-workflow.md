---
description: How to work with Gemini via direct CLI dispatch
---

# Gemini Multi-Agent Workflow

## Dispatch Command
```bash
# Simple review (stdout)
python scripts/dispatch.py gemini "prompt" --review

# Review and post to GitHub issue
python scripts/dispatch.py gemini "prompt" --review --github 66

# Read prompt from stdin
echo "prompt" | python scripts/dispatch.py gemini - --review
```
Default model: `gemini-3.1-pro-preview`

## Programmatic Usage (from Python)
```python
from scripts.dispatch import dispatch_gemini_with_retry, post_to_github

ok, output = dispatch_gemini_with_retry("Review this module...", review=True)
if ok:
    post_to_github(66, output, "gemini-3.1-pro-preview")
```

## Gemini Roles

**1. Adversary Reviewer (primary role)**
- Send completed work to Gemini for review BEFORE closing any issue
- Gemini catches: version inaccuracies, missing ACs, scope gaps, technical errors, Russicisms in translations
- If Gemini says NEEDS CHANGES, address feedback before closing
- Post Gemini's review as a comment on the issue

**2. Translator (Ukrainian)**
- Produces good Ukrainian translations (99-100% of original length)
- Quality: 9-10/10 for Ukrainian language
- Must follow glossary at `docs/glossary.md`

**3. Content Drafter (with expansion)**
- Writes first drafts (~350-400 lines) — needs Claude expansion to 700-900+
- Use `scripts/prompts/module-writer.md` as the prompt
- Workflow: Gemini drafts → Claude reads → Claude expands (adds tables, diagrams, code, depth)

**4. Curriculum Planner**
- Good at gap analysis and proposing structure
- Push back if suggestions duplicate existing content (Gemini sometimes misses what exists)
- Always cross-reference suggestions against actual `docs/` directory

## Content Pipeline
1. **Plan** with Gemini (gap analysis, module specs, structure)
2. **Draft** — either Gemini drafts (needs expansion) or Claude writes directly (full quality)
3. **Expand** — if Gemini drafted, Claude agent reads and expands to full depth
4. **Review** — Gemini adversary review (score, flag issues)
5. **Fix** — address Gemini feedback
6. **Commit** — with nav updates, READMEs, changelog

## Gemini Limitations
- Cannot write full-depth modules from scratch (produces outlines ~140-400 lines)
- Sometimes flags existing content as "missing" (Vault, Velero, KEDA were all flagged when already covered)
- Use `scripts/prompts/module-writer.md` when asking Gemini to draft
