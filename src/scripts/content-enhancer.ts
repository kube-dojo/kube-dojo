/**
 * KubeDojo Content Enhancer
 * Issue: #138
 *
 * Runs on every page. Finds War Story, Did You Know, and Quiz patterns
 * in existing .md content and adds CSS classes for rich styling.
 * No .md files are modified — purely additive DOM enhancement.
 */

function enhanceContent(): void {
  const content = document.querySelector('.sl-markdown-content');
  if (!content) return;

  enhanceMetaChips(content);
  enhanceWarStories(content);
  enhanceDidYouKnow(content);
  enhanceQuizSections(content);
  enhanceDedication(content);
}

/**
 * Meta Chips: Style the first blockquote (Complexity/Time/Prerequisites)
 * as colored badge chips matching the POC design.
 */
/**
 * Meta Chips: Transform the first blockquote (Complexity/Time/Prerequisites)
 * into colored inline chips matching the POC design.
 * POC shows: ⚠ Medium | ⏱ 45-55 min | 🏆 CKA Exam (as colored pills on one line)
 */
function buildChips(complexity: string | null, time: string | null): HTMLDivElement | null {
  const chips: string[] = [];
  if (complexity) {
    const upper = complexity.toUpperCase();
    const cls = upper === 'QUICK' ? 'kd-chip-quick' :
                (upper === 'MEDIUM' ? 'kd-chip-medium' : 'kd-chip-advanced');
    const icon = upper === 'QUICK' ? '✓' : upper === 'MEDIUM' ? '⚠' : '⚡';
    chips.push(`<span class="kd-chip ${cls}">${icon} ${upper.charAt(0) + upper.slice(1).toLowerCase()}</span>`);
  }
  if (time) {
    chips.push(`<span class="kd-chip kd-chip-time">⏱ ${time}</span>`);
  }
  if (chips.length === 0) return null;
  const div = document.createElement('div');
  div.className = 'kd-meta-chips';
  div.innerHTML = chips.join('');
  return div;
}

function enhanceMetaChips(root: Element): void {
  if (root.querySelector('.kd-meta-chips')) return; // already enhanced

  // Pattern 1: blockquote format (e.g. "> **Toolkit Track** | Complexity: `[COMPLEX]` | Time: 45 min")
  const firstBq = root.querySelector('blockquote');
  if (firstBq && !firstBq.closest('.kd-warstory') && !firstBq.closest('.kd-dyk')) {
    const text = firstBq.textContent || '';
    if (text.includes('Complexity') || text.includes('Time to Complete') || text.includes('Time:')) {
      const complexityMatch = text.match(/\[(QUICK|MEDIUM|COMPLEX|ADVANCED|EXPERT)\]/i);
      const timeMatch = text.match(/Time(?:\s+to\s+Complete)?:\s*(.+?)(?:\n|$|\|)/);
      const chips = buildChips(
        complexityMatch ? complexityMatch[1] : null,
        timeMatch ? timeMatch[1].trim() : null,
      );
      if (chips) { firstBq.replaceWith(chips); return; }
    }
  }

  // Pattern 2: H2 heading format (e.g. "## Complexity: [COMPLEX]" + "## Time to Complete: 55-60 min")
  const headings = root.querySelectorAll('h2');
  let complexityH2: Element | null = null;
  let timeH2: Element | null = null;
  let complexity: string | null = null;
  let time: string | null = null;

  for (const h2 of headings) {
    const text = h2.textContent || '';
    const cMatch = text.match(/Complexity:\s*\[?(QUICK|MEDIUM|COMPLEX|ADVANCED|EXPERT)\]?/i);
    if (cMatch) { complexityH2 = h2; complexity = cMatch[1]; continue; }
    const tMatch = text.match(/Time(?:\s+to\s+Complete)?:\s*(.+)/i);
    if (tMatch) { timeH2 = h2; time = tMatch[1].trim(); continue; }
    // Stop scanning after first non-meta heading
    if (complexityH2 || timeH2) break;
  }

  if (!complexityH2 && !timeH2) return;

  const chips = buildChips(complexity, time);
  if (!chips) return;

  // Replace the first meta heading with chips, remove the other
  const firstEl = complexityH2 || timeH2;
  const secondEl = complexityH2 && timeH2 ? (complexityH2 === firstEl ? timeH2 : complexityH2) : null;
  // Remove the HR between them if present
  if (firstEl && secondEl) {
    let between = firstEl.nextElementSibling;
    while (between && between !== secondEl) {
      const next = between.nextElementSibling;
      if (between.tagName === 'HR') between.remove();
      between = next;
    }
    secondEl.remove();
  }
  firstEl!.replaceWith(chips);
}

/**
 * War Stories: Find headings containing "War Story" and wrap
 * the heading + following content in a styled card.
 */
