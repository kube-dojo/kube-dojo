import { describe, expect, it } from 'vitest';
import { buildLessonCatalog, countLessonProgress } from '../src/scripts/progress-catalog';
import { lessonIsComplete, PROGRESS_KEY, readSavedProgress, setLessonComplete } from '../src/scripts/progress-state';

const catalog = buildLessonCatalog([
  { source: 'src/content/docs/ai/module-1.md', pathname: '/ai/lesson/' },
  { source: 'src/content/docs/uk/ai/module-1.md', pathname: '/uk/ai/lesson/' },
]);
function fixture(initial: string | null, failWrite = false) {
  let raw = initial;
  const writes: string[] = [];
  const storage = () => ({
    getItem(key: string) { expect(key).toBe(PROGRESS_KEY); return raw; },
    setItem(key: string, value: string) {
      expect(key).toBe(PROGRESS_KEY);
      if (failWrite) throw new Error('Quota exceeded');
      writes.push(value); raw = value;
    },
  });
  return { storage, writes, raw: () => raw };
}

describe('shared lesson completion', () => {
  it('reflects a Ukrainian mark in the shared lesson and preserves unrelated keys', () => {
    const f = fixture('{"retired":17}');
    const result = setLessonComplete(f.storage, catalog, 'uk/ai/lesson', true, 100);
    expect(result.ok).toBe(true);
    if (!result.ok) throw new Error('Expected write');
    expect(lessonIsComplete(catalog[0], result.data)).toBe(true);
    expect(countLessonProgress(catalog, Object.keys(result.data))).toMatchObject({ completed: 1, unknownKeys: ['retired'] });
    expect(JSON.parse(f.raw()!)).toEqual({ retired: 17, 'uk/ai/lesson': 100 });
  });

  it('explicit undo removes both language marks but retains other records', () => {
    const f = fixture('{"ai/lesson":1,"uk/ai/lesson":2,"retired":17}');
    expect(setLessonComplete(f.storage, catalog, 'ai/lesson', false)).toEqual({ ok: true, data: { retired: 17 } });
    expect(JSON.parse(f.raw()!)).toEqual({ retired: 17 });
  });

  it('reads fresh state on each operation', () => {
    const f = fixture(null);
    setLessonComplete(f.storage, catalog, 'ai/lesson', true, 100);
    setLessonComplete(f.storage, catalog, 'uk/ai/lesson', true, 101);
    expect(readSavedProgress(f.storage)).toEqual({ ok: true, data: { 'ai/lesson': 100, 'uk/ai/lesson': 101 } });
  });

  it('retains malformed raw data and performs no write', () => {
    const f = fixture('null');
    expect(setLessonComplete(f.storage, catalog, 'ai/lesson', true)).toEqual({ ok: false, reason: 'invalid', raw: 'null' });
    expect(f.writes).toHaveLength(0);
    expect(f.raw()).toBe('null');
  });

  it('reports unavailable storage access and failed persistence', () => {
    expect(readSavedProgress(() => { throw new Error('SecurityError'); })).toEqual({ ok: false, reason: 'unavailable' });
    const f = fixture('{"retired":17}', true);
    expect(setLessonComplete(f.storage, catalog, 'ai/lesson', true)).toEqual({ ok: false, reason: 'write' });
    expect(f.raw()).toBe('{"retired":17}');
  });

  it('refuses non-lessons and invalid completion timestamps without writes', () => {
    const f = fixture(null);
    expect(setLessonComplete(f.storage, catalog, 'progress', true)).toMatchObject({ ok: false, reason: 'unknown-lesson' });
    expect(setLessonComplete(f.storage, catalog, 'ai/lesson', true, NaN)).toMatchObject({ ok: false, reason: 'timestamp' });
    expect(f.writes).toHaveLength(0);
  });
});
