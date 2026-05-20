Refactor the following script excerpt while preserving behavior.

Goals:

- remove duplicate global state mutations where practical
- improve names so the data flow is clearer
- keep all checks behaviorally equivalent
- reduce LOC
- keep the output ruff-clean

Source: `scripts/check_site_health.py`, selected because it is an older
procedural script with global `errors`, `warnings`, and `stats` state shared
across many checks.

```python
errors = []
warnings = []
stats = {}

def error(msg: str):
    errors.append(msg)

def warn(msg: str):
    warnings.append(msg)

def check_frontmatter():
    missing_fm = 0
    missing_title = 0
    missing_order = 0
    for md in sorted(_iter_markdown_files()):
        rel = str(md.relative_to(DOCS_DIR))
        content = md.read_text(errors="replace")
        if not content.startswith("---"):
            error(f"Missing frontmatter: {rel}")
            missing_fm += 1
            continue
        parts = content.split("---", 2)
        if len(parts) < 3:
            error(f"Malformed frontmatter: {rel}")
            missing_fm += 1
            continue
        fm = parts[1]
        if "title:" not in fm:
            error(f"Missing title: {rel}")
            missing_title += 1
        if md.name.startswith("module-") and "order:" not in fm:
            warn(f"Missing sidebar.order: {rel}")
            missing_order += 1
```

Return the refactored Python code only.

