import { createHash } from 'node:crypto';
import { readFileSync, readdirSync, realpathSync, statSync } from 'node:fs';
import { isAbsolute, relative, resolve, sep } from 'node:path';
import { buildDocumentRouteSet } from './document-route-set.mjs';

export class UnsupportedDocumentSource extends Error {}
const SOURCE_PREFIX = 'src/content/docs/';
const fail = (message) => { throw new UnsupportedDocumentSource(message); };
const hash = (path) => createHash('sha256').update(readFileSync(path)).digest('hex');
const isInside = (root, path) => {
  const value = relative(root, path);
  return value !== '..' && !value.startsWith(`..${sep}`) && !isAbsolute(value);
};

function docsRoot(checkoutRoot) {
  if (typeof checkoutRoot !== 'string' || !checkoutRoot) fail('checkout root must be text');
  try {
    const checkout = realpathSync(checkoutRoot);
    const root = realpathSync(resolve(checkout, 'src/content/docs'));
    if (!statSync(root).isDirectory()) fail('content docs root is not a directory');
    if (!isInside(checkout, root)) fail('content docs root escapes checkout');
    return { checkout, root };
  } catch (error) {
    if (error instanceof UnsupportedDocumentSource) throw error;
    fail('content docs root is missing');
  }
}

function sourceFile({ checkout, root }, source) {
  if (!source.startsWith(SOURCE_PREFIX)) fail(`source must start with ${SOURCE_PREFIX}: ${source}`);
  if (!/\.mdx?$/i.test(source)) fail(`source is not MD/MDX: ${source}`);
  let path;
  try { path = realpathSync(resolve(checkout, source)); } catch { fail(`source is missing: ${source}`); }
  if (!isInside(root, path)) fail(`source escapes content root: ${source}`);
  if (!statSync(path).isFile()) fail(`source is not a file: ${source}`);
  return path;
}

function concreteSources(root, directory = root, found = new Set()) {
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    const path = resolve(directory, entry.name);
    if (entry.isSymbolicLink()) fail(`content docs contains symlink: ${relative(root, path).split(sep).join('/')}`);
    if (entry.isDirectory()) concreteSources(root, path, found);
    else if (entry.isFile() && /\.mdx?$/i.test(entry.name)) found.add(`${SOURCE_PREFIX}${relative(root, path).split(sep).join('/')}`);
  }
  return found;
}

/** Compare manifest source-hash metadata with a checkout; this does not prove an immutable snapshot. */
export function validateDocumentSources(manifest, checkoutRoot) {
  const routeSet = buildDocumentRouteSet(manifest);
  const root = docsRoot(checkoutRoot);
  const represented = new Set();
  for (const [source, primary] of routeSet.primaryBySource) {
    const actual = hash(sourceFile(root, source));
    if (actual !== primary.sourceSha256) fail(`stale source bytes: ${source}`);
    represented.add(source);
  }
  for (const source of concreteSources(root.root)) {
    if (!represented.has(source)) fail(`missing source coverage: ${source}`);
  }
  return { sourceCount: represented.size, fallbackCount: routeSet.fallbacks.length };
}
