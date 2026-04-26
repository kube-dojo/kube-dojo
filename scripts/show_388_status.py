#!/usr/bin/env python3
"""Quick status of the #388 batch: what shipped, what needs review,
what's still pending, what failed."""
from __future__ import annotations
import json, re, subprocess, sys
from pathlib import Path
from collections import Counter

PEND_RE = re.compile(r'^revision_pending:\s*true', re.MULTILINE)
def has_banner(p: Path) -> bool:
    try: text = p.read_text(encoding='utf-8')
    except OSError: return False
    end = text.find('\n---', 3)
    if end < 0: return False
    return bool(PEND_RE.search(text[:end+4]))

state_dir = Path('.pipeline/quality-pipeline')

# Categorize every state file by stage + auto_approved flag
buckets = {
    'COMMITTED_full_review': [],
    'COMMITTED_auto_approved': [],
    'FAILED_visual_aid': [],
    'FAILED_density': [],
    'FAILED_claude_reviewer': [],
    'FAILED_codex_dispatch': [],
    'FAILED_other': [],
    'IN_FLIGHT': [],
    'OTHER': [],
}
for sp in sorted(state_dir.glob('*.json')):
    if sp.name.endswith('.lock'): continue
    try: d = json.loads(sp.read_text())
    except json.JSONDecodeError: continue
    stage = d.get('stage') or 'UNKNOWN'
    slug = sp.stem
    if stage == 'COMMITTED':
        auto = (d.get('review') or {}).get('auto_approved') is True
        buckets['COMMITTED_auto_approved' if auto else 'COMMITTED_full_review'].append(slug)
    elif stage == 'FAILED':
        fr = d.get('failure_reason') or ''
        if 'visual-aid regression' in fr:
            buckets['FAILED_visual_aid'].append((slug, fr[:80]))
        elif 'density gate failed' in fr or 'density gate' in fr:
            buckets['FAILED_density'].append((slug, fr[:80]))
        elif 'claude dispatch failed' in fr:
            buckets['FAILED_claude_reviewer'].append((slug, fr[:80]))
        elif 'codex' in fr.lower() and 'dispatch' in fr.lower():
            buckets['FAILED_codex_dispatch'].append((slug, fr[:80]))
        else:
            buckets['FAILED_other'].append((slug, fr[:80]))
    elif stage in {'WRITE_IN_PROGRESS','REVIEW_IN_PROGRESS','CITATION_VERIFY','REVIEW_PENDING'}:
        buckets['IN_FLIGHT'].append((slug, stage))

# Banners still showing on disk
still_bannered = sum(1 for p in Path('src/content/docs').rglob('*.md')
                     if p.name != 'index.md' and has_banner(p))

print('=' * 70)
print(f'#388 batch status — banner-set REWRITE scope')
print('=' * 70)
print(f'  shipped + reviewed (COMMITTED_full_review):      {len(buckets["COMMITTED_full_review"])}')
print(f'  shipped + auto-approved (COMMITTED_auto_approved): {len(buckets["COMMITTED_auto_approved"])}  ← needs deferred review')
print(f'  still has revision_pending banner on disk:       {still_bannered}  ← not yet rewritten')
print()
print('FAILEDs by mode:')
for k in ('FAILED_visual_aid','FAILED_density','FAILED_claude_reviewer','FAILED_codex_dispatch','FAILED_other'):
    if buckets[k]:
        print(f'  {k}: {len(buckets[k])}')
        for s, fr in buckets[k][:5]:
            print(f'    {s}')
            print(f'      → {fr}')

if buckets['IN_FLIGHT']:
    print()
    print('IN_FLIGHT (stuck stages, may need reset):')
    for s, st in buckets['IN_FLIGHT']:
        print(f'  {st:25s} {s}')

# Post-review queue file
prq = Path('.pipeline/quality-pipeline/post-review-queue.txt')
if prq.exists():
    n = sum(1 for _ in prq.read_text().splitlines() if _.strip())
    print(f'\npost-review queue file: {prq} ({n} slugs awaiting deferred review)')
