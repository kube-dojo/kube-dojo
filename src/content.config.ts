import { defineCollection } from 'astro:content';
import { docsLoader } from '@astrojs/starlight/loaders';
import { docsSchema } from '@astrojs/starlight/schema';
import { z } from 'astro:content';

export const collections = {
  docs: defineCollection({
    loader: docsLoader(),
    schema: docsSchema({
      extend: z.object({
        lab: z.object({
          id: z.string(),
          url: z.string().url(),
          duration: z.string(),
          difficulty: z.enum(['beginner', 'intermediate', 'advanced']),
          environment: z.enum(['ubuntu', 'kubernetes']),
        }).optional(),
      }),
    }),
  }),
};
