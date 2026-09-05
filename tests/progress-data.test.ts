import { describe, expect, it } from 'vitest';
import { parseProgress, prepareProgressImport } from '../src/scripts/progress-data';

describe('legacy progress validation', () => {
  it('distinguishes absent storage from malformed storage', () => {
    expect(parseProgress(null)).toEqual({ ok: true, data: {} });
    expect(parseProgress('')).toEqual({ ok: false, reason: 'json', raw: '' });
  });

  it.each(['null', '[]', 'true', '42', '"lesson"'])('rejects a non-map: %s', raw => {
    expect(parseProgress(raw)).toEqual({ ok: false, reason: 'shape', raw });
  });

  it.each(['true', 'null', '"123"', '0', '-1', '1.5', '1e400', '9007199254740992', '{}', '[]'])
  ('rejects an invalid timestamp without salvaging partial data: %s', timestamp => {
    const raw = `{"known":123,"bad":${timestamp}}`;
    expect(parseProgress(raw)).toEqual({ ok: false, reason: 'entry', raw });
  });

  it('rejects an empty route key', () => {
    expect(parseProgress('{"":123}')).toMatchObject({ ok: false, reason: 'entry' });
  });

  it('preserves unknown, retired and language-specific keys without rewriting', () => {
    const data = { 'retired/lesson': 1, 'uk/ai/lesson': 2, 'ai/lesson': 3 };
    expect(parseProgress(JSON.stringify(data))).toEqual({ ok: true, data });
  });
});

describe('non-destructive import preparation', () => {
  it('merges both maps, retaining the newest timestamp for an exact key', () => {
    const result = prepareProgressImport('{"old":2,"same":8}', '{"new":3,"same":4}');
    expect(result).toEqual({
      ok: true, data: { old: 2, same: 8, new: 3 }, serialized: '{"old":2,"same":8,"new":3}',
    });
    expect(prepareProgressImport(null, '{"new":3}')).toMatchObject({ ok: true, data: { new: 3 } });
  });

  it('does not replace unreadable existing data with an otherwise valid import', () => {
    expect(prepareProgressImport('broken backup', '{"new":3}')).toEqual({
      ok: false, source: 'existing', error: { ok: false, reason: 'json', raw: 'broken backup' },
    });
  });

  it('returns no writable replacement for an invalid import', () => {
    const result = prepareProgressImport('{"old":2}', '{"new":false}');
    expect(result).toMatchObject({ ok: false, source: 'import' });
    expect(result).not.toHaveProperty('serialized');
  });

  it('keeps prototype-like keys as data through merge and export', () => {
    const result = prepareProgressImport('{"__proto__":2}', '{"constructor":3,"__proto__":4}');
    expect(result.ok).toBe(true);
    if (!result.ok) throw new Error('Expected a valid legacy map');
    expect(Object.getPrototypeOf(result.data)).toBe(Object.prototype);
    expect(Object.hasOwn(result.data, '__proto__')).toBe(true);
    expect(JSON.parse(result.serialized)).toEqual(JSON.parse('{"__proto__":4,"constructor":3}'));
  });
});
