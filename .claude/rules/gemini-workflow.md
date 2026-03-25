---
description: How to work with Gemini via the ai_agent_bridge
---

# Gemini Multi-Agent Workflow

## Bridge Command
```bash
python scripts/ai_agent_bridge/__main__.py ask-gemini "prompt" --task-id "id" --stdout-only
```

## Gemini Roles
1. **Adversary Reviewer** — send work for review before closing issues
2. **Translator** — produces good Ukrainian translations (99-100% of original)
3. **Content Drafter** — writes first drafts (~350-400L), needs Claude expansion to 700-900+
4. **Curriculum Planner** — gap analysis, module specs (push back if it duplicates existing content)

## Content Pipeline
1. Plan with Gemini → 2. Gemini drafts OR Claude writes → 3. Claude expands if Gemini drafted → 4. Gemini reviews → 5. Fix feedback → 6. Commit

## Gemini Limitations
- Cannot write full-depth modules from scratch (produces outlines)
- Sometimes flags existing content as "missing" (always cross-check docs/)
- Use `scripts/prompts/module-writer.md` when asking Gemini to draft
