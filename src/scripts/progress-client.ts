import type { Lesson } from './progress-catalog';

let pending: Promise<Lesson[]> | undefined;

/** Cache successful loads per page session; failed requests can be retried. */
export function loadLessonCatalog(): Promise<Lesson[]> {
  return pending ??= fetch(`${import.meta.env.BASE_URL.replace(/\/?$/, '/')}progress-catalog.json`)
    .then(async response => {
      if (!response.ok) throw new Error('Progress catalog is unavailable');
      const value = await response.json();
      if (value?.schemaVersion !== 1 || !Array.isArray(value.lessons)) throw new Error('Invalid progress catalog');
      const ids = new Set<string>();
      const keys = new Set<string>();
      for (const lesson of value.lessons) {
        if (!lesson || typeof lesson.id !== 'string' || !lesson.id || ids.has(lesson.id) ||
          typeof lesson.track !== 'string' || !lesson.track || !['module', 'chapter'].includes(lesson.kind) ||
          !Array.isArray(lesson.keys) || !lesson.keys.length) throw new Error('Invalid progress lesson');
        ids.add(lesson.id);
        for (const key of lesson.keys) {
          if (typeof key !== 'string' || !key || keys.has(key)) throw new Error('Invalid progress route');
          keys.add(key);
        }
      }
      return value.lessons as Lesson[];
    }).catch(error => { pending = undefined; throw error; });
}
