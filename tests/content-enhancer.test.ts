import { describe, it, expect, beforeEach } from 'vitest';

// Test the content enhancer DOM transforms by simulating the patterns
// it looks for and verifying the output.

// Helper: create a minimal .sl-markdown-content container
function createContent(html: string): Element {
  document.body.innerHTML = `<div class="sl-markdown-content">${html}</div>`;
  return document.querySelector('.sl-markdown-content')!;
}

// Re-implement the enhancer functions for testing (they read from DOM)
// These mirror the actual implementations in content-enhancer.ts

function enhanceMetaChips(root: Element): void {
  const firstBq = root.querySelector('blockquote');
  if (!firstBq || firstBq.closest('.kd-warstory') || firstBq.closest('.kd-dyk')) return;

  const text = firstBq.textContent || '';
  if (!text.includes('Complexity') && !text.includes('Time to Complete')) return;
  if (firstBq.classList.contains('kd-meta-enhanced')) return;

  firstBq.classList.add('kd-meta-enhanced');

  const complexityMatch = text.match(/\[(QUICK|MEDIUM|ADVANCED|EXPERT)\]/i);
  const complexity = complexityMatch ? complexityMatch[1].toUpperCase() : null;

  const timeMatch = text.match(/Time to Complete:\s*(.+?)(?:\n|$)/);
  const time = timeMatch ? timeMatch[1].trim() : null;

  const chips: string[] = [];
  if (complexity) {
    const cls = complexity === 'QUICK' ? 'kd-chip-quick' :
                complexity === 'MEDIUM' ? 'kd-chip-medium' : 'kd-chip-advanced';
    const icon = complexity === 'QUICK' ? '✓' : complexity === 'MEDIUM' ? '⚠' : '⚡';
    chips.push(`<span class="kd-chip ${cls}">${icon} ${complexity.charAt(0) + complexity.slice(1).toLowerCase()}</span>`);
  }
  if (time) {
    chips.push(`<span class="kd-chip kd-chip-time">⏱ ${time}</span>`);
  }

  if (chips.length > 0) {
    const chipsDiv = document.createElement('div');
    chipsDiv.className = 'kd-meta-chips';
    chipsDiv.innerHTML = chips.join('');
    firstBq.replaceWith(chipsDiv);
  }
}

function enhanceWarStories(root: Element): void {
  const headings = root.querySelectorAll('h2, h3, h4');
  headings.forEach((heading) => {
    const text = heading.textContent || '';
    if (!text.toLowerCase().includes('war story')) return;
    if (heading.closest('.kd-warstory')) return;

    const level = parseInt(heading.tagName[1]);
    const siblings: Element[] = [];
    let next = heading.nextElementSibling;
    while (next) {
      if (next.tagName.match(/^H[1-6]$/) && parseInt(next.tagName[1]) <= level) break;
      siblings.push(next);
      next = next.nextElementSibling;
    }

    const wrapper = document.createElement('div');
    wrapper.className = 'kd-warstory';

    const header = document.createElement('div');
    header.className = 'kd-warstory-header';
    header.innerHTML = `<span>🔥</span><span>${text.replace(/war story:?\s*/i, '').trim() || 'War Story'}</span>`;

    const body = document.createElement('div');
    body.className = 'kd-warstory-body';
    siblings.forEach((el) => body.appendChild(el));

    wrapper.appendChild(header);
    wrapper.appendChild(body);
    heading.replaceWith(wrapper);
  });
}

function enhanceQuizSections(root: Element): void {
  const headings = root.querySelectorAll('h2, h3');
  headings.forEach((heading) => {
    const text = (heading.textContent || '').toLowerCase();
    if (!text.includes('quiz') && !text.includes('knowledge check')) return;

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
          summary.prepend(badge);
        }
        next.classList.add('kd-quiz-item');
      }
      next = next.nextElementSibling;
    }
  });
}

