import { parseProgress, type ProgressData } from './progress-data';
import type { Lesson } from './progress-catalog';

export const PROGRESS_KEY = 'kubedojo-progress';
export type ProgressStorage = () => Pick<Storage, 'getItem' | 'setItem'>;
export type StateResult =
  | { ok: true; data: ProgressData }
  | { ok: false; reason: 'unavailable' | 'invalid' | 'unknown-lesson' | 'timestamp' | 'write'; raw?: string };

/** The accessor is called inside try: even obtaining window.localStorage can throw. */
export function readSavedProgress(storage: ProgressStorage): StateResult {
  let raw: string | null;
  try { raw = storage().getItem(PROGRESS_KEY); }
  catch { return { ok: false, reason: 'unavailable' }; }
  const parsed = parseProgress(raw);
  return parsed.ok ? parsed : { ok: false, reason: 'invalid', raw: parsed.raw };
}

export function lessonIsComplete(lesson: Lesson, data: ProgressData): boolean {
  return lesson.keys.some(key => Object.hasOwn(data, key));
}

/** Explicit user action. Read fresh before writing; this is not a cross-tab transaction. */
export function setLessonComplete(
  storage: ProgressStorage, catalog: Lesson[], routeKey: string, complete: boolean, timestamp = Date.now(),
): StateResult {
  const lesson = catalog.find(item => item.keys.includes(routeKey));
  if (!lesson) return { ok: false, reason: 'unknown-lesson' };
  if (complete && (!Number.isSafeInteger(timestamp) || timestamp <= 0)) {
    return { ok: false, reason: 'timestamp' };
  }
  const existing = readSavedProgress(storage);
  if (!existing.ok) return existing;
  const entries = new Map(Object.entries(existing.data));
  if (complete) {
    entries.set(routeKey, timestamp);
  } else {
    // Undo the shared lesson, including marks made through its other language routes.
    for (const key of lesson.keys) entries.delete(key);
  }
  const data = Object.fromEntries(entries);
  try { storage().setItem(PROGRESS_KEY, JSON.stringify(data)); }
  catch { return { ok: false, reason: 'write' }; }
  return { ok: true, data };
}
