import assert from 'node:assert/strict';
import test from 'node:test';
import { createHash } from 'node:crypto';
import { mkdirSync, mkdtempSync, rmSync, symlinkSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { tmpdir } from 'node:os';
import { validateDocumentSources } from './document-source-validation.mjs';

const hash = (text) => createHash('sha256').update(text).digest('hex');
const source = (path) => `src/content/docs/${path}`;
const route = (source, text, overrides = {}) => ({ id: source.replace(/\.mdx?$/, ''), url: `https://site.test/${source}/`, pathname: `/${source}/`, source, sourceSha256: hash(text), isFallback: false, locale: null, lang: null, ...overrides });
const manifest = (routes) => ({ schemaVersion: 1, scope: 'starlight-document-routes', config: { site: 'https://site.test/', base: '/', trailingSlash: 'always', buildFormat: 'directory' }, routes, redirects: [] });
const fixture = () => {
  const root = mkdtempSync(join(tmpdir(), 'document-source-'));
  const docs = join(root, 'src/content/docs');
  mkdirSync(docs, { recursive: true });
  return { root, docs, write: (source, text) => { mkdirSync(dirname(join(docs, source)), { recursive: true }); writeFileSync(join(docs, source), text); } };
};
const rejects = (fn, pattern) => assert.throws(fn, { name: 'Error', message: pattern });

test('validates concrete EN, UK, and fallback source coverage', () => {
  const f = fixture();
  try {
    f.write('guide.md', 'English'); f.write('uk/guide.md', 'Українська');
    const en = route(source('guide.md'), 'English');
    const fallback = route(source('guide.md'), 'English', { id: 'uk/guide', url: 'https://site.test/uk/guide/', pathname: '/uk/guide/', isFallback: true, locale: 'uk', lang: 'uk' });
    const uk = route(source('uk/guide.md'), 'Українська', { id: 'uk/translated', url: 'https://site.test/uk/translated/', pathname: '/uk/translated/', locale: 'uk', lang: 'uk' });
    assert.deepEqual(validateDocumentSources(manifest([en, fallback, uk]), f.root), { sourceCount: 2, fallbackCount: 1 });
  } finally { rmSync(f.root, { recursive: true, force: true }); }
});

test('rejects changed bytes and missing or unrepresented files', () => {
  const f = fixture();
  try {
    f.write('guide.md', 'before');
    const stale = manifest([route(source('guide.md'), 'before')]);
    f.write('guide.md', 'after');
    rejects(() => validateDocumentSources(stale, f.root), /stale source bytes/);
    rejects(() => validateDocumentSources(manifest([route('guide.md', 'after')]), f.root), /must start with src\/content\/docs/);
    rejects(() => validateDocumentSources(manifest([route(source('missing.md'), 'none')]), f.root), /source is missing/);
    f.write('extra.mdx', 'extra');
    rejects(() => validateDocumentSources(manifest([route(source('guide.md'), 'after')]), f.root), /missing source coverage: src\/content\/docs\/extra.mdx/);
  } finally { rmSync(f.root, { recursive: true, force: true }); }
});

test('rejects an external symlink and non-file source', () => {
  const f = fixture();
  try {
    const outside = join(f.root, 'outside.md'); writeFileSync(outside, 'outside');
    symlinkSync(outside, join(f.docs, 'escape.md'));
    rejects(() => validateDocumentSources(manifest([route(source('escape.md'), 'outside')]), f.root), /escapes content root/);
    mkdirSync(join(f.docs, 'folder.md'));
    rejects(() => validateDocumentSources(manifest([route(source('folder.md'), 'none')]), f.root), /source is not a file/);
  } finally { rmSync(f.root, { recursive: true, force: true }); }
});

test('rejects a docs-root escape and unrepresented symlink entries', () => {
  const f = fixture();
  const outside = mkdtempSync(join(tmpdir(), 'outside-docs-'));
  try {
    rmSync(f.docs, { recursive: true }); symlinkSync(outside, f.docs);
    rejects(() => validateDocumentSources(manifest([]), f.root), /root escapes checkout/);
  } finally { rmSync(f.root, { recursive: true, force: true }); rmSync(outside, { recursive: true, force: true }); }
  const g = fixture();
  try {
    g.write('guide.md', 'guide');
    const outside = join(g.root, 'outside.md'); writeFileSync(outside, 'outside');
    symlinkSync(outside, join(g.docs, 'unrepresented.md'));
    rejects(() => validateDocumentSources(manifest([route(source('guide.md'), 'guide')]), g.root), /contains symlink: unrepresented.md/);
    rmSync(join(g.docs, 'unrepresented.md'));
    const directory = join(g.root, 'outside-dir'); mkdirSync(directory);
    symlinkSync(directory, join(g.docs, 'unrepresented-dir'));
    rejects(() => validateDocumentSources(manifest([route(source('guide.md'), 'guide')]), g.root), /contains symlink: unrepresented-dir/);
  } finally { rmSync(g.root, { recursive: true, force: true }); }
});
