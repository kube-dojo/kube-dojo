---
description: Checklist before committing new modules or content changes
---

# New Content Checklist

EVERY TIME new modules are added, do ALL of these BEFORE committing:

1. **mkdocs.yml nav** — add to navigation
2. **Parent README** — add module to section's README table
3. **Build** — `source .venv/bin/activate && NO_MKDOCS_2_WARNING=1 mkdocs build` — verify 0 warnings
4. **Verify links** — no broken relative links or orphaned modules
5. **changelog.md** — add entry for significant additions
6. **index.md** — update if module counts changed significantly
