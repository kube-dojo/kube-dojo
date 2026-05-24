from __future__ import annotations


DESIGN_SYSTEM_LINK = '<link rel="stylesheet" href="/static/design-system.css">'

POLL_STALE_CSS = """
    .poll-stale { opacity: 0.72; }
    .poll-stale[data-poll-ts]::after { content: " · stale"; color: var(--amber, #f59e0b); font-size: 0.85em; font-weight: 700; }
"""


def render_poll_stale_script() -> str:
    return """
<script>
(() => {
  const STALE_MS = 24 * 60 * 60 * 1000;
  function markStalePolls() {
    document.querySelectorAll("[data-poll-ts]").forEach((el) => {
      const ts = Number(el.dataset.pollTs) * 1000;
      if (Number.isFinite(ts) && ts > 0 && Date.now() - ts > STALE_MS) {
        el.classList.add("poll-stale");
      }
    });
  }
  markStalePolls();
  setInterval(markStalePolls, 60000);
})();
</script>"""


def render_global_chrome(*, include_search: bool = True, include_afk: bool = False) -> str:
    parts: list[str] = []
    if include_search:
        parts.append(render_search_widget())
    if include_afk:
        parts.append(render_afk_notify_markup())
    return "\n".join(parts)


AFK_NOTIFY_CSS = """
    .afk-notify{position:fixed;right:18px;bottom:18px;z-index:30;display:flex;align-items:center;gap:10px;max-width:min(440px,calc(100vw - 36px));border:1px solid rgba(61,214,198,.5);background:#121416;color:var(--text);border-radius:6px;padding:10px 12px;box-shadow:0 18px 60px rgba(0,0,0,.4);font-size:13px}
    .afk-notify[hidden]{display:none}
    .afk-notify span{color:var(--text);font-size:13px;margin:0}
    .afk-notify button{border:1px solid var(--line);border-radius:5px;background:var(--panel-2);color:var(--text);padding:6px 9px;font-size:12px;font-weight:800;cursor:pointer;white-space:nowrap}
    .afk-notify button:first-of-type{background:var(--teal);border-color:var(--teal);color:#071211}
"""


