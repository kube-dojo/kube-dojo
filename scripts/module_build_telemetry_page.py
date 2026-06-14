"""HTML page for KubeDojo telemetry dashboard (#1973 P1–P3).

Renders module-build, tool-timing, and runtime dispatch rollups from the
``/api/telemetry/*`` JSON endpoints. Kept out of ``local_api.py`` to match
the agents telemetry page pattern.
"""
from __future__ import annotations

# Dark-theme: consume the shared design-system tokens (static/design-system.css,
# loaded via ds_link) so this page matches the rest of the Local Monitor. The old
# hardcoded light-theme hex (#fff cards, #1e3a8a headings, #64748b text) rendered
# dark-on-dark and was unreadable — kube-dojo/kube-dojo.github.io#1976.
_PAGE_CSS = """
.mb-main{max-width:1180px;margin:0 auto;padding:1.2rem}
.mb-head h1{font-size:1.4rem;margin:0 0 .2rem;color:var(--text)}
.mb-sub{color:var(--text-secondary);font-size:.9rem;margin-bottom:1rem}
.mb-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:.75rem;margin:1rem 0 1.4rem}
.mb-card{background:var(--surface-0);border:1px solid var(--border);border-radius:.5rem;padding:.65rem .75rem}
.mb-card .label{color:var(--text-dim);font-size:.75rem;text-transform:uppercase;letter-spacing:.03em}
.mb-card .value{font-size:1.15rem;font-weight:700;color:var(--accent);margin-top:.15rem}
.mb-section{margin:1.6rem 0}
.mb-section h2{font-size:1.05rem;color:var(--text);margin:0 0 .5rem}
.mb-section-head{display:flex;flex-wrap:wrap;align-items:center;gap:.5rem;margin-bottom:.5rem}
.mb-section-head h2{margin:0}
.mb-win-btns{display:flex;gap:.35rem}
.mb-win-btns button{font-size:.75rem;padding:.2rem .45rem;border:1px solid var(--border);background:var(--surface-1);border-radius:.25rem;cursor:pointer;color:var(--text-secondary)}
.mb-win-btns button.active{background:var(--accent-muted);border-color:var(--accent);color:var(--accent);font-weight:600}
.mb-note{color:var(--text-secondary);font-size:.82rem;margin:.35rem 0 .6rem}
.mb-note a{color:var(--accent)}
table.mb{border-collapse:collapse;width:100%;font-size:.84rem;background:var(--surface-0);color:var(--text)}
table.mb th,table.mb td{border:1px solid var(--border);padding:.35rem .5rem;text-align:right;vertical-align:top}
table.mb th:first-child,table.mb td:first-child,
table.mb th:nth-child(2),table.mb td:nth-child(3),
table.mb td.meta{text-align:left}
table.mb th{background:var(--surface-1);color:var(--text-secondary);font-weight:600}
table.mb td.k{font-weight:600;text-align:left}
table.mb td.meta{color:var(--text-secondary);font-size:.8rem}
table.mb td.yes{color:var(--green);font-weight:600}
table.mb td.no{color:var(--text-dim)}
.mb-legend{color:var(--text-secondary);font-size:.8rem;margin-top:1.2rem;border-top:1px solid var(--border);padding-top:.6rem}
.empty{color:var(--text-dim);font-style:italic;padding:.5rem}
"""

