import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { routes } from '#kubedojo-quality-starlight-routing';
import { formatCanonical } from '#kubedojo-quality-starlight-canonical';
import { slugToPathname } from '#kubedojo-quality-starlight-slugs';
import project from 'virtual:starlight/project-context';
import manifestConfig from 'virtual:kubedojo-quality-route-manifest-config';
import { runtimeUrlFromPathname } from './route-manifest-integration.mjs';

const configValue = manifestConfig as {
  schemaVersion: number;
  site: string | null;
  base: string;
  trailingSlash: 'always' | 'never' | 'ignore';
  buildFormat: 'directory' | 'file' | 'preserve';
  redirects: { source: string; target: string; status: number | null }[];
};

const unsupported = (reason: string): never => {
  throw new Error(`KubeDojo route manifest unsupported: ${reason}`);
};

const sourceHashes = new Map<string, string>();

function hashSource(source: string) {
  const known = sourceHashes.get(source);
  if (known) return known;
  const root = new URL(project.root);
  if (root.protocol !== 'file:') unsupported('Starlight project root is not file-based');
  let bytes: Buffer;
  try {
    bytes = readFileSync(resolve(fileURLToPath(root), source));
  } catch (error) {
    throw new Error(`KubeDojo route manifest cannot hash Starlight source: ${source}`, { cause: error });
  }
  const hash = createHash('sha256').update(bytes).digest('hex');
  sourceHashes.set(source, hash);
  return hash;
}

function config() {
  const value = configValue;
  if (value?.schemaVersion !== 1) unsupported('unknown manifest configuration schema');
  if (!value.site || value.buildFormat !== 'directory') unsupported('site and directory build format are required');
  if (!['always', 'never', 'ignore'].includes(value.trailingSlash)) unsupported('unknown trailingSlash policy');
  if (typeof value.base !== 'string' || !value.base.startsWith('/')) unsupported('base must be root-relative');
  return value;
}

function routeRecord(route: (typeof routes)[number], value: ReturnType<typeof config>) {
  if (typeof route?.id !== 'string' || typeof route.entry?.filePath !== 'string' || !route.entry.filePath) {
    unsupported('Starlight route is missing an id or source mapping');
  }
  const source = route.entry.filePath;
  if (source.startsWith('/') || source.split('/').includes('..')) unsupported(`Starlight source is not site-relative: ${source}`);
  const url = runtimeUrlFromPathname(value.site, value.base, slugToPathname(route.id));
  const canonical = formatCanonical(url.href, { format: value.buildFormat, trailingSlash: value.trailingSlash });
  return { id: route.id, url: canonical, pathname: new URL(canonical).pathname, source, sourceSha256: hashSource(source), isFallback: route.isFallback === true, locale: route.locale ?? null, lang: route.lang ?? null };
}

function collisionSummary(records: ReturnType<typeof routeRecord>[]) {
  const groups = new Map<string, ReturnType<typeof routeRecord>[]>();
  for (const record of records) groups.set(record.pathname, [...(groups.get(record.pathname) ?? []), record]);
  const collisions = [...groups].filter(([, entries]) => entries.length > 1);
  if (!collisions.length) return;
  const listed = collisions.slice(0, 6).map(([pathname, entries]) => `${pathname}: ${entries.slice(0, 3).map(({ id, source, isFallback }) => `${id} (${source}, fallback=${isFallback})`).join(' | ')}`).join('; ');
  return `Starlight route ambiguity in ${collisions.length} canonical pathname(s): ${listed}${collisions.length > 6 ? '; additional collisions omitted' : ''}`;
}

export function GET() {
  const value = config();
  const records = routes.map((route) => routeRecord(route, value));
  const collisions = collisionSummary(records);
  if (collisions) unsupported(collisions);
  const { redirects, schemaVersion: _schemaVersion, ...snapshot } = value;
  return new Response(JSON.stringify({ schemaVersion: 1, scope: 'starlight-document-routes', config: snapshot, routes: records, redirects }, null, 2) + '\n', {
    headers: { 'content-type': 'application/json; charset=utf-8' },
  });
}
