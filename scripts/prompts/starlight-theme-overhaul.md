# Starlight Theme Overhaul — Reusable Prompt

> Battle-tested from KubeDojo (568 modules, 1,437 pages, light/dark mode, i18n).
> Use this prompt when customizing a Starlight site's design.

---

## The #1 Rule

**CSS overrides on Starlight DON'T WORK for layout changes — use component overrides.**

- CSS works for: colors, fonts, spacing, borders, shadows, backgrounds
- CSS fails for: sidebar structure, header layout, footer nesting, page title format
- If you're fighting `!important` on layout — stop and override the component instead

---

## Architecture

```
src/
├── pages/
│   └── index.astro              ← Standalone homepage (bypasses Starlight entirely)
├── components/
│   ├── Header.astro             ← Custom topbar (logo, nav pills, search, theme toggle)
│   ├── Sidebar.astro            ← Filtering, collapsible, progress checkmarks
│   ├── PageTitle.astro          ← Breadcrumbs + clean title
│   ├── Footer.astro             ← Custom footer
│   └── Head.astro               ← Script injection point
├── css/
│   └── custom.css               ← Design tokens + Starlight overrides + custom classes
└── scripts/
    ├── content-enhancer.ts      ← Client-side DOM transforms (pattern → styled card)
    └── progress-tracker.ts      ← localStorage progress + sidebar decoration
```

### Config (astro.config.mjs)

```javascript
export default defineConfig({
  integrations: [
    starlight({
      components: {
        Head: './src/components/Head.astro',
        Header: './src/components/Header.astro',
        Footer: './src/components/Footer.astro',
        Sidebar: './src/components/Sidebar.astro',
        PageTitle: './src/components/PageTitle.astro',
      },
      customCss: ['./src/css/custom.css'],
    }),
  ],
});
```

---

## Step-by-Step Implementation

### Step 1: Homepage (if custom layout needed)

Create `src/pages/index.astro` as a **standalone Astro page** — no Starlight imports, full `<html>/<head>/<body>`. Starlight still handles all `src/content/docs/` pages.

Why standalone? Starlight's Hero component constrains layout. For hero sections, track cards, terminal visualizations, stats — bypass Starlight entirely.

```astro
---
// src/pages/index.astro — NO Starlight imports
---
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>My Site</title>
  <style>
    /* All CSS inline or imported */
  </style>
</head>
<body>
  <!-- Full control: hero, cards, stats, anything -->
</body>
</html>
```

### Step 2: Design Tokens (custom.css)

Define your palette as CSS variables. Override Starlight's tokens to change the accent color site-wide:

```css
:root {
  /* Your palette */
  --brand-primary: #326CE5;
  --brand-dark: #1a3a6e;
  --g50: #f8f9fa;
  --g200: #e2e8f0;
  --g800: #1e293b;
  --g900: #0f172a;

  /* Override Starlight tokens */
  --sl-color-accent: var(--brand-primary);
  --sl-color-accent-low: color-mix(in srgb, var(--brand-primary) 15%, white);
  --sl-color-accent-high: var(--brand-dark);
}
```

### Step 3: Dark Mode

Use `:root[data-theme='dark']` for every custom class. Never assume light-only:

```css
:root[data-theme='dark'] {
  --sl-color-bg: var(--g900);
  --sl-color-text: #e2e8f0;
}

/* Every custom component needs dark variant */
.my-card { background: white; border: 1px solid var(--g200); }
:root[data-theme='dark'] .my-card { background: var(--g800); border-color: var(--g700); }
```

### Step 4: Component Overrides

#### Header.astro — Custom Navigation

Key pattern: keep Starlight's built-in components (Search, ThemeSelect, SocialIcons, LanguageSelect) but wrap in custom layout:

```astro
---
import Default from '@astrojs/starlight/components/Header.astro';
import Search from '@astrojs/starlight/components/Search.astro';
import ThemeSelect from '@astrojs/starlight/components/ThemeSelect.astro';
import SocialIcons from '@astrojs/starlight/components/SocialIcons.astro';
---
<header class="my-header">
  <a href="/" class="my-logo">Logo</a>
  <nav class="my-nav">
    <a href="/docs/">Docs</a>
    <a href="/guides/">Guides</a>
  </nav>
  <div class="my-header-right">
    <Search {...Astro.props} />
    <ThemeSelect {...Astro.props} />
    <SocialIcons {...Astro.props} />
  </div>
</header>
```

#### Sidebar.astro — Intelligent Filtering

For large sites (100+ pages), show only the active section's children, not the full tree:

```astro
---
import type { Props } from '@astrojs/starlight/props';
const { sidebar } = Astro.props;

// Walk sidebar tree, find branch containing current page
function findActiveBranch(entries) {
  for (const e of entries) {
    if (e.type !== 'group') continue;
    if (!hasCurrent(e.entries)) continue;

    // Check if we should go deeper
    const activeChild = e.entries.find(c => c.type === 'group' && hasCurrent(c.entries));
    if (activeChild) {
      const groups = e.entries.filter(c => c.type === 'group');
      const hasDeep = groups.some(c => c.entries?.some(gc => gc.type === 'group'));
      if (groups.length <= 3 && hasDeep) {
        const deeper = findActiveBranch(e.entries);
        if (deeper) return deeper;
      }
    }
    return { label: e.label, entries: e.entries };
  }
  return null;
}

function hasCurrent(entries) {
  return entries.some(e =>
    (e.type === 'link' && e.isCurrent) ||
    (e.type === 'group' && hasCurrent(e.entries || []))
  );
}

const branch = findActiveBranch(sidebar);
---
<!-- Render branch.entries as collapsible <details> groups -->
```

#### PageTitle.astro — Breadcrumbs

Build breadcrumbs from the URL path, mapping slugs to friendly names:

```astro
---
import Default from '@astrojs/starlight/components/PageTitle.astro';
const path = Astro.url.pathname;
const parts = path.split('/').filter(Boolean);

const labels = {
  'docs': 'Documentation',
  'guides': 'Guides',
  // ... your mappings
};

const crumbs = parts.map((part, i) => ({
  label: labels[part] || part.replace(/-/g, ' '),
  href: '/' + parts.slice(0, i + 1).join('/') + '/',
}));
---
<nav aria-label="Breadcrumb" class="my-breadcrumbs">
  {crumbs.map((c, i) => (
    <>{i > 0 && <span>›</span>}<a href={c.href}>{c.label}</a></>
  ))}
</nav>
<Default {...Astro.props}><slot /></Default>
```

#### Head.astro — Script Injection

Wrap Starlight's Head to inject client-side scripts:

```astro
---
import Default from '@astrojs/starlight/components/Head.astro';
---
<Default {...Astro.props}><slot /></Default>
<script src="../scripts/content-enhancer.ts"></script>
```

### Step 5: Content Enhancer (Client-Side DOM Transforms)

Pattern: find elements in rendered HTML, wrap/restyle them. **Never modify markdown files.**

```typescript
// src/scripts/content-enhancer.ts

function enhance() {
  const content = document.querySelector('.sl-markdown-content');
  if (!content) return;

  // Example: Find all h2 with "War Story" and wrap in styled card
  content.querySelectorAll('h2, h3').forEach(heading => {
    if (!heading.textContent?.includes('War Story')) return;
    if (heading.closest('.my-warstory')) return; // Already enhanced

    const wrapper = document.createElement('div');
    wrapper.className = 'my-warstory';

    // Collect siblings until next heading of same/higher level
    const siblings = [];
    let next = heading.nextElementSibling;
    const level = parseInt(heading.tagName[1]);
    while (next && !(next.matches(`h1,h2,h3`) && parseInt(next.tagName[1]) <= level)) {
      siblings.push(next);
      next = next.nextElementSibling;
    }

    heading.before(wrapper);
    wrapper.append(heading, ...siblings);
  });
}

// Run on load AND on Astro page transitions (SPA mode)
function init() {
  enhance();
}
document.addEventListener('astro:page-load', init);
if (document.readyState !== 'loading') init();
else document.addEventListener('DOMContentLoaded', init);
```

---

## Common Pitfalls

| Pitfall | Why It Fails | Fix |
|---------|-------------|-----|
| CSS-only sidebar layout | Starlight renders sidebar server-side with fixed structure | Override `Sidebar.astro` component |
| Forgetting `astro:page-load` | Astro uses SPA transitions; `DOMContentLoaded` only fires once | Listen to both events |
| Forgetting dark mode | Users toggle theme; hardcoded colors break | Add `:root[data-theme='dark']` for every custom class |
| `!important` chains | Fighting Starlight's scoped styles escalates | Override the component instead |
| Modifying markdown in enhancer | Fragile, breaks on content updates | Only add/transform CSS classes on rendered HTML |
| Reinventing Search/ThemeSelect | Starlight's built-ins work well | Import and reuse them in your Header override |
| Giant sidebar on large sites | 500+ links overwhelm users | Filter sidebar to show only active branch |

---

## Validation Checklist

Before declaring the theme "done":

- [ ] `npm run build` — 0 errors, 0 warnings
- [ ] Light mode looks correct on all page types (home, docs, index pages)
- [ ] Dark mode looks correct everywhere (toggle and check)
- [ ] Mobile responsive (< 768px) — sidebar collapses, nav adapts
- [ ] All interactive elements have hover/focus states
- [ ] Accessibility: `aria-pressed`, `aria-hidden`, `role`, `tabindex` on interactive elements
- [ ] Page transitions work (click between pages, check script re-initialization)
- [ ] Search works (Starlight's Pagefind integration)
- [ ] i18n works if applicable (language switcher, correct URL prefixes)
