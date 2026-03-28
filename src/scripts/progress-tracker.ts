/**
 * KubeDojo Progress Tracker
 * Issue: #139
 *
 * localStorage-based module completion tracking.
 * Adds "Mark as Complete" button to module pages.
 * Decorates sidebar links with checkmarks for completed modules.
 */

const STORAGE_KEY = 'kubedojo-progress';

interface ProgressData {
  [slug: string]: number; // timestamp of completion
}

// ===== Core API =====

function getProgress(): ProgressData {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function saveProgress(data: ProgressData): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  } catch {
    // localStorage full or unavailable — fail silently
  }
}

function markComplete(slug: string): void {
  const data = getProgress();
  data[slug] = Date.now();
  saveProgress(data);
}

function markIncomplete(slug: string): void {
  const data = getProgress();
  delete data[slug];
  saveProgress(data);
}

function isComplete(slug: string): boolean {
  return slug in getProgress();
}

function getTrackProgress(trackPrefix: string): { completed: number; total: number } {
  const data = getProgress();
  const sidebarLinks = document.querySelectorAll('.kd-sb a[href]');
  let total = 0;
  let completed = 0;
  sidebarLinks.forEach((link) => {
    const href = (link as HTMLAnchorElement).pathname;
    if (href.startsWith(`/${trackPrefix}`)) {
      total++;
      const slug = href.replace(/^\/|\/$/g, '');
      if (data[slug]) completed++;
    }
  });
  return { completed, total };
}

function exportProgress(): string {
  return JSON.stringify(getProgress(), null, 2);
}

function importProgress(json: string): boolean {
  try {
    const data = JSON.parse(json);
    if (typeof data !== 'object') return false;
    saveProgress(data);
    return true;
  } catch {
    return false;
  }
}

// ===== UI: Mark Complete Button =====

function injectCompleteButton(): void {
  // Only show on module pages (not index/splash pages)
  const content = document.querySelector('.sl-markdown-content');
  if (!content) return;

  // Don't add to homepage
  if (document.querySelector('.kd-hero')) return;

  // Get current page slug
  const slug = window.location.pathname.replace(/^\/|\/$/g, '');
  if (!slug) return;

  // Find the pagination nav (prev/next) or end of content
  const pagination = document.querySelector('.pagination-links') ||
                     document.querySelector('[class*="pagination"]');
  const target = pagination || content;

  // Don't duplicate
  if (document.querySelector('.kd-complete-wrapper')) return;

  const wrapper = document.createElement('div');
  wrapper.className = 'kd-complete-wrapper';
  wrapper.style.cssText = 'margin: 2rem 0 1rem; padding-top: 1.5rem; border-top: 1px solid var(--sl-color-gray-2);';

  const btn = document.createElement('button');
  btn.className = 'kd-complete-btn';
  updateButtonState(btn, slug);

  btn.addEventListener('click', () => {
    if (isComplete(slug)) {
      markIncomplete(slug);
    } else {
      markComplete(slug);
    }
    updateButtonState(btn, slug);
    decorateSidebar();
  });

  wrapper.appendChild(btn);

  if (pagination) {
    pagination.parentNode?.insertBefore(wrapper, pagination);
  } else {
    content.appendChild(wrapper);
  }
}

function updateButtonState(btn: HTMLButtonElement, slug: string): void {
  const completed = isComplete(slug);
  btn.className = `kd-complete-btn${completed ? ' completed' : ''}`;
  btn.setAttribute('aria-pressed', String(completed));
  btn.innerHTML = completed
    ? '✓ Completed — click to undo'
    : '○ Mark as Complete';
}

// ===== UI: Sidebar Checkmarks =====

function decorateSidebar(): void {
  const data = getProgress();
  const links = document.querySelectorAll('.kd-sb a[href]');
  links.forEach((link) => {
    const href = (link as HTMLAnchorElement).pathname;
    const slug = href.replace(/^\/|\/$/g, '');
    if (data[slug]) {
      link.setAttribute('data-completed', 'true');
    } else {
      link.removeAttribute('data-completed');
    }
  });
}

// ===== Init =====

function init(): void {
  injectCompleteButton();
  decorateSidebar();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

// Re-run on Astro page transitions
document.addEventListener('astro:page-load', init);
