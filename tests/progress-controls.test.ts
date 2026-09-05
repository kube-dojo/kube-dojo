import { expect, it, vi } from 'vitest';

it('binds eligible controls to shared progress and reports invalid storage without mutation', async () => {
  const records = new Map<string, string>();
  const localStorage = {
    getItem: (key: string) => records.get(key) ?? null,
    setItem: (key: string, value: string) => { records.set(key, value); },
    clear: () => records.clear(),
  };
  vi.stubGlobal('localStorage', localStorage);
  const lessons = [{ id: 'ai/module-a', track: 'ai', kind: 'module', keys: ['ai/a', 'uk/ai/a'] }];
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({ schemaVersion: 1, lessons }) }));
  const page = (path: string) => {
    window.history.replaceState({}, '', path);
    document.body.innerHTML = '<nav class="kd-sb"><a href="/ai/a/">EN</a><a href="/uk/ai/a/">UK</a></nav><div class="sl-markdown-content"></div>';
  };
  localStorage.setItem('kubedojo-progress', '{"uk/ai/a":123,"retired":17}');
  page('/ai/a/');
  const { init } = await import('../src/scripts/progress-tracker');
  await init();
  const button = document.querySelector<HTMLButtonElement>('.kd-complete-btn')!;
  expect(button.getAttribute('aria-pressed')).toBe('true');
  expect(document.querySelectorAll('[data-completed="true"]')).toHaveLength(2);
  button.click();
  expect(JSON.parse(localStorage.getItem('kubedojo-progress')!)).toEqual({ retired: 17 });
  expect(button.getAttribute('aria-pressed')).toBe('false');
  localStorage.setItem('kubedojo-progress', 'null');
  await init();
  expect(button.disabled).toBe(true);
  expect(button.hasAttribute('aria-pressed')).toBe(false);
  expect(document.querySelector('[role="alert"]')?.textContent).toContain('could not be read');
  button.click();
  expect(localStorage.getItem('kubedojo-progress')).toBe('null');
  localStorage.setItem('kubedojo-progress', '{}');
  document.querySelector<HTMLButtonElement>('#kd-progress-error button')!.click();
  await vi.waitFor(() => expect(button.disabled).toBe(false));
  expect(document.querySelector('[role="alert"]')).toBeNull();
  page('/progress/');
  await init();
  expect(document.querySelector('.kd-complete-btn')).toBeNull();
  localStorage.clear();
  vi.unstubAllGlobals();
});
