export class UnsupportedRoute extends TypeError {}

function text(value, label) {
  if (typeof value !== 'string') throw new UnsupportedRoute(`${label} must be text`);
  return value;
}

function parsed(value, label, base) {
  try {
    return new URL(text(value, label), base);
  } catch (error) {
    throw new UnsupportedRoute(`${label} is not a valid URL`, { cause: error });
  }
}

function siteOrigin(value) {
  const origin = parsed(value, 'site origin');
  if (!['http:', 'https:'].includes(origin.protocol) || origin.username || origin.password || origin.search || origin.hash || origin.pathname !== '/') {
    throw new UnsupportedRoute('site origin must be an HTTP(S) origin without a path, query, or fragment');
  }
  return origin;
}

function canonicalSource(value, origin) {
  const source = text(value, 'canonical source');
  if (source.startsWith('//') || (!source.startsWith('/') && !/^[a-z][a-z\d+.-]*:\/\//i.test(source))) {
    throw new UnsupportedRoute('canonical source must be an absolute URL or root-relative path');
  }
  const result = parsed(source, 'canonical source', origin);
  if (!['http:', 'https:'].includes(result.protocol)) throw new UnsupportedRoute('canonical source must be HTTP(S)');
  return result;
}

/** Manifest entries are URL-serialized pathnames; normalization is never a fallback. */
function manifestRoutes(paths, origin) {
  if (typeof paths === 'string' || !paths || typeof paths[Symbol.iterator] !== 'function') throw new UnsupportedRoute('manifest paths must be a non-string iterable');
  const routes = new Set();
  for (const value of paths) {
    const path = text(value, 'manifest route');
    if (!path.startsWith('/') || path.startsWith('//') || path.includes('?') || path.includes('#')) {
      throw new UnsupportedRoute('manifest routes must be root-relative paths');
    }
    const route = parsed(path, 'manifest route', origin);
    if (route.origin !== origin.origin || route.search || route.hash || route.pathname !== path) throw new UnsupportedRoute('manifest route must be a serialized pathname');
    routes.add(route.pathname);
  }
  return routes;
}

/** Resolve one URL; routeExists checks paths only, never anchors or redirect destinations. */
export function resolveRoute(href, canonicalSourceValue, siteOriginValue, knownPaths) {
  const origin = siteOrigin(siteOriginValue);
  const source = canonicalSource(canonicalSourceValue, origin);
  const routes = manifestRoutes(knownPaths, origin);
  const target = parsed(href, 'href', source);
  if (target.protocol === 'mailto:') return { url: target.href, kind: 'mailto', path: null, routeExists: null };
  if (!['http:', 'https:'].includes(target.protocol)) throw new UnsupportedRoute('only HTTP(S) and mailto links are supported');
  const internal = target.origin === origin.origin;
  return { url: target.href, kind: internal ? 'internal' : 'external-http', path: target.pathname, routeExists: internal ? routes.has(target.pathname) : null };
}