_PAGE_JS = """
var ttWindow='1h';
function fmt(v){return v==null?'\\u2014':String(v);}
function money(v){return v==null?'\\u2014':'$'+Number(v).toFixed(4);}
function pct(v){return v==null?'\\u2014':(Number(v)*100).toFixed(1)+'%';}
function el(tag,text,cls){var e=document.createElement(tag);if(text!=null)e.textContent=text;if(cls)e.className=cls;return e;}
function renderTotals(t){
  var host=document.getElementById('mb-totals');
  host.textContent='';
  var cards=[
    ['runs',t.runs],['swarm',t.swarm_runs],['solo',t.solo_runs],['participants',t.participants],
    ['prompt tok',t.prompt_tokens],['response tok',t.response_tokens],['total tok',t.total_tokens],['cost est',money(t.cost_usd_est)]
  ];
  cards.forEach(function(pair){
    var card=el('div',null,'mb-card');
    card.appendChild(el('div',pair[0],'label'));
    card.appendChild(el('div',fmt(pair[1]),'value'));
    host.appendChild(card);
  });
}
function renderRuns(rows){
  var host=document.getElementById('mb-runs');
  host.textContent='';
  if(!rows||!rows.length){host.appendChild(el('div','no module-build records yet','empty'));return;}
  var table=el('table',null,'mb');
  var thead=el('thead'),htr=el('tr');
  ['track','slug','run','swarm','tokens','cost','participants','source'].forEach(function(c){htr.appendChild(el('th',c));});
  thead.appendChild(htr);table.appendChild(thead);
  var tb=el('tbody');
  rows.forEach(function(r){
    var tr=el('tr');
    tr.appendChild(el('td',r.track,'meta'));
    tr.appendChild(el('td',r.slug,'meta'));
    tr.appendChild(el('td',r.run_id,'k'));
    var sw=el('td',r.swarm_used?'yes ('+r.swarm_label+')':'no',r.swarm_used?'yes':'no');
    tr.appendChild(sw);
    tr.appendChild(el('td',fmt((r.totals||{}).total_tokens)));
    tr.appendChild(el('td',money((r.totals||{}).cost_usd_est)));
    tr.appendChild(el('td',fmt((r.totals||{}).participants)));
    tr.appendChild(el('td',r.source,'meta'));
    tb.appendChild(tr);
  });
  table.appendChild(tb);host.appendChild(table);
}
function renderToolTimings(rows){
  var host=document.getElementById('tt-tools');
  host.textContent='';
  if(!rows||!rows.length){host.appendChild(el('div','no tool timings in window','empty'));return;}
  var table=el('table',null,'mb');
  var thead=el('thead'),htr=el('tr');
  ['tool','count','p50 ms','p95 ms','p99 ms','mean ms','failures'].forEach(function(c){htr.appendChild(el('th',c));});
  thead.appendChild(htr);table.appendChild(thead);
  var tb=el('tbody');
  rows.forEach(function(r){
    var tr=el('tr');
    tr.appendChild(el('td',r.tool_name,'k'));
    tr.appendChild(el('td',fmt(r.count)));
    tr.appendChild(el('td',fmt(r.p50_ms)));
    tr.appendChild(el('td',fmt(r.p95_ms)));
    tr.appendChild(el('td',fmt(r.p99_ms)));
    tr.appendChild(el('td',fmt(r.mean_ms)));
    tr.appendChild(el('td',fmt(r.failure_count)));
    tb.appendChild(tr);
  });
  table.appendChild(tb);host.appendChild(table);
}
function renderRuntimeUsage(agents, totals){
  var host=document.getElementById('ru-usage');
  host.textContent='';
  var cardsHost=document.getElementById('ru-totals');
  cardsHost.textContent='';
  var cards=[
    ['calls',totals.calls],['ok',totals.ok],['failed',totals.failed],
    ['fail rate',pct(totals.rate_failed)],['mean elapsed s',fmt(totals.mean_elapsed_s)]
  ];
  cards.forEach(function(pair){
    var card=el('div',null,'mb-card');
    card.appendChild(el('div',pair[0],'label'));
    card.appendChild(el('div',fmt(pair[1]),'value'));
    cardsHost.appendChild(card);
  });
  if(!agents||!agents.length){host.appendChild(el('div','no dispatch records in window','empty'));return;}
  var table=el('table',null,'mb');
  var thead=el('thead'),htr=el('tr');
  ['agent','calls','ok','failed','fail rate','mean s','p95 s','models'].forEach(function(c){htr.appendChild(el('th',c));});
  thead.appendChild(htr);table.appendChild(thead);
  var tb=el('tbody');
  agents.forEach(function(r){
    var tr=el('tr');
    tr.appendChild(el('td',r.agent,'k'));
    tr.appendChild(el('td',fmt(r.calls)));
    tr.appendChild(el('td',fmt(r.ok)));
    tr.appendChild(el('td',fmt(r.failed)));
    tr.appendChild(el('td',pct(r.rate_failed)));
    tr.appendChild(el('td',fmt(r.mean_elapsed_s)));
    tr.appendChild(el('td',fmt(r.p95_elapsed_s)));
    tr.appendChild(el('td',(r.models||[]).join(', '),'meta'));
    tb.appendChild(tr);
  });
  table.appendChild(tb);host.appendChild(table);
}
function renderRuntimeRecent(rows){
  var host=document.getElementById('ru-recent');
  host.textContent='';
  if(!rows||!rows.length){host.appendChild(el('div','no recent dispatches','empty'));return;}
  var table=el('table',null,'mb');
  var thead=el('thead'),htr=el('tr');
  ['ts','agent','model','class','ok','elapsed s','task id'].forEach(function(c){htr.appendChild(el('th',c));});
  thead.appendChild(htr);table.appendChild(thead);
  var tb=el('tbody');
  rows.forEach(function(r){
    var tr=el('tr');
    tr.appendChild(el('td',fmt(r.ts),'meta'));
    tr.appendChild(el('td',r.agent,'k'));
    tr.appendChild(el('td',r.model,'meta'));
    tr.appendChild(el('td',r.task_class,'meta'));
    tr.appendChild(el('td',r.ok===false?'no':'yes',r.ok===false?'no':'yes'));
    tr.appendChild(el('td',fmt(r.elapsed_s)));
    tr.appendChild(el('td',r.task_id,'meta'));
    tb.appendChild(tr);
  });
  table.appendChild(tb);host.appendChild(table);
}
function setToolWindow(w, btn){
  ttWindow=w;
  document.querySelectorAll('.mb-win-btns button').forEach(function(b){b.classList.remove('active');});
  if(btn) btn.classList.add('active');
  loadToolTimings();
}
async function loadModuleBuilds(){
  try{
    var r=await fetch('/api/telemetry/module-builds?limit=100');
    var d=await r.json();
    document.getElementById('mb-summary').textContent=
      d.records_total+' module-build records \\u00b7 generated '+d.generated_at;
    renderTotals(d.totals||{});
    renderRuns(d.runs||[]);
  }catch(e){document.getElementById('mb-summary').textContent='failed to load module builds: '+e;}
}
async function loadToolTimings(){
  try{
    var r=await fetch('/api/telemetry/tool-timings?window='+encodeURIComponent(ttWindow));
    var d=await r.json();
    document.getElementById('tt-summary').textContent=
      (d.tools||[]).length+' tools \\u00b7 window '+d.window+' \\u00b7 generated '+d.generated_at;
    renderToolTimings(d.tools||[]);
  }catch(e){document.getElementById('tt-summary').textContent='failed to load tool timings: '+e;}
}
async function loadRuntime(){
  try{
    var ur=await fetch('/api/telemetry/runtime/usage?days=7');
    var u=await ur.json();
    document.getElementById('ru-summary').textContent=
      'last '+u.days+' days \\u00b7 generated '+u.generated_at;
    renderRuntimeUsage(u.agents||[], u.totals||{});
    var rr=await fetch('/api/telemetry/runtime/recent?limit=50');
    var rec=await rr.json();
    renderRuntimeRecent(rec.records||[]);
  }catch(e){document.getElementById('ru-summary').textContent='failed to load runtime usage: '+e;}
}
loadModuleBuilds();
loadToolTimings();
loadRuntime();
"""


