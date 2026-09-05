export interface Lesson {
  id: string;
  track: string;
  kind: 'module' | 'chapter';
  keys: string[];
}
export interface LessonRoute { source: string; pathname: string }

/** Use source identity for translations, but actual runtime paths for saved keys. */
export function buildLessonCatalog(routes: LessonRoute[]): Lesson[] {
  const lessons = new Map<string, Lesson>();
  const seenPaths = new Set<string>();
  for (const { source, pathname } of routes) {
    if (!pathname.startsWith('/') || pathname.startsWith('//') || /[?#]/.test(pathname) ||
      new URL(pathname, 'https://catalog.invalid').pathname !== pathname) {
      throw new Error(`Invalid lesson pathname: ${pathname}`);
    }
    if (seenPaths.has(pathname)) throw new Error(`Duplicate lesson pathname: ${pathname}`);
    seenPaths.add(pathname);
    if (!source.startsWith('src/content/docs/')) continue;
    const relative = source.slice('src/content/docs/'.length);
    if (relative.split('/').some(part => !part || part === '.' || part === '..')) {
      throw new Error(`Invalid lesson source: ${source}`);
    }
    if (/\.staging\./.test(relative) || !/\.(md|mdx|markdown|mdown|mkdn|mkd|mdwn)$/.test(relative)) continue;
    const id = relative.replace(/^uk\//, '').replace(/\.(md|mdx|markdown|mdown|mkdn|mkd|mdwn)$/, '');
    const parts = id.split('/');
    const name = parts.at(-1)!;
    const kind = name.startsWith('module-') ? 'module'
      : parts[0] === 'ai-history' && name.startsWith('ch-') ? 'chapter' : null;
    if (!kind || parts.length < 2) continue;
    const lesson = lessons.get(id) ?? { id, track: parts[0], kind, keys: [] };
    const key = pathname.replace(/^\/|\/$/g, '');
    // Slash variants can refer to the same saved key; never count them twice.
    if (!lesson.keys.includes(key)) lesson.keys.push(key);
    lessons.set(id, lesson);
  }
  const owners = new Map<string, string>();
  for (const lesson of lessons.values()) {
    for (const key of lesson.keys) {
      const owner = owners.get(key);
      if (owner && owner !== lesson.id) throw new Error(`Ambiguous lesson key: ${key}`);
      owners.set(key, lesson.id);
    }
    lesson.keys.sort();
  }
  return [...lessons.values()].sort((a, b) => a.id.localeCompare(b.id));
}

/** Pass keys only after progress-data validation; completion is self-reported. */
export function countLessonProgress(catalog: Lesson[], completedKeys: Iterable<string>) {
  const keys = new Set(completedKeys);
  const recognized = new Set(catalog.flatMap(lesson => lesson.keys));
  const tracks: Record<string, { total: number; completed: number }> = Object.create(null);
  let completed = 0;
  for (const lesson of catalog) {
    const row = tracks[lesson.track] ??= { total: 0, completed: 0 };
    row.total++;
    if (lesson.keys.some(key => keys.has(key))) { row.completed++; completed++; }
  }
  return { total: catalog.length, completed, tracks, unknownKeys: [...keys].filter(key => !recognized.has(key)) };
}
