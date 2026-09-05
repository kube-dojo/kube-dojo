import assert from 'node:assert/strict';
import test from 'node:test';
import { ROUTE_MANIFEST_ENV, ROUTE_MANIFEST_PATTERN, routeManifestIntegration, runtimeUrlFromPathname } from './route-manifest-integration.mjs';

const config = { site: 'https://site.test/contained-path/', base: '/docs/', trailingSlash: 'always', build: { format: 'directory' }, redirects: { '/old/': '/new/' } };

test('does not change standard builds', () => {
  const prior = process.env[ROUTE_MANIFEST_ENV];
  delete process.env[ROUTE_MANIFEST_ENV];
  const hook = routeManifestIntegration().hooks['astro:config:setup'];
  let calls = 0;
  hook({ config, injectRoute: () => calls++, updateConfig: () => calls++ });
  if (prior === undefined) delete process.env[ROUTE_MANIFEST_ENV]; else process.env[ROUTE_MANIFEST_ENV] = prior;
  assert.equal(calls, 0);
});

test('enabled build injects the audit endpoint and exact resolved config', () => {
  const prior = process.env[ROUTE_MANIFEST_ENV];
  process.env[ROUTE_MANIFEST_ENV] = '1';
  const integration = routeManifestIntegration();
  const hook = integration.hooks['astro:config:setup'];
  let update, route;
  hook({ config, updateConfig: (value) => update = value, injectRoute: (value) => route = value });
  integration.hooks['astro:config:done']({ config });
  if (prior === undefined) delete process.env[ROUTE_MANIFEST_ENV]; else process.env[ROUTE_MANIFEST_ENV] = prior;
  assert.deepEqual(route.pattern, ROUTE_MANIFEST_PATTERN);
  assert.equal(route.prerender, true);
  const source = update.vite.plugins[0].load('\0virtual:kubedojo-quality-route-manifest-config');
  const snapshot = JSON.parse(source.replace('export default ', ''));
  assert.deepEqual(snapshot, { schemaVersion: 1, site: 'https://site.test/contained-path/', base: '/docs/', trailingSlash: 'always', buildFormat: 'directory', redirects: [{ source: '/old/', target: '/new/', status: null }] });
  assert.deepEqual(Object.keys(update.vite.resolve.alias).sort(), ['#kubedojo-quality-starlight-canonical', '#kubedojo-quality-starlight-routing', '#kubedojo-quality-starlight-slugs']);
});

test('canonical runtime pathname stays absolute when site has a path and base changes', () => {
  assert.equal(runtimeUrlFromPathname('https://site.test/contained-path/', '/docs/', '/uk/lesson/').href, 'https://site.test/docs/uk/lesson/');
});
