# Claude Extensions for KubeDojo

This folder contains Claude Code slash commands and skills for the KubeDojo project.

## Structure

```
claude_extensions/
├── skills/             # Skills (auto-invoked by Claude)
│   ├── module-quality-reviewer.md
│   ├── cka-expert.md
│   └── curriculum-writer.md
└── README.md
```

Slash commands (`/review-module`, `/review-part`, `/verify-technical`)
were retired 2026-05-21: the production review workflow runs through
`scripts/dispatch_smart.py review --agent sonnet|agy|codex`, the
deterministic verifier is `scripts/quality/verify_module.py`, and the
cross-family review protocol lives in `docs/review-protocol.md`. Skills
below are still active.

## Available Skills

### `module-quality-reviewer`
Comprehensive quality assessment using the KubeDojo quality rubric. Scores modules on Theory, Practical, Engagement, and Exam Relevance.

### `cka-expert`
Authoritative CKA 2025 curriculum knowledge. Use when writing or reviewing CKA content to ensure accuracy.

### `curriculum-writer`
Module template and writing guidelines. Use when creating new modules to ensure consistent structure and tone.

## Deployment

Extensions are automatically deployed when using `start-claude.sh`:

```bash
# From kubedojo root - recommended way to start
./start-claude.sh
```

Or deploy manually:

```bash
# Deploy extensions only
./claude_extensions/deploy.sh

# Deploy quietly (for scripts)
./claude_extensions/deploy.sh --quiet
```

The deploy script only copies changed files, making it fast and safe to run repeatedly.

## Development Workflow

1. **Edit** extensions in `claude_extensions/` (tracked in git)
2. **Test** by deploying to `.claude/` locally
3. **Commit** changes to `claude_extensions/`
4. **Deploy** to `.claude/` when ready to use

The `.claude/` directory is gitignored—it's the "installed" version.

## Creating New Skills

1. Create `claude_extensions/skills/your-skill.md`
2. Write comprehensive knowledge/instructions
3. Deploy to `.claude/skills/`
4. Claude will auto-invoke when relevant

Skills don't need YAML frontmatter—they're reference documents that Claude uses when the topic is relevant.

## Quality Standards Reference

All modules should score 8+/10 to be considered complete:

| Category | Weight | What It Measures |
|----------|--------|------------------|
| Theory Depth | 25% | Explains "why", junior-friendly |
| Practical Value | 25% | Runnable code, clear steps |
| Engagement | 25% | Analogies, war stories, tone |
| Exam Relevance | 25% | CKA 2025 aligned, speed tips |

Target: **10/10** for all modules (Part 0 is the reference standard).
