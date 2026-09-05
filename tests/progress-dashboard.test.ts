import { expect, it } from 'vitest';
import { buildLessonCatalog } from '../src/scripts/progress-catalog';
import { renderProgressDashboard } from '../src/scripts/progress-dashboard';

it('renders shared language counts, book chapters, new tracks and retained unknown entries', () => {
  const catalog = buildLessonCatalog([
    { source: 'src/content/docs/ai/module-a.md', pathname: '/ai/a/' },
    { source: 'src/content/docs/uk/ai/module-a.md', pathname: '/uk/ai/a/' },
    { source: 'src/content/docs/ai-history/ch-01.md', pathname: '/ai-history/ch-01/' },
    { source: 'src/content/docs/new-track/module-new.md', pathname: '/new-track/new/' },
  ]);
  const target = document.createElement('div');
  renderProgressDashboard(target, catalog, { 'ai/a': 1, 'uk/ai/a': 2, retired: 3 });
  expect(target.firstElementChild?.textContent).toBe('1 of 3 lessons marked complete (33%).');
  expect([...target.querySelectorAll('h3')].map(h => h.textContent)).toEqual(['History of AI', 'AI', 'new-track']);
  expect(target.textContent).toContain('1 saved entries are outside the current lesson catalog');
  expect(target.querySelector('progress')?.getAttribute('aria-valuetext')).toBe('1 of 3 lessons marked complete');
  renderProgressDashboard(target, catalog.slice(0, 1), { retired: 3 });
  expect(target.querySelectorAll('section')).toHaveLength(1);
  expect(target.firstElementChild?.textContent).toBe('0 of 1 lessons marked complete (0%).');
});

it('handles an empty catalog without false percentages or invalid progress bounds', () => {
  const target = document.createElement('div');
  renderProgressDashboard(target, [], {});
  expect(target.firstElementChild?.textContent).toBe('0 of 0 lessons marked complete (0%).');
  expect(target.querySelector('progress')?.max).toBe(1);
  expect(target.querySelector('progress')?.value).toBe(0);
});
