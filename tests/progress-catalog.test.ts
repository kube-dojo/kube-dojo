import { describe, expect, it } from 'vitest';
import { buildLessonCatalog, countLessonProgress } from '../src/scripts/progress-catalog';

const route = (source: string, pathname: string) => ({ source: `src/content/docs/${source}`, pathname });

describe('eligible lesson catalog', () => {
  it('uses runtime paths, unifies translated sources and includes fallback routes', () => {
    const catalog = buildLessonCatalog([
      route('ai/module-1.1-test.md', '/ai/custom/'),
      route('uk/ai/module-1.1-test.md', '/uk/ai/translated/'),
      route('ai/module-1.2-next.md', '/ai/next/'),
      route('ai/module-1.2-next.md', '/uk/ai/next/'),
    ]);
    expect(catalog).toHaveLength(2);
    expect(catalog[0].keys).toEqual(['ai/custom', 'uk/ai/translated']);
    const counts = countLessonProgress(catalog, ['ai/custom', 'uk/ai/translated', 'uk/ai/next']);
    expect(counts).toMatchObject({ total: 2, completed: 2, tracks: { ai: { total: 2, completed: 2 } } });
  });

  it('includes book chapters and new module tracks but excludes hubs and staging', () => {
    const catalog = buildLessonCatalog([
      route('ai-history/ch-01-test.md', '/ai-history/ch-01-test/'),
      route('new-track/module-1-test.mdx', '/new-track/module-1-test/'),
      route('ai-history/index.md', '/ai-history/'),
      route('progress.mdx', '/progress/'),
      route('new-track/module-2-test.staging.md', '/staging/'),
      route('new-track/module-picture.png', '/picture/'),
    ]);
    expect(catalog.map(({ kind }) => kind)).toEqual(['chapter', 'module']);
    expect(countLessonProgress(catalog, []).total).toBe(2);
  });

  it('keeps removed or renamed route marks outside counts without deleting them', () => {
    const keys = ['ai/retired', 'ai/new', 'uk/ai/retired'];
    const catalog = buildLessonCatalog([route('ai/module-new.md', '/ai/new/')]);
    expect(countLessonProgress(catalog, keys)).toMatchObject({
      total: 1, completed: 1, unknownKeys: ['ai/retired', 'uk/ai/retired'],
    });
    expect(keys).toEqual(['ai/retired', 'ai/new', 'uk/ai/retired']);
    expect(countLessonProgress([], keys)).toMatchObject({ total: 0, completed: 0, unknownKeys: keys });
  });

  it('retains a Ukrainian-only lesson in the shared catalog', () => {
    const catalog = buildLessonCatalog([route('uk/linux/module-new.md', '/uk/linux/new/')]);
    expect(catalog[0].id).toBe('linux/module-new');
    expect(countLessonProgress(catalog, ['uk/linux/new']).completed).toBe(1);
  });

  it('fails on ambiguous routes or normalized keys instead of choosing an owner', () => {
    expect(() => buildLessonCatalog([
      route('ai/module-a.md', '/same/'), route('ai/module-b.md', '/same/'),
    ])).toThrow('Duplicate');
    expect(() => buildLessonCatalog([
      route('ai/module-a.md', '/same/'), route('ai/module-b.md', '/same'),
    ])).toThrow('Ambiguous');
  });

  it.each(['/ai/../other/', '//other.invalid/lesson/', '/lesson/?query', '/a\\b/'])
  ('rejects a non-canonical input pathname: %s', pathname => {
    expect(() => buildLessonCatalog([route('ai/module-a.md', pathname)])).toThrow('Invalid lesson pathname');
  });
});
