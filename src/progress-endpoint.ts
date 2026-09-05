import type { APIContext } from 'astro';
import { routes } from '#kubedojo-progress-routes';
import { slugToPathname } from '#kubedojo-progress-slugs';
import { formatCanonical } from '#kubedojo-progress-canonical';
import format from 'virtual:kubedojo-progress-format';
import { buildLessonCatalog } from './scripts/progress-catalog';

export function GET(context: APIContext) {
  if (!context.site) throw new Error('Progress catalog requires site metadata');
  const base = import.meta.env.BASE_URL.replace(/\/?$/, '/');
  const lessons = buildLessonCatalog(routes.map(route => {
    const url = new URL(base + slugToPathname(route.id).slice(1), context.site);
    const pathname = new URL(formatCanonical(url.href, format)).pathname;
    return { source: route.entry.filePath, pathname };
  }));
  return new Response(JSON.stringify({ schemaVersion: 1, lessons }), {
    headers: { 'Content-Type': 'application/json' },
  });
}