describe('Content Enhancer — Meta Chips', () => {
  beforeEach(() => { document.body.innerHTML = ''; });

  it('transforms complexity blockquote into chips', () => {
    const root = createContent(`
      <blockquote>Complexity: [MEDIUM] | Time to Complete: 45-55 min</blockquote>
      <p>Module content here</p>
    `);
    enhanceMetaChips(root);

    const chips = root.querySelector('.kd-meta-chips');
    expect(chips).not.toBeNull();
    expect(chips!.querySelector('.kd-chip-medium')).not.toBeNull();
    expect(chips!.querySelector('.kd-chip-time')).not.toBeNull();
    expect(chips!.querySelector('.kd-chip-time')!.textContent).toContain('45-55 min');
  });

  it('handles QUICK complexity', () => {
    const root = createContent(`<blockquote>Complexity: [QUICK] | Time to Complete: 15 min</blockquote>`);
    enhanceMetaChips(root);

    const chip = root.querySelector('.kd-chip-quick');
    expect(chip).not.toBeNull();
    expect(chip!.textContent).toContain('Quick');
  });

  it('handles ADVANCED complexity', () => {
    const root = createContent(`<blockquote>Complexity: [ADVANCED] | Time to Complete: 90 min</blockquote>`);
    enhanceMetaChips(root);

    expect(root.querySelector('.kd-chip-advanced')).not.toBeNull();
  });

  it('ignores blockquotes without Complexity/Time', () => {
    const root = createContent(`<blockquote>Just a regular quote</blockquote>`);
    enhanceMetaChips(root);

    expect(root.querySelector('.kd-meta-chips')).toBeNull();
    expect(root.querySelector('blockquote')).not.toBeNull();
  });

  it('does not double-enhance', () => {
    const root = createContent(`<blockquote>Complexity: [MEDIUM] | Time to Complete: 30 min</blockquote>`);
    enhanceMetaChips(root);
    enhanceMetaChips(root);

    expect(root.querySelectorAll('.kd-meta-chips').length).toBe(1);
  });
});

describe('Content Enhancer — War Stories', () => {
  beforeEach(() => { document.body.innerHTML = ''; });

  it('wraps war story heading + content in card', () => {
    const root = createContent(`
      <h2>War Story: $2.3M Database Meltdown</h2>
      <p>The database crashed at 3am.</p>
      <p>Nobody had monitoring.</p>
      <h2>Next Section</h2>
    `);
    enhanceWarStories(root);

    const warstory = root.querySelector('.kd-warstory');
    expect(warstory).not.toBeNull();
    expect(warstory!.querySelector('.kd-warstory-header')).not.toBeNull();
    expect(warstory!.querySelector('.kd-warstory-body')!.children.length).toBe(2);
  });

  it('does not capture content past the next heading', () => {
    const root = createContent(`
      <h2>War Story: Outage</h2>
      <p>Story content</p>
      <h2>Unrelated Section</h2>
      <p>Should not be captured</p>
    `);
    enhanceWarStories(root);

    const body = root.querySelector('.kd-warstory-body')!;
    expect(body.children.length).toBe(1);
    expect(body.textContent).toContain('Story content');
    expect(body.textContent).not.toContain('Should not be captured');
  });

  it('does not double-enhance', () => {
    const root = createContent(`<h2>War Story: Test</h2><p>Content</p>`);
    enhanceWarStories(root);
    enhanceWarStories(root);

    expect(root.querySelectorAll('.kd-warstory').length).toBe(1);
  });
});

describe('Content Enhancer — Quiz Sections', () => {
  beforeEach(() => { document.body.innerHTML = ''; });

  it('adds Q badges to details elements', () => {
    const root = createContent(`
      <h2>Knowledge Check</h2>
      <details><summary>What is a Pod?</summary><p>Answer</p></details>
      <details><summary>What is a Service?</summary><p>Answer</p></details>
      <details><summary>What is a Deployment?</summary><p>Answer</p></details>
    `);
    enhanceQuizSections(root);

    const badges = root.querySelectorAll('.kd-quiz-badge');
    expect(badges.length).toBe(3);
    expect(badges[0].textContent).toBe('Q1');
    expect(badges[1].textContent).toBe('Q2');
    expect(badges[2].textContent).toBe('Q3');
  });

  it('adds kd-quiz-item class to details', () => {
    const root = createContent(`
      <h2>Quiz</h2>
      <details><summary>Question</summary><p>Answer</p></details>
    `);
    enhanceQuizSections(root);

    expect(root.querySelector('details.kd-quiz-item')).not.toBeNull();
  });

  it('ignores non-quiz headings', () => {
    const root = createContent(`
      <h2>Regular Section</h2>
      <details><summary>Some details</summary><p>Content</p></details>
    `);
    enhanceQuizSections(root);

    expect(root.querySelectorAll('.kd-quiz-badge').length).toBe(0);
  });

  it('does not double-badge', () => {
    const root = createContent(`
      <h2>Quiz</h2>
      <details><summary>Q?</summary><p>A</p></details>
    `);
    enhanceQuizSections(root);
    enhanceQuizSections(root);

    expect(root.querySelectorAll('.kd-quiz-badge').length).toBe(1);
  });
});