def render_afk_notify_markup() -> str:
    return """
<div class="afk-notify" id="afk-notify" hidden>
  <span>Get notified when decisions need your call</span>
  <button type="button" id="afk-notify-enable">Enable</button>
  <button type="button" id="afk-notify-dismiss">Not now</button>
</div>
<script>
(() => {
  const OPT_OUT = "kdjo_notify_optout";
  const SNAPSHOT = "kdjo_pending_files";
  const POLL_MS = 60000;
  const banner = document.getElementById("afk-notify");
  const enable = document.getElementById("afk-notify-enable");
  const dismiss = document.getElementById("afk-notify-dismiss");
  const supported = "Notification" in window;
  const optedOut = () => localStorage.getItem(OPT_OUT) === "1";
  function readSnapshot() {
    try {
      const parsed = JSON.parse(localStorage.getItem(SNAPSHOT) || "[]");
      if (Array.isArray(parsed)) {
        return new Map(parsed.map(item => {
          if (typeof item === "string") return [item, {is_stale: false}];
          return [String(item.filename || ""), {is_stale: !!item.is_stale}];
        }).filter(([name]) => name));
      }
      return new Map(Object.entries(parsed || {}).map(([name, state]) => [
        String(name),
        {is_stale: !!(state && state.is_stale)}
      ]));
    } catch {
      return new Map();
    }
  }
  function writeSnapshot(files) {
    const snapshot = files
      .filter(file => file && file.filename)
      .map(file => ({filename: String(file.filename), is_stale: !!file.is_stale}));
    localStorage.setItem(SNAPSHOT, JSON.stringify(snapshot));
  }
  function ageLabel(file) {
    if (file.is_stale) return "stale (>24h)";
    const age = Math.max(0, Math.floor((Date.now() - Number(file.mtime || 0) * 1000) / 1000));
    if (age < 60) return age + "s ago";
    if (age < 3600) return Math.floor(age / 60) + "m ago";
    if (age < 86400) return Math.floor(age / 3600) + "h ago";
    return Math.floor(age / 86400) + "d ago";
  }
  function suppressNotifications() {
    return document.visibilityState === "visible" && window.location.pathname === "/decisions";
  }
  function notify(title, file) {
    if (!supported || optedOut() || Notification.permission !== "granted" || suppressNotifications()) return;
    const notification = new Notification(title, {
      body: file.filename + " — " + ageLabel(file),
      tag: "kdjo-decision-" + file.filename
    });
    notification.onclick = () => {
      window.focus();
      window.location.href = "/decisions#card-" + encodeURIComponent(file.filename);
      notification.close();
    };
  }
  async function pollPendingDecisions() {
    if (optedOut()) return;
    try {
      const res = await fetch("/api/decisions/pending", {cache: "no-store"});
      if (!res.ok) return;
      const data = await res.json();
      const files = Array.isArray(data.files) ? data.files : [];
      const previous = readSnapshot();
      files.forEach(file => {
        if (!file || !file.filename) return;
        const before = previous.get(String(file.filename));
        if (!before) notify("Decision pending", file);
        else if (!before.is_stale && file.is_stale) notify("Decision stale", file);
      });
      writeSnapshot(files);
    } catch {
      // Local monitor pages should stay quiet when the API is unavailable.
    }
  }
  function maybeShowBanner() {
    if (!banner || !supported || optedOut() || Notification.permission !== "default") return;
    banner.hidden = false;
  }
  enable?.addEventListener("click", async () => {
    if (!supported || optedOut()) return;
    banner.hidden = true;
    await Notification.requestPermission();
    await pollPendingDecisions();
  });
  dismiss?.addEventListener("click", () => {
    localStorage.setItem(OPT_OUT, "1");
    if (banner) banner.hidden = true;
  });
  maybeShowBanner();
  pollPendingDecisions();
  setInterval(pollPendingDecisions, POLL_MS);
})();
</script>"""


