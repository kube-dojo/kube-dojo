import { countLessonProgress, type Lesson } from './progress-catalog';
import type { ProgressData } from './progress-data';
import { loadLessonCatalog } from './progress-client';
import { PROGRESS_KEY, readSavedProgress } from './progress-state';

const names = new Map(Object.entries({
  prerequisites: 'Fundamentals', linux: 'Linux', cloud: 'Cloud', k8s: 'Certifications',
  platform: 'Platform Engineering', 'on-premises': 'On-Premises', ai: 'AI',
  'ai-ml-engineering': 'AI/ML Engineering', 'ai-history': 'History of AI',
}));

function bar(label: string, completed: number, total: number): HTMLProgressElement {
  const element = document.createElement('progress');
  element.max = Math.max(1, total);
  element.value = completed;
  element.setAttribute('aria-label', label);
  element.setAttribute('aria-valuetext', `${completed} of ${total} lessons marked complete`);
  element.style.width = '100%';
  return element;
}

/** Render only validated progress. Unknown keys remain stored but are not lessons. */
export function renderProgressDashboard(target: HTMLElement, lessons: Lesson[], data: ProgressData): void {
  const counts = countLessonProgress(lessons, Object.keys(data));
  const summary = document.createElement('p');
  const percentage = counts.total ? Math.round(100 * counts.completed / counts.total) : 0;
  summary.textContent = `${counts.completed} of ${counts.total} lessons marked complete (${percentage}%).`;
  target.replaceChildren(summary, bar('All lessons', counts.completed, counts.total));
  for (const [track, count] of Object.entries(counts.tracks)) {
    const section = document.createElement('section');
    const title = document.createElement('h3');
    const label = names.get(track) ?? track;
    title.textContent = label;
    const text = document.createElement('p');
    text.textContent = `${count.completed} / ${count.total} lessons marked complete`;
    section.append(title, text, bar(label, count.completed, count.total));
    target.appendChild(section);
  }
  if (counts.unknownKeys.length) {
    const note = document.createElement('p');
    note.textContent = `${counts.unknownKeys.length} saved entries are outside the current lesson catalog. They remain in your backup and are not counted above.`;
    target.appendChild(note);
  }
}

export async function refreshProgressDashboard(): Promise<void> {
  const target = document.getElementById('kd-progress-dashboard');
  if (!target) return;
  target.setAttribute('aria-busy', 'true');
  try {
    const lessons = await loadLessonCatalog();
    const state = readSavedProgress(() => window.localStorage);
    if (!state.ok) throw new Error(state.reason === 'invalid'
      ? 'Saved progress is invalid. Export the original backup before importing or resetting.'
      : 'Browser storage is unavailable. Progress cannot be read.');
    renderProgressDashboard(target, lessons, state.data);
  } catch (error) {
    const note = document.createElement('p');
    note.setAttribute('role', 'alert');
    note.textContent = error instanceof Error ? error.message : 'Progress is unavailable.';
    const retry = document.createElement('button');
    retry.textContent = 'Retry progress';
    retry.addEventListener('click', () => { void refreshProgressDashboard(); });
    target.replaceChildren(note, retry);
  } finally {
    target.setAttribute('aria-busy', 'false');
  }
}

if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', refreshProgressDashboard);
else void refreshProgressDashboard();
document.addEventListener('astro:page-load', refreshProgressDashboard);
document.addEventListener('kubedojo:progress-change', refreshProgressDashboard);
window.addEventListener('storage', event => {
  if (event.key === PROGRESS_KEY || event.key === null) void refreshProgressDashboard();
});
