/**
 * KubeDojo Lab Progress — localStorage-based tracking.
 *
 * Schema:
 * {
 *   "kubedojo-labs": {
 *     "cka-2.1-pods": { "status": "completed", "completedAt": "2026-04-01T..." },
 *     "prereq-0.3-first-commands": { "status": "started", "startedAt": "2026-04-01T..." }
 *   }
 * }
 *
 * Migration: When Supabase is added later, this same API surface is preserved.
 * localStorage becomes a cache, Supabase becomes source of truth.
 */

const STORAGE_KEY = 'kubedojo-labs';

export interface LabEntry {
  status: 'started' | 'completed';
  startedAt: string;
  completedAt?: string;
}

export type LabProgress = Record<string, LabEntry>;

function getAll(): LabProgress {
  if (typeof localStorage === 'undefined') return {};
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function saveAll(data: LabProgress): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  } catch {
    // SSR or restricted environment
  }
}

/** Mark a lab as started (no-op if already started or completed). */
export function markStarted(labId: string): void {
  const data = getAll();
  if (data[labId]) return; // already tracked
  data[labId] = {
    status: 'started',
    startedAt: new Date().toISOString(),
  };
  saveAll(data);
}

/** Mark a lab as completed. */
export function markCompleted(labId: string): void {
  const data = getAll();
  data[labId] = {
    status: 'completed',
    startedAt: data[labId]?.startedAt ?? new Date().toISOString(),
    completedAt: new Date().toISOString(),
  };
  saveAll(data);
}

/** Get status of a single lab. */
export function getLabStatus(labId: string): LabEntry | null {
  return getAll()[labId] ?? null;
}

/** Get all progress. */
export function getProgress(): LabProgress {
  return getAll();
}

/** Count completed/total for a track prefix (e.g., "cka-" or "prereq-"). */
export function getTrackProgress(prefix: string): { completed: number; started: number; total: number } {
  const data = getAll();
  let completed = 0;
  let started = 0;
  let total = 0;
  for (const [id, entry] of Object.entries(data)) {
    if (id.startsWith(prefix)) {
      total++;
      if (entry.status === 'completed') completed++;
      else if (entry.status === 'started') started++;
    }
  }
  return { completed, started, total };
}

/** Export all progress as JSON string (for backup/migration). */
export function exportProgress(): string {
  return JSON.stringify(getAll(), null, 2);
}

/** Import progress from JSON string (merges, doesn't overwrite completed). */
export function importProgress(json: string): number {
  const imported: LabProgress = JSON.parse(json);
  const current = getAll();
  let count = 0;
  for (const [id, entry] of Object.entries(imported)) {
    if (!current[id] || (current[id].status === 'started' && entry.status === 'completed')) {
      current[id] = entry;
      count++;
    }
  }
  saveAll(current);
  return count;
}

/** Reset all progress. */
export function resetProgress(): void {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // Fallback: overwrite with empty
    try { localStorage.setItem(STORAGE_KEY, '{}'); } catch { /* noop */ }
  }
}
