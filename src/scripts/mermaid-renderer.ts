import mermaid from 'mermaid';

declare global {
  interface Window {
    __kdMermaid?: { refresh: () => void };
  }
}

const MERMAID_PRE_SELECTOR = 'pre[data-language="mermaid"]';
const state = {
  renderCount: 0,
  lastTheme: null as string | null,
};

function currentTheme(): 'light' | 'dark' {
  return document.documentElement.dataset.theme === 'light' ? 'light' : 'dark';
}

function getMermaidBlocks(root: ParentNode = document): HTMLPreElement[] {
  return Array.from(root.querySelectorAll(MERMAID_PRE_SELECTOR));
}

function getHost(pre: HTMLPreElement): HTMLElement {
  return (pre.closest('figure') || pre.closest('.expressive-code') || pre) as HTMLElement;
}

function getDiagramSource(pre: HTMLPreElement): string {
  // Expressive Code wraps each rendered line in `.ec-line` divs. We walk
  // those directly and join with `\n`. Earlier code used `pre.innerText`,
  // but `innerText` collapses lines that share a layout block — which
  // for tightly-packed diagrams (no blank-line separators between every
  // statement) produced one giant single-line string and broke parsing.
  const ecLines = pre.querySelectorAll('.ec-line');
  if (ecLines.length > 0) {
    return Array.from(ecLines)
      .map((line) => (line.textContent || '').replace(/\u00a0/g, ' '))
      .join('\n')
      .trim();
  }
  // Fallback for non-Expressive-Code rendered blocks.
  return (pre.innerText || pre.textContent || '').replace(/\u00a0/g, ' ').trim();
}

function prepareHost(pre: HTMLPreElement): HTMLElement | null {
  const host = getHost(pre);
  const source = getDiagramSource(pre);
  if (!source) return null;

  host.classList.add('kd-mermaid-host');
  host.dataset.mermaidState = 'loading';
  host.dataset.mermaidSource = source;

  let mount = host.querySelector('.kd-mermaid__mount') as HTMLDivElement | null;
  if (!mount) {
    mount = document.createElement('div');
    mount.className = 'kd-mermaid__mount';
    mount.setAttribute('aria-live', 'polite');
    pre.insertAdjacentElement('afterend', mount);
  }

  return host;
}

async function renderHost(host: HTMLElement): Promise<void> {
  const mount = host.querySelector('.kd-mermaid__mount') as HTMLDivElement | null;
  const source = host.dataset.mermaidSource;
  if (!mount || !source) return;

  host.dataset.mermaidState = 'loading';
  mount.replaceChildren();

  mermaid.initialize({
    startOnLoad: false,
    securityLevel: 'loose',
    theme: currentTheme() === 'light' ? 'default' : 'dark',
  });

  const renderId = `kd-mermaid-${++state.renderCount}`;
  try {
    const { svg, bindFunctions } = await mermaid.render(renderId, source);
    mount.innerHTML = svg;
    bindFunctions?.(mount);
    host.dataset.mermaidState = 'ready';
  } catch (error) {
    host.dataset.mermaidState = 'error';
    console.error('Mermaid render failed:', error);
  }
}

async function refresh(root: ParentNode = document): Promise<void> {
  document.documentElement.classList.add('js-mermaid');
  const hosts = getMermaidBlocks(root).map(prepareHost).filter(Boolean) as HTMLElement[];
  const theme = currentTheme();

  if (!hosts.length) {
    state.lastTheme = theme;
    return;
  }

  await Promise.all(hosts.map((host) => renderHost(host)));
  state.lastTheme = theme;
}

function runRefresh(): void {
  refresh().catch((error) => {
    console.error('Mermaid initialization failed:', error);
    document.querySelectorAll<HTMLElement>('.kd-mermaid-host').forEach((host) => {
      host.dataset.mermaidState = 'error';
    });
  });
}

if (window.__kdMermaid?.refresh) {
  window.__kdMermaid.refresh();
} else {
  window.__kdMermaid = { refresh: runRefresh };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', runRefresh, { once: true });
  } else {
    runRefresh();
  }

  document.addEventListener('astro:page-load', runRefresh);

  const themeObserver = new MutationObserver(() => {
    const theme = currentTheme();
    if (theme !== state.lastTheme && document.querySelector('.kd-mermaid-host')) {
      runRefresh();
    }
  });

  themeObserver.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['data-theme'],
  });
}