def render_module_builds_page_html(*, top_nav: str = "", nav_css: str = "", ds_link: str = "") -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Telemetry - KubeDojo Local Monitor</title>
  {ds_link}
  <style>
{nav_css}
{_PAGE_CSS}
  </style>
</head>
<body>
  {top_nav}
  <main class="mb-main">
    <div class="mb-head">
      <h1>Telemetry</h1>
      <div class="mb-sub" id="mb-summary">loading module builds&hellip;</div>
    </div>

    <div id="mb-totals" class="mb-cards"></div>

    <div class="mb-section">
      <h2>Module build runs</h2>
      <div id="mb-runs"><div class="empty">loading&hellip;</div></div>
    </div>

    <div class="mb-section">
      <div class="mb-section-head">
        <h2>Tool timings</h2>
        <div class="mb-win-btns">
          <button type="button" onclick="setToolWindow('5m', this)">5m</button>
          <button type="button" class="active" onclick="setToolWindow('1h', this)">1h</button>
          <button type="button" onclick="setToolWindow('24h', this)">24h</button>
        </div>
      </div>
      <div class="mb-sub" id="tt-summary">loading tool timings&hellip;</div>
      <div id="tt-tools"><div class="empty">loading&hellip;</div></div>
    </div>

    <div class="mb-section">
      <h2>Runtime usage</h2>
      <div class="mb-note">
        <a href="/agents">/agents</a> tracks review-outcome quality (annotated ground checks);
        this section shows dispatch usage and latency from <code>logs/smart_dispatch.jsonl</code>.
      </div>
      <div class="mb-sub" id="ru-summary">loading runtime usage&hellip;</div>
      <div id="ru-totals" class="mb-cards"></div>
      <div id="ru-usage"><div class="empty">loading&hellip;</div></div>
    </div>

    <div class="mb-section">
      <h2>Recent dispatches</h2>
      <div id="ru-recent"><div class="empty">loading&hellip;</div></div>
    </div>

    <div class="mb-legend">
      Module builds: record finalize-time token rollups with
      <code>python -m scripts.agent_telemetry record-build</code> or
      <code>POST /api/telemetry/module-builds</code>.
      Tool timings: ingest via <code>POST /api/telemetry/tool-timings</code>.
    </div>
  </main>
  <script>
{_PAGE_JS}
  </script>
</body>
</html>"""
