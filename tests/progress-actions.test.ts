import { expect, it, vi } from 'vitest';
import { initProgressActions, mergeProgressText } from '../src/scripts/progress-actions';

it('merges valid imports, preserves invalid originals, and requires explicit reset confirmation', () => {
  let raw: string | null = '{"retired":10}';
  vi.stubGlobal('localStorage', {
    getItem: () => raw,
    setItem: (_key: string, value: string) => { raw = value; },
    removeItem: () => { raw = null; },
  });
  document.body.innerHTML = '<button id="kd-export-btn"></button><input id="kd-import-input" type="file"><button id="kd-clear-btn"></button><p id="kd-progress-actions-status" role="status"></p>';
  initProgressActions();
  initProgressActions();
  expect(mergeProgressText('{"ai/module":11}')).toBe(true);
  expect(JSON.parse(raw!)).toEqual({ retired: 10, 'ai/module': 11 });
  expect(mergeProgressText('null')).toBe(false);
  expect(JSON.parse(raw!)).toEqual({ retired: 10, 'ai/module': 11 });
  raw = 'invalid original';
  expect(mergeProgressText('{"new":12}')).toBe(false);
  expect(raw).toBe('invalid original');
  expect(document.getElementById('kd-progress-actions-status')?.textContent).toContain('Export the original backup');
  document.getElementById('kd-clear-btn')!.click();
  expect(raw).toBe('invalid original');
  const cancel = document.querySelector<HTMLButtonElement>('#kd-progress-actions-status button:last-child')!;
  expect(document.activeElement).toBe(cancel);
  cancel.click();
  expect(raw).toBe('invalid original');
  document.getElementById('kd-clear-btn')!.click();
  document.getElementById('kd-progress-reset-confirm')!.click();
  expect(raw).toBeNull();
  expect(document.activeElement).toBe(document.getElementById('kd-clear-btn'));
  vi.unstubAllGlobals();
});

it('passes the exact original malformed text to the backup download', async () => {
  const original = '  invalid original\n';
  let captured: Blob | undefined;
  vi.stubGlobal('localStorage', { getItem: () => original });
  vi.stubGlobal('URL', class extends URL {
    static createObjectURL(blob: Blob) { captured = blob; return 'blob:progress-test'; }
    static revokeObjectURL() {}
  });
  const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
  document.body.innerHTML = '<button id="kd-export-btn"></button><p id="kd-progress-actions-status"></p>';
  initProgressActions();
  document.getElementById('kd-export-btn')!.click();
  expect(await captured?.text()).toBe(original);
  expect(click).toHaveBeenCalledTimes(1);
  click.mockRestore();
  vi.unstubAllGlobals();
});
