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
  const confirm = vi.fn().mockReturnValue(false);
  vi.stubGlobal('confirm', confirm);
  document.getElementById('kd-clear-btn')!.click();
  expect(raw).toBe('invalid original');
  confirm.mockReturnValue(true);
  document.getElementById('kd-clear-btn')!.click();
  expect(raw).toBeNull();
  expect(confirm).toHaveBeenCalledTimes(2);
  vi.unstubAllGlobals();
});
