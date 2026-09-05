import { prepareProgressImport } from './progress-data';
import { PROGRESS_KEY } from './progress-state';

function message(text: string): void {
  const target = document.getElementById('kd-progress-actions-status');
  if (target) target.textContent = text;
}
function changed(): void {
  document.dispatchEvent(new Event('kubedojo:progress-change'));
}

/** Report malformed existing data instead of silently replacing it. */
export function mergeProgressText(raw: string): boolean {
  try {
    const result = prepareProgressImport(window.localStorage.getItem(PROGRESS_KEY), raw);
    if (!result.ok) {
      message(result.source === 'existing'
        ? 'Existing progress is invalid. Export the original backup before resetting or repairing it.'
        : 'Invalid progress file. Existing progress was not changed.');
      return false;
    }
    window.localStorage.setItem(PROGRESS_KEY, result.serialized);
    message('Progress imported. Existing entries were retained; later timestamps win duplicate entries.');
    changed();
    return true;
  } catch {
    message('Progress could not be imported. Browser storage may be unavailable or full.');
    return false;
  }
}

export function initProgressActions(): void {
  const exportButton = document.getElementById('kd-export-btn');
  if (!exportButton || exportButton.dataset.progressBound) return;
  exportButton.dataset.progressBound = 'true';
  exportButton.addEventListener('click', () => {
    try {
      // Preserve the original bytes, including malformed JSON, for recovery.
      const raw = window.localStorage.getItem(PROGRESS_KEY) ?? '{}';
      const url = URL.createObjectURL(new Blob([raw], { type: 'application/json' }));
      const link = document.createElement('a');
      link.href = url;
      link.download = 'kubedojo-progress-' + new Date().toISOString().slice(0, 10) + '.json';
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      message('Original backup download requested.');
    } catch { message('Backup could not be read or downloaded. Existing data was not changed.'); }
  });
  const input = document.getElementById('kd-import-input') as HTMLInputElement | null;
  input?.addEventListener('change', async () => {
    const file = input.files?.[0];
    if (!file) return;
    try { mergeProgressText(await file.text()); }
    catch { message('The selected file could not be read. Existing progress was not changed.'); }
    finally { input.value = ''; }
  });
  const resetButton = document.getElementById('kd-clear-btn');
  resetButton?.addEventListener('click', () => {
    const target = document.getElementById('kd-progress-actions-status');
    if (!target) return;
    message('Remove all saved progress? Export a backup first if you want to restore it later. ');
    const confirm = document.createElement('button');
    confirm.id = 'kd-progress-reset-confirm';
    confirm.textContent = 'Confirm reset';
    const cancel = document.createElement('button');
    cancel.textContent = 'Cancel reset';
    cancel.addEventListener('click', () => { message('Reset cancelled.'); resetButton.focus(); });
    confirm.addEventListener('click', () => {
      try {
        window.localStorage.removeItem(PROGRESS_KEY);
        message('Saved progress removed from this browser.');
        changed();
      } catch { message('Progress could not be reset. Browser storage is unavailable.'); }
      resetButton.focus();
    });
    target.append(confirm, ' ', cancel);
    cancel.focus();
  });
}

if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initProgressActions);
else initProgressActions();
document.addEventListener('astro:page-load', initProgressActions);
