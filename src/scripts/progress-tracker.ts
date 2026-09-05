/**
 * KubeDojo Progress Tracker
 * Issue: #139
 *
 * localStorage-based module completion tracking.
 * Adds "Mark as Complete" button to module pages.
 * Decorates sidebar links with checkmarks for completed modules.
 */

import { loadLessonCatalog } from './progress-client';
import type { Lesson } from './progress-catalog';
import type { ProgressData } from './progress-data';
import { lessonIsComplete, PROGRESS_KEY, readSavedProgress, setLessonComplete } from './progress-state';

let catalog: Lesson[] = [];
const storage = () => window.localStorage;

// ===== Core API =====

function getProgress(): ProgressData {
  const result = readSavedProgress(storage);
  if (!result.ok) throw new Error('Saved progress could not be read. Your existing data has not been changed.');
  return result.data;
}

function markComplete(slug: string): void {
  if (!setLessonComplete(storage, catalog, slug, true).ok) throw new Error('Progress could not be saved.');
}

function markIncomplete(slug: string): void {
  if (!setLessonComplete(storage, catalog, slug, false).ok) throw new Error('Progress could not be saved.');
}

function isComplete(slug: string): boolean {
  const lesson = catalog.find(item => item.keys.includes(slug));
  return !!lesson && lessonIsComplete(lesson, getProgress());
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

  // Don't add to non-module pages (changelog, landing pages)
  if (!catalog.some(lesson => lesson.keys.includes(slug))) return;

  // Find the pagination nav (prev/next) or end of content
  const pagination = document.querySelector('.pagination-links') ||
                     document.querySelector('[class*="pagination"]');

  // Don't duplicate
  if (document.querySelector('.kd-complete-wrapper')) return;

  const wrapper = document.createElement('div');
  wrapper.className = 'kd-complete-wrapper';
  wrapper.style.cssText = 'margin: 2rem 0 1rem; padding-top: 1.5rem; border-top: 1px solid var(--sl-color-gray-2);';

  const btn = document.createElement('button');
  btn.className = 'kd-complete-btn';
  updateButtonState(btn, slug);

  btn.addEventListener('click', () => {
    try {
      if (isComplete(slug)) {
        markIncomplete(slug);
      } else {
        markComplete(slug);
      }
      updateButtonState(btn, slug);
      decorateSidebar();
      document.getElementById('kd-progress-error')?.remove();
    } catch (error) { showError(error); }
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
  btn.textContent = completed
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
    const lesson = catalog.find(item => item.keys.includes(slug));
    if (lesson && lessonIsComplete(lesson, data)) {
      link.setAttribute('data-completed', 'true');
    } else {
      link.removeAttribute('data-completed');
    }
  });
}

// ===== Init =====

function showError(error: unknown): void {
  const complete = document.querySelector<HTMLButtonElement>('.kd-complete-btn');
  if (complete) {
    complete.disabled = true;
    complete.removeAttribute('aria-pressed');
    complete.textContent = 'Progress unavailable';
  }
  document.querySelectorAll('[data-completed]').forEach(link => link.removeAttribute('data-completed'));
  let note = document.getElementById('kd-progress-error');
  if (!note) {
    note = document.createElement('p');
    note.id = 'kd-progress-error';
    note.setAttribute('role', 'alert');
    document.querySelector('.sl-markdown-content')?.appendChild(note);
  }
  note.textContent = error instanceof Error ? error.message : 'Progress is unavailable.';
  const retry = document.createElement('button');
  retry.textContent = 'Retry progress';
  retry.addEventListener('click', () => { void init(); });
  note.append(' ', retry);
}

export async function init(): Promise<void> {
  try {
    catalog = await loadLessonCatalog();
    injectCompleteButton();
    decorateSidebar();
    const btn = document.querySelector<HTMLButtonElement>('.kd-complete-btn');
    if (btn) {
      updateButtonState(btn, location.pathname.replace(/^\/|\/$/g, ''));
      btn.disabled = false;
    }
    document.getElementById('kd-progress-error')?.remove();
  } catch (error) { showError(error); }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

// Re-run on Astro page transitions
document.addEventListener('astro:page-load', init);
document.addEventListener('kubedojo:progress-change', init);
window.addEventListener('storage', event => {
  if (event.key === PROGRESS_KEY || event.key === null) void init();
});
