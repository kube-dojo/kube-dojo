import { afterEach, expect, it, vi } from 'vitest';

afterEach(() => { vi.unstubAllGlobals(); vi.resetModules(); });

it('caches successful requests and retains runtime routes', async () => {
  const lessons = [{ id: 'ai/module-a', track: 'ai', kind: 'module', keys: ['ai/a', 'uk/ai/a'] }];
  const fetcher = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ schemaVersion: 1, lessons }) });
  vi.stubGlobal('fetch', fetcher);
  const { loadLessonCatalog } = await import('../src/scripts/progress-client');
  expect(await loadLessonCatalog()).toEqual(lessons);
  expect(await loadLessonCatalog()).toEqual(lessons);
  expect(fetcher).toHaveBeenCalledTimes(1);
  expect(fetcher).toHaveBeenCalledWith('/progress-catalog.json');
});

it('allows retry after failure and rejects conflicting route owners', async () => {
  const lesson = { id: 'ai/module-a', track: 'ai', kind: 'module', keys: ['ai/a'] };
  vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce({ ok: false }).mockResolvedValueOnce({
    ok: true, json: async () => ({ schemaVersion: 1, lessons: [lesson, { ...lesson, id: 'ai/module-b' }] }),
  }));
  const { loadLessonCatalog } = await import('../src/scripts/progress-client');
  await expect(loadLessonCatalog()).rejects.toThrow('unavailable');
  await expect(loadLessonCatalog()).rejects.toThrow('Invalid progress route');
});
