import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  markStarted,
  markCompleted,
  getLabStatus,
  getProgress,
  getTrackProgress,
  exportProgress,
  importProgress,
  resetProgress,
} from '../src/components/LabProgress';

// Mock localStorage for happy-dom
const store: Record<string, string> = {};
const localStorageMock = {
  getItem: vi.fn((key: string) => store[key] ?? null),
  setItem: vi.fn((key: string, value: string) => { store[key] = value; }),
  removeItem: vi.fn((key: string) => { delete store[key]; }),
  clear: vi.fn(() => { Object.keys(store).forEach(k => delete store[k]); }),
};
Object.defineProperty(globalThis, 'localStorage', { value: localStorageMock, writable: true });

describe('LabProgress', () => {
  beforeEach(() => {
    Object.keys(store).forEach(k => delete store[k]);
    vi.clearAllMocks();
  });

  describe('markStarted', () => {
    it('creates a started entry', () => {
      markStarted('cka-2.1-pods');
      const status = getLabStatus('cka-2.1-pods');
      expect(status).not.toBeNull();
      expect(status!.status).toBe('started');
      expect(status!.startedAt).toBeTruthy();
      expect(status!.completedAt).toBeUndefined();
    });

    it('does not overwrite existing entry', () => {
      markStarted('cka-2.1-pods');
      const first = getLabStatus('cka-2.1-pods')!.startedAt;
      markStarted('cka-2.1-pods');
      expect(getLabStatus('cka-2.1-pods')!.startedAt).toBe(first);
    });

    it('does not overwrite completed entry', () => {
      markCompleted('cka-2.1-pods');
      markStarted('cka-2.1-pods');
      expect(getLabStatus('cka-2.1-pods')!.status).toBe('completed');
    });
  });

  describe('markCompleted', () => {
    it('creates a completed entry', () => {
      markCompleted('cka-2.1-pods');
      const status = getLabStatus('cka-2.1-pods');
      expect(status!.status).toBe('completed');
      expect(status!.completedAt).toBeTruthy();
    });

    it('preserves startedAt when completing a started lab', () => {
      markStarted('cka-2.1-pods');
      const startedAt = getLabStatus('cka-2.1-pods')!.startedAt;
      markCompleted('cka-2.1-pods');
      expect(getLabStatus('cka-2.1-pods')!.startedAt).toBe(startedAt);
    });

    it('sets startedAt if not previously started', () => {
      markCompleted('cka-2.1-pods');
      expect(getLabStatus('cka-2.1-pods')!.startedAt).toBeTruthy();
    });
  });

  describe('getLabStatus', () => {
    it('returns null for unknown lab', () => {
      expect(getLabStatus('nonexistent')).toBeNull();
    });
  });

  describe('getProgress', () => {
    it('returns empty object when no progress', () => {
      expect(getProgress()).toEqual({});
    });

    it('returns all entries', () => {
      markStarted('a');
      markCompleted('b');
      const progress = getProgress();
      expect(Object.keys(progress)).toHaveLength(2);
    });
  });

  describe('getTrackProgress', () => {
    it('counts by prefix', () => {
      markStarted('cka-1.1-foo');
      markCompleted('cka-1.2-bar');
      markCompleted('cka-2.1-baz');
      markStarted('prereq-0.3-test');

      const cka = getTrackProgress('cka-');
      expect(cka.completed).toBe(2);
      expect(cka.started).toBe(1);
      expect(cka.total).toBe(3);

      const prereq = getTrackProgress('prereq-');
      expect(prereq.started).toBe(1);
      expect(prereq.total).toBe(1);
    });

    it('returns zeros for unknown prefix', () => {
      const result = getTrackProgress('nonexistent-');
      expect(result).toEqual({ completed: 0, started: 0, total: 0 });
    });
  });

  describe('exportProgress / importProgress', () => {
    it('exports as JSON', () => {
      markCompleted('cka-2.1-pods');
      const json = exportProgress();
      const parsed = JSON.parse(json);
      expect(parsed['cka-2.1-pods'].status).toBe('completed');
    });

    it('imports and merges', () => {
      markStarted('cka-2.1-pods');
      const imported = JSON.stringify({
        'cka-2.1-pods': { status: 'completed', startedAt: '2026-01-01', completedAt: '2026-01-01' },
        'cka-2.2-deployments': { status: 'completed', startedAt: '2026-01-01', completedAt: '2026-01-01' },
      });
      const count = importProgress(imported);
      expect(count).toBe(2); // upgraded started→completed + new entry
      expect(getLabStatus('cka-2.1-pods')!.status).toBe('completed');
      expect(getLabStatus('cka-2.2-deployments')!.status).toBe('completed');
    });

    it('does not downgrade completed to started', () => {
      markCompleted('cka-2.1-pods');
      const imported = JSON.stringify({
        'cka-2.1-pods': { status: 'started', startedAt: '2026-01-01' },
      });
      const count = importProgress(imported);
      expect(count).toBe(0);
      expect(getLabStatus('cka-2.1-pods')!.status).toBe('completed');
    });
  });

  describe('resetProgress', () => {
    it('clears all progress', () => {
      markCompleted('a');
      markCompleted('b');
      resetProgress();
      expect(getProgress()).toEqual({});
    });
  });
});