function enhanceWarStories(root: Element): void {
  const headings = root.querySelectorAll('h2, h3, h4');
  headings.forEach((heading) => {
    const text = heading.textContent || '';
    if (!text.toLowerCase().includes('war story')) return;
    if (heading.closest('.kd-warstory')) return; // already enhanced

    // Extract impact from heading text (e.g. "$2.3M lost revenue")
    const impactMatch = text.match(/\$[\d.,]+[MBK]?\s*[\w\s]*/i);

    // Collect sibling elements until next heading of same or higher level
    const level = parseInt(heading.tagName[1]);
    const siblings: Element[] = [];
    let next = heading.nextElementSibling;
    while (next) {
      if (next.tagName.match(/^H[1-6]$/) && parseInt(next.tagName[1]) <= level) break;
      siblings.push(next);
      next = next.nextElementSibling;
    }

    // Build wrapper
    const wrapper = document.createElement('div');
    wrapper.className = 'kd-warstory';

    const header = document.createElement('div');
    header.className = 'kd-warstory-header';
    header.innerHTML = `<span>🔥</span><span>${text.replace(/war story:?\s*/i, '').trim() || 'War Story'}</span>`;
    if (impactMatch) {
      header.innerHTML += `<span class="impact">${impactMatch[0].trim()}</span>`;
    }

    const body = document.createElement('div');
    body.className = 'kd-warstory-body';

    // Move siblings into body
    siblings.forEach((el) => body.appendChild(el));

    wrapper.appendChild(header);
    wrapper.appendChild(body);

    // Replace heading with wrapper
    heading.replaceWith(wrapper);
  });
}

/**
 * Did You Know: Find headings or blockquotes containing "Did You Know"
 * and wrap in a styled card.
 */
function enhanceDidYouKnow(root: Element): void {
  // Pattern 1: ## Did You Know? heading followed by blockquotes
  const headings = root.querySelectorAll('h2, h3');
  headings.forEach((heading) => {
    const text = heading.textContent || '';
    if (!text.toLowerCase().includes('did you know')) return;
    if (heading.closest('.kd-dyk')) return;

    // Collect following blockquotes
    const blockquotes: Element[] = [];
    let next = heading.nextElementSibling;
    while (next) {
      if (next.tagName === 'BLOCKQUOTE') {
        blockquotes.push(next);
      } else if (next.tagName === 'HR' || next.tagName.match(/^H[1-6]$/)) {
        break;
      }
      next = next.nextElementSibling;
    }

    if (blockquotes.length === 0) return;

    const wrapper = document.createElement('div');
    wrapper.className = 'kd-dyk';

    const header = document.createElement('div');
    header.className = 'kd-dyk-header';
    header.innerHTML = '💡 Did You Know?';

    wrapper.appendChild(header);
    blockquotes.forEach((bq) => {
      const div = document.createElement('div');
      div.className = 'kd-dyk-item';
      div.innerHTML = bq.innerHTML;
      wrapper.appendChild(div);
    });

    // Replace heading and blockquotes
    blockquotes.forEach((bq) => bq.remove());
    heading.replaceWith(wrapper);
  });
}

/**
 * Quiz sections: Enhance details/summary blocks within quiz sections
 * with letter badges and better styling.
 */
function enhanceQuizSections(root: Element): void {
  // Find quiz headings
  const headings = root.querySelectorAll('h2, h3');
  headings.forEach((heading) => {
    const text = (heading.textContent || '').toLowerCase();
    if (!text.includes('quiz') && !text.includes('knowledge check')) return;

    // Find all details elements after this heading
    let next = heading.nextElementSibling;
    let questionNum = 0;
    while (next) {
      if (next.tagName.match(/^H[1-6]$/) && next.tagName <= heading.tagName) break;

      if (next.tagName === 'DETAILS') {
        const summary = next.querySelector('summary');
        if (summary && !summary.querySelector('.kd-quiz-badge')) {
          questionNum++;
          const badge = document.createElement('span');
          badge.className = 'kd-quiz-badge';
          badge.textContent = `Q${questionNum}`;
          badge.style.cssText = `
            display: inline-block; background: #326CE5; color: white;
            font-size: 0.7rem; font-weight: 700; padding: 0.1rem 0.5rem;
            border-radius: 4px; margin-right: 0.5rem; font-family: var(--sl-font-mono);
          `;
          summary.prepend(badge);
        }
        next.classList.add('kd-quiz-item');
      }
      next = next.nextElementSibling;
    }
  });
}

/**
 * Dedication: Wrap the 🇺🇦 Dedication/Присвята section in a Ukrainian flag border.
 */
function enhanceDedication(root: Element): void {
  const headings = root.querySelectorAll('h2');
  headings.forEach((heading) => {
    const text = heading.textContent || '';
    if (!text.includes('Dedication') && !text.includes('Присвята')) return;
    if (heading.closest('.kd-dedication-wrap')) return;

    // Collect ALL siblings until the next <hr> or end of content
    // This captures the h2, paragraphs, h3 (poem title), AND the blockquote (poem)
    const siblings: Element[] = [];
    let next = heading.nextElementSibling;
    while (next) {
      // Stop at <hr> (markdown ---) which separates dedication from the dojo quote
      if (next.tagName === 'HR') break;
      // Stop at another h2 that ISN'T part of the dedication
      if (next.tagName === 'H2' && !next.textContent?.includes('Заповіт') && !next.textContent?.includes('Testament')) break;
      siblings.push(next);
      next = next.nextElementSibling;
    }

    // Build wrapper with flag border
    const outer = document.createElement('div');
    outer.className = 'kd-dedication-wrap';
    const inner = document.createElement('div');
    inner.className = 'kd-dedication-wrap-inner';

    // Clone heading into inner, then move siblings
    inner.appendChild(heading.cloneNode(true));
    siblings.forEach((el) => inner.appendChild(el));

    outer.appendChild(inner);
    heading.replaceWith(outer);
  });
}

// Run on page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', enhanceContent);
} else {
  enhanceContent();
}

// Re-run on Astro page transitions (View Transitions)
document.addEventListener('astro:page-load', enhanceContent);
