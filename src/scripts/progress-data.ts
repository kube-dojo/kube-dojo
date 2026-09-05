/** Legacy route → completion-time records. Keys are retained, not catalog-filtered. */
export type ProgressData = Record<string, number>;
export type ProgressResult =
  | { ok: true; data: ProgressData }
  | { ok: false; reason: 'json' | 'shape' | 'entry'; raw: string };

/** A failed read must not become an empty record that callers then overwrite. */
export function parseProgress(raw: string | null): ProgressResult {
  if (raw === null) return { ok: true, data: {} };
  let value: unknown;
  try {
    value = JSON.parse(raw);
  } catch {
    return { ok: false, reason: 'json', raw };
  }
  if (value === null || typeof value !== 'object' || Array.isArray(value)) {
    return { ok: false, reason: 'shape', raw };
  }
  const entries = Object.entries(value);
  if (entries.some(([key, timestamp]) =>
    key.length === 0 || typeof timestamp !== 'number' ||
    !Number.isSafeInteger(timestamp) || timestamp <= 0)) {
    return { ok: false, reason: 'entry', raw };
  }
  // fromEntries treats even "__proto__" as an own data property.
  return { ok: true, data: Object.fromEntries(entries) };
}

export type ProgressMergeResult =
  | { ok: true; data: ProgressData; serialized: string }
  | { ok: false; source: 'existing' | 'import'; error: Extract<ProgressResult, { ok: false }> };

/** Pure preparation: callers write only a successful result, reporting write failures. */
export function prepareProgressImport(existingRaw: string | null, importedRaw: string): ProgressMergeResult {
  const existing = parseProgress(existingRaw);
  if (!existing.ok) return { ok: false, source: 'existing', error: existing };
  const imported = parseProgress(importedRaw);
  if (!imported.ok) return { ok: false, source: 'import', error: imported };
  const entries = new Map(Object.entries(existing.data));
  for (const [key, timestamp] of Object.entries(imported.data)) {
    entries.set(key, Math.max(entries.get(key) ?? 0, timestamp));
  }
  const data = Object.fromEntries(entries);
  return { ok: true, data, serialized: JSON.stringify(data) };
}