def render_search_widget() -> str:
    return """
<style>
  /* Keep in sync with .channels-app height calculations in channels.py. */
  :root{--search-widget-h:53px}
  .search-widget{position:sticky;top:var(--topnav-h,45px);z-index:55;background:#121416;border-bottom:1px solid var(--line,rgba(255,255,255,.08));padding:8px 24px}
  .search-box{position:relative;max-width:720px}
  .search-input{width:100%;height:36px;border:1px solid var(--line,rgba(255,255,255,.12));border-radius:6px;background:#0f1011;color:var(--text,#f3f4f2);padding:0 12px;font:13px/1.4 ui-monospace,SFMono-Regular,Menlo,monospace}
  .search-input:focus{outline:2px solid rgba(61,214,198,.35);border-color:var(--teal,#3dd6c6)}
  .search-dropdown{position:absolute;top:42px;left:0;right:0;z-index:70;display:grid;gap:2px;max-height:min(420px,70vh);overflow:auto;border:1px solid var(--line,rgba(255,255,255,.12));border-radius:6px;background:#101112;box-shadow:0 18px 64px rgba(0,0,0,.45);padding:5px}
  .search-dropdown[hidden]{display:none}
  .search-result{display:grid;grid-template-columns:auto minmax(0,1fr);gap:9px;border:1px solid transparent;border-radius:5px;background:transparent;color:var(--text,#f3f4f2);padding:8px;text-align:left;cursor:pointer}
  .search-result.active,.search-result:hover{border-color:rgba(61,214,198,.45);background:rgba(61,214,198,.11)}
  .search-chip{align-self:start;border:1px solid var(--line,rgba(255,255,255,.12));border-radius:999px;padding:2px 6px;color:var(--muted,#9ca3a3);font-size:10px;font-weight:850;letter-spacing:.04em}
  .search-result-title{font-size:12px;font-weight:850;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .search-snippet{font-size:12px;color:var(--muted,#9ca3a3);margin-top:2px;line-height:1.35}
  .search-snippet mark{background:rgba(253,224,71,.22);color:#fde68a;border-radius:3px;padding:0 2px}
  .search-empty{color:var(--muted,#9ca3a3);font-size:12px;padding:10px}
  @media(max-width:760px){.search-widget{padding:8px 12px}.search-dropdown{max-height:62vh}}
</style>
<div class="search-widget" data-search-widget>
  <div class="search-box">
    <input class="search-input" type="search" placeholder="Search messages + decisions" autocomplete="off" aria-label="Search messages and decisions">
    <div class="search-dropdown" role="listbox" hidden></div>
  </div>
</div>
<script>
(() => {
  const root = document.querySelector("[data-search-widget]");
  if (!root) return;
  const input = root.querySelector(".search-input");
  const dropdown = root.querySelector(".search-dropdown");
  let timer = null;
  let results = [];
  let active = -1;
  const escapeHtml = value => String(value || "").replace(/[&<>"']/g, ch => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  }[ch]));
  function close() {
    dropdown.hidden = true;
    dropdown.innerHTML = "";
    results = [];
    active = -1;
  }
  function setActive(index) {
    active = index;
    dropdown.querySelectorAll(".search-result").forEach((row, idx) => {
      row.classList.toggle("active", idx === active);
      if (idx === active) row.scrollIntoView({block: "nearest"});
    });
  }
  function navigate(result) {
    if (result && result.url) window.location.href = result.url;
  }
  function render() {
    if (!results.length) {
      dropdown.innerHTML = '<div class="search-empty">No matches</div>';
      dropdown.hidden = false;
      return;
    }
    dropdown.innerHTML = results.map((result, idx) => {
      const isDecision = result.kind === "decision";
      const chip = isDecision ? "DECISION" : "CHAT";
      const title = isDecision
        ? (result.title || result.filename || "Decision")
        : ((result.from_agent || "agent") + " in " + (result.channel || "channel"));
      return '<button type="button" class="search-result" data-index="' + idx + '" role="option">' +
        '<span class="search-chip">' + chip + '</span>' +
        '<span><span class="search-result-title">' + escapeHtml(title) + '</span>' +
        '<span class="search-snippet">' + (result.snippet || "") + '</span></span>' +
      '</button>';
    }).join("");
    dropdown.hidden = false;
    setActive(0);
  }
  async function runSearch() {
    const query = input.value.trim();
    if (query.length < 2) {
      close();
      return [];
    }
    try {
      const res = await fetch("/api/search?q=" + encodeURIComponent(query) + "&kind=all&limit=10", {cache: "no-store"});
      if (!res.ok) {
        close();
        return [];
      }
      const data = await res.json();
      results = Array.isArray(data.results) ? data.results : [];
      active = -1;
      render();
      return results;
    } catch {
      close();
    }
    return [];
  }
  input.addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(runSearch, 200);
  });
  input.addEventListener("keydown", event => {
    if (event.key === "Escape") {
      close();
      input.blur();
      return;
    }
    if (dropdown.hidden) return;
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActive(Math.min(results.length - 1, active + 1));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActive(Math.max(0, active - 1));
    } else if (event.key === "Enter") {
      event.preventDefault();
      navigate(results[active]);
    }
  });
  input.addEventListener("keydown", async event => {
    if (event.key !== "Enter" || !dropdown.hidden || input.value.trim().length < 2) return;
    event.preventDefault();
    const freshResults = await runSearch();
    navigate(freshResults[0]);
  });
  dropdown.addEventListener("mousedown", event => {
    const row = event.target.closest(".search-result");
    if (!row) return;
    event.preventDefault();
    navigate(results[Number(row.dataset.index)]);
  });
  document.addEventListener("click", event => {
    if (!root.contains(event.target)) close();
  });
})();
</script>"""
