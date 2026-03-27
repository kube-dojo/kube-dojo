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
function enhanceMetaChips(root: Element): void {
  const firstBq = root.querySelector('blockquote');
  if (!firstBq || firstBq.closest('.kd-warstory') || firstBq.closest('.kd-dyk')) return;

  const text = firstBq.textContent || '';
  // Only target the metadata blockquote (contains Complexity or Time to Complete)
  if (!text.includes('Complexity') && !text.includes('Time to Complete')) return;
  if (firstBq.classList.contains('kd-meta-enhanced')) return;

  firstBq.classList.add('kd-meta-enhanced');

  // Style complexity badges inline
  const html = firstBq.innerHTML;
  const styled = html
    .replace(/\[QUICK\]/g, '<span class="kd-chip kd-chip-quick">[QUICK]</span>')
    .replace(/\[MEDIUM\]/g, '<span class="kd-chip kd-chip-medium">[MEDIUM]</span>')
    .replace(/\[ADVANCED\]/g, '<span class="kd-chip kd-chip-advanced">[ADVANCED]</span>')
    .replace(/\[EXPERT\]/g, '<span class="kd-chip kd-chip-advanced">[EXPERT]</span>');

  if (styled !== html) {
    firstBq.innerHTML = styled;
  }
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
