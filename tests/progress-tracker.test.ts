import { describe, it, expect, beforeEach } from 'vitest';

// Mock localStorage since happy-dom's implementation is incomplete
const store: Record<string, string> = {};
const mockStorage = {
  getItem: (key: string) => store[key] ?? null,
  setItem: (key: string, val: string) => { store[key] = val; },
  removeItem: (key: string) => { delete store[key]; },
  clear: () => { for (const k in store) delete store[k]; },
};
Object.defineProperty(globalThis, 'localStorage', { value: mockStorage, writable: true });

const STORAGE_KEY = 'kubedojo-progress';

interface ProgressData {
  [slug: string]: number;
}

function getProgress(): ProgressData {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function saveProgress(data: ProgressData): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
}

function markComplete(slug: string): void {
  const data = getProgress();
  data[slug] = Date.now();
  saveProgress(data);
}

function markIncomplete(slug: string): void {
  const data = getProgress();
  delete data[slug];
  saveProgress(data);
}

function isComplete(slug: string): boolean {
  return slug in getProgress();
}

function exportProgress(): string {
  return JSON.stringify(getProgress(), null, 2);
}

function importProgress(json: string): boolean {
  try {
    const data = JSON.parse(json);
    if (typeof data !== 'object') return false;
    saveProgress(data);
    return true;
  } catch {
    return false;
  }
}

describe('Progress Tracker — Core API', () => {
  beforeEach(() => {
    mockStorage.clear();
  });

  it('returns empty object when no progress', () => {
    expect(getProgress()).toEqual({});
  });

  it('markComplete adds a slug with timestamp', () => {
    const before = Date.now();
    markComplete('k8s/cka/part1/module-1.1');
    const after = Date.now();

    const data = getProgress();
    expect(data['k8s/cka/part1/module-1.1']).toBeGreaterThanOrEqual(before);
    expect(data['k8s/cka/part1/module-1.1']).toBeLessThanOrEqual(after);
  });

  it('isComplete returns true for completed slugs', () => {
    markComplete('test-slug');
    expect(isComplete('test-slug')).toBe(true);
    expect(isComplete('other-slug')).toBe(false);
  });

  it('markIncomplete removes a slug', () => {
    markComplete('test-slug');
    expect(isComplete('test-slug')).toBe(true);

    markIncomplete('test-slug');
    expect(isComplete('test-slug')).toBe(false);
  });

  it('markIncomplete on non-existent slug is safe', () => {
    markIncomplete('does-not-exist');
    expect(getProgress()).toEqual({});
  });

  it('multiple slugs tracked independently', () => {
    markComplete('slug-a');
    markComplete('slug-b');
    markComplete('slug-c');

    expect(isComplete('slug-a')).toBe(true);
    expect(isComplete('slug-b')).toBe(true);
    expect(isComplete('slug-c')).toBe(true);

    markIncomplete('slug-b');
    expect(isComplete('slug-a')).toBe(true);
    expect(isComplete('slug-b')).toBe(false);
    expect(isComplete('slug-c')).toBe(true);
  });

  it('exportProgress returns formatted JSON', () => {
    markComplete('test-slug');
    const exported = exportProgress();
    const parsed = JSON.parse(exported);
    expect(parsed).toHaveProperty('test-slug');
  });

  it('importProgress loads valid JSON', () => {
    const data = { 'imported-slug': 1234567890 };
    expect(importProgress(JSON.stringify(data))).toBe(true);
    expect(isComplete('imported-slug')).toBe(true);
  });

  it('importProgress rejects invalid JSON', () => {
    expect(importProgress('not json')).toBe(false);
  });

  it('importProgress rejects non-object JSON', () => {
    expect(importProgress('"just a string"')).toBe(false);
    expect(importProgress('42')).toBe(false);
  });

  it('importProgress overwrites existing data', () => {
    markComplete('old-slug');
    importProgress(JSON.stringify({ 'new-slug': 999 }));

    expect(isComplete('old-slug')).toBe(false);
    expect(isComplete('new-slug')).toBe(true);
  });

  it('handles corrupted localStorage gracefully', () => {
    localStorage.setItem(STORAGE_KEY, 'not valid json{{{');
    expect(getProgress()).toEqual({});
  });
});
