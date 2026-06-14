"""HTML page for the agent-telemetry Monitor tab (#1860, phase 2).

Renders the per-lane / per-harness / per-model performance rollup from
`/api/telemetry/agents` (served by `agent_telemetry.build_agent_telemetry`).
Kept in its own module so the big HTML/JS blob stays out of `local_api.py`;
`local_api.route_request` wires `/agents` (this page) + `/api/telemetry/agents`
(the JSON) and passes the shared nav/chrome in. The client builds the DOM with
createElement + textContent (no innerHTML) so values are never interpreted as
markup.
"""
from __future__ import annotations

# Dark-theme: consume the shared design-system tokens (static/design-system.css,
# loaded via ds_link) so this page matches the rest of the Local Monitor. The old
# hardcoded light-theme hex rendered dark-on-dark and was unreadable —
# kube-dojo/kube-dojo.github.io#1976.
_PAGE_CSS = """
.tel-main{max-width:1180px;margin:0 auto;padding:1.2rem}
.tel-head h1{font-size:1.4rem;margin:0 0 .2rem;color:var(--text)}
.tel-sub{color:var(--text-secondary);font-size:.9rem;margin-bottom:1rem}
.tel-section{margin:1.6rem 0}
.tel-section h2{font-size:1.05rem;color:var(--text);margin:0 0 .1rem}
.tel-section .hint{color:var(--text-secondary);font-size:.82rem;margin-bottom:.5rem}
table.tg{border-collapse:collapse;width:100%;font-size:.88rem;background:var(--surface-0);color:var(--text)}
table.tg th,table.tg td{border:1px solid var(--border);padding:.35rem .55rem;text-align:right}
table.tg th:first-child,table.tg td:first-child,
table.tg th:nth-child(2),table.tg td.dim{text-align:left}
table.tg th{background:var(--surface-1);color:var(--text-secondary);font-weight:600}
table.tg td.k{font-weight:600;text-align:left}
table.tg td.dim{color:var(--text-secondary);font-size:.82rem}
table.tg td.bad{color:var(--red);font-weight:700;background:var(--red-muted)}
table.tg td.warn{color:var(--amber);font-weight:600}
.tel-legend{color:var(--text-secondary);font-size:.8rem;margin-top:1.2rem;border-top:1px solid var(--border);padding-top:.6rem}
.empty{color:var(--text-dim);font-style:italic;padding:.5rem}
"""

# DOM is built with createElement + textContent only (no innerHTML) — values are
# never parsed as markup.
_PAGE_JS = """
function pct(v){return v==null?'\\u2014':v+'%';}
function num(v){return v==null?'\\u2014':String(Math.round(v));}
function el(tag,text,cls){var e=document.createElement(tag);if(text!=null)e.textContent=text;if(cls)e.className=cls;return e;}
function renderTable(hostId,rows,keyName,showHarness){
  var host=document.getElementById(hostId);
  host.textContent='';
  if(!rows||!rows.length){host.appendChild(el('div','no data yet','empty'));return;}
  var table=el('table',null,'tg');
  var thead=el('thead'),htr=el('tr');
  [keyName,showHarness?'harness':'models','disp','fail%','avg s','annot','miss%','outcomes']
    .forEach(function(c){htr.appendChild(el('th',c));});
  thead.appendChild(htr);table.appendChild(thead);
  var tb=el('tbody');
  rows.forEach(function(r){
    var tr=el('tr');
    tr.appendChild(el('td',r[keyName],'k'));
    tr.appendChild(el('td',showHarness?(r.harness||'?'):(r.models||[]).join(', '),'dim'));
    tr.appendChild(el('td',r.dispatches));
    var f=el('td',pct(r.fail_pct));
    if(r.fail_pct!=null&&r.fail_pct>=25)f.className='bad';else if(r.fail_pct!=null&&r.fail_pct>=10)f.className='warn';
    tr.appendChild(f);
    tr.appendChild(el('td',num(r.avg_elapsed_s)));
    tr.appendChild(el('td',r.annotated));
    var m=el('td',pct(r.miss_pct));if(r.miss_pct!=null&&r.miss_pct>0)m.className='bad';tr.appendChild(m);
    var oc=Object.entries(r.outcomes||{}).map(function(kv){return kv[0]+'='+kv[1];}).join(' ');
    tr.appendChild(el('td',oc||'\\u2014','dim'));
    tb.appendChild(tr);
  });
  table.appendChild(tb);host.appendChild(table);
}
async function loadTelemetry(){
  try{
    var r=await fetch('/api/telemetry/agents');var d=await r.json();
    document.getElementById('tel-summary').textContent=
      d.dispatch_total+' dispatches \\u00b7 '+d.annotated_total+' annotated outcomes';
    renderTable('tel-lanes',d.lanes,'lane',true);
    renderTable('tel-harness',d.by_harness,'harness',false);
    renderTable('tel-model',d.by_model,'model',false);
  }catch(e){document.getElementById('tel-summary').textContent='failed to load: '+e;}
}
loadTelemetry();
"""


def render_agents_page_html(*, top_nav: str = "", nav_css: str = "", ds_link: str = "") -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Agents - KubeDojo Local Monitor</title>
  {ds_link}
  <style>
{nav_css}
{_PAGE_CSS}
  </style>
</head>
<body>
  {top_nav}
  <main class="tel-main">
    <div class="tel-head">
      <h1>Agent Performance</h1>
      <div class="tel-sub" id="tel-summary">loading&hellip;</div>
    </div>

    <div class="tel-section">
      <h2>By lane</h2>
      <div class="hint">what you dispatch to (a harness + model pairing)</div>
      <div id="tel-lanes"><div class="empty">loading&hellip;</div></div>
    </div>

    <div class="tel-section">
      <h2>By harness</h2>
      <div class="hint">the runtime — isolates harness reliability from model quality (deepseek &amp; qwen both run on hermes)</div>
      <div id="tel-harness"><div class="empty">loading&hellip;</div></div>
    </div>

    <div class="tel-section">
      <h2>By model</h2>
      <div class="hint">the brain — how a model performs regardless of which harness ran it</div>
      <div id="tel-model"><div class="empty">loading&hellip;</div></div>
    </div>

    <div class="tel-legend">
      <strong>fail%</strong> = empty/errored dispatches (operational, all history) ·
      <strong>miss%</strong> = (fabrication + overturned) / annotated (quality, ground-checked outcomes) ·
      grow the signal with <code>scripts/agent_telemetry.py annotate</code>.
    </div>
  </main>
  <script>
{_PAGE_JS}
  </script>
</body>
</html>"""
