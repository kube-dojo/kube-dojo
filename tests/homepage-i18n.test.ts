import { describe, it, expect } from 'vitest';
import { translations } from '../src/i18n/homepage';
import type { HomepageStrings } from '../src/i18n/homepage';

describe('Homepage translations', () => {
  const locales = Object.keys(translations);

  it('has at least en and uk locales', () => {
    expect(locales).toContain('en');
    expect(locales).toContain('uk');
  });

  it('all locales have the same keys', () => {
    const enKeys = Object.keys(translations.en).sort();
    for (const locale of locales) {
      const keys = Object.keys(translations[locale]).sort();
      expect(keys).toEqual(enKeys);
    }
  });

  it('no locale has empty strings (except prefix)', () => {
    const allowEmpty = ['prefix']; // en prefix is intentionally ''
    for (const locale of locales) {
      const t = translations[locale];
      for (const [key, val] of Object.entries(t)) {
        if (typeof val === 'string' && !allowEmpty.includes(key)) {
          expect(val.length, `${locale}.${key} is empty`).toBeGreaterThan(0);
        }
      }
    }
  });

  it('whereRows has the same number of entries across locales', () => {
    const enCount = translations.en.whereRows.length;
    for (const locale of locales) {
      expect(translations[locale].whereRows.length, `${locale} whereRows count`).toBe(enCount);
    }
  });

  it('whereRows have valid [desc, label, href] tuples', () => {
    for (const locale of locales) {
      for (const row of translations[locale].whereRows) {
        expect(row).toHaveLength(3);
        expect(row[2], `${locale} href should start with /`).toMatch(/^\//);
      }
    }
  });

  it('uk locale uses correct prefix /uk', () => {
    expect(translations.uk.prefix).toBe('/uk');
    expect(translations.uk.langSwitchHref).toBe('/');
  });

  it('en locale uses empty prefix', () => {
    expect(translations.en.prefix).toBe('');
    expect(translations.en.langSwitchHref).toBe('/uk/');
  });

  it('uk whereRows hrefs include /uk/ prefix', () => {
    for (const row of translations.uk.whereRows) {
      expect(row[2], `UK href "${row[2]}" should start with /uk/`).toMatch(/^\/uk\//);
    }
  });

  it('en whereRows hrefs do not include /uk/ prefix', () => {
    for (const row of translations.en.whereRows) {
      expect(row[2], `EN href "${row[2]}" should not start with /uk/`).not.toMatch(/^\/uk\//);
    }
  });

  it('no Russicisms in Ukrainian text', () => {
    const russicisms = /[ыёъэ]/;
    const t = translations.uk;
    for (const [key, val] of Object.entries(t)) {
      if (typeof val === 'string') {
        expect(val, `uk.${key} contains Russicism`).not.toMatch(russicisms);
      }
    }
  });
});
