import { defineCollection } from 'astro:content';
import { glob, type LoaderContext } from 'astro/loaders';
import { docsSchema } from '@astrojs/starlight/schema';
import { z } from 'astro:content';

const docsExtensions = ['markdown', 'mdown', 'mkdn', 'mkd', 'mdwn', 'md', 'mdx'];
// `.staging.md` is gitignored ephemera from older pipelines; the loader
// pattern still excludes them defensively until the leftover files are
// audited and removed.
const docsPattern = [
  `**/[^_]*.{${docsExtensions.join(',')}}`,
  `!**/*.staging.{${docsExtensions.join(',')}}`,
];

function isStagingDoc(path: string): boolean {
  return path.includes('.staging.');
}

function withFilteredWatcher(context: LoaderContext): LoaderContext {
  if (!context.watcher) return context;

  const watcher = context.watcher;
  return {
    ...context,
    watcher: {
      add(...args) {
        watcher.add(...args);
        return watcher;
      },
      on(event, callback) {
        if (event === 'add' || event === 'change' || event === 'unlink') {
          return watcher.on(event, ((path: string) => {
            if (isStagingDoc(path)) return;
            return callback(path);
          }) as typeof callback);
        }
        return watcher.on(event, callback);
      },
    } as typeof watcher,
  };
}

const starlightDocsLoader = {
  name: 'starlight-docs-loader',
  load: (context) =>
    glob({
      base: new URL('content/docs/', context.config.srcDir),
      pattern: docsPattern,
      // The dev server already stores parsed frontmatter plus rendered output.
      // Dropping raw source bodies reduces the content-layer memory footprint.
      retainBody: false,
    }).load(withFilteredWatcher(context)),
};

export const collections = {
  docs: defineCollection({
    loader: starlightDocsLoader,
    schema: docsSchema({
      extend: z.object({
        lab: z.object({
          id: z.string(),
          url: z.string().url(),
          duration: z.string(),
          difficulty: z.enum(['beginner', 'intermediate', 'advanced']),
          environment: z.enum(['ubuntu', 'kubernetes', 'centos']),
        }).optional(),
      }),
    }),
  }),
};
