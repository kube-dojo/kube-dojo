"""HTML page for the Headroom stats dashboard (#2026).

Renders the live Headroom proxy stats (compression %, tokens removed, cost
savings, per-agent usage) from the ``/api/headroom/stats`` endpoint. Kept out of
``local_api.py`` to match the telemetry / agents page pattern. Uses the shared
design-system tokens (loaded via ``ds_link``) for dark-theme parity (#1976).
"""
from __future__ import annotations

_PAGE_CSS = """
.hr-main{max-width:1180px;margin:0 auto;padding:1.2rem}
.hr-head h1{font-size:1.4rem;margin:0 0 .2rem;color:var(--text)}
.hr-sub{color:var(--text-secondary);font-size:.9rem;margin-bottom:1rem}
.hr-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:.75rem;margin:1rem 0 1.4rem}
.hr-card{background:var(--surface-0);border:1px solid var(--border);border-radius:.5rem;padding:.65rem .75rem}
.hr-card .label{color:var(--text-dim);font-size:.75rem;text-transform:uppercase;letter-spacing:.03em}
.hr-card .value{font-size:1.15rem;font-weight:700;color:var(--accent);margin-top:.15rem}
.hr-card .sub{color:var(--text-secondary);font-size:.72rem;margin-top:.1rem}
.hr-card.good .value{color:var(--green)}
.hr-section{margin:1.6rem 0}
.hr-section h2{font-size:1.05rem;color:var(--text);margin:0 0 .5rem}
.hr-note{color:var(--text-secondary);font-size:.82rem;margin:.35rem 0 .6rem}
.hr-note code{background:var(--surface-1);padding:.05rem .3rem;border-radius:.2rem}
table.hr{border-collapse:collapse;width:100%;font-size:.84rem;background:var(--surface-0);color:var(--text)}
table.hr th,table.hr td{border:1px solid var(--border);padding:.35rem .5rem;text-align:right;vertical-align:top}
table.hr th:first-child,table.hr td:first-child,
table.hr th:nth-child(2),table.hr td:nth-child(2),table.hr td.meta{text-align:left}
table.hr th{background:var(--surface-1);color:var(--text-secondary);font-weight:600}
table.hr td.k{font-weight:600;text-align:left}
table.hr td.meta{color:var(--text-secondary);font-size:.8rem}
.hr-down{background:var(--surface-0);border:1px solid var(--border);border-left:3px solid var(--amber,#d97706);border-radius:.5rem;padding:1rem;color:var(--text-secondary)}
.hr-down strong{color:var(--text)}
.empty{color:var(--text-dim);font-style:italic;padding:.5rem}
"""

_PAGE_JS = """
function num(v){return v==null?'\\u2014':Number(v).toLocaleString();}
function money(v){return v==null?'\\u2014':'$'+Number(v).toFixed(2);}
function pctRaw(v){return v==null?'\\u2014':Number(v).toFixed(1)+'%';}
function el(tag,text,cls){var e=document.createElement(tag);if(text!=null)e.textContent=text;if(cls)e.className=cls;return e;}
function card(label,value,sub,good){
  var c=el('div',null,'hr-card'+(good?' good':''));
  c.appendChild(el('div',label,'label'));
  c.appendChild(el('div',value,'value'));
  if(sub)c.appendChild(el('div',sub,'sub'));
  return c;
}
function cardsInto(id,pairs){
  var host=document.getElementById(id);host.textContent='';
  pairs.forEach(function(p){host.appendChild(card(p[0],p[1],p[2],p[3]));});
}
function showDown(d){
  document.getElementById('hr-summary').textContent='proxy unreachable';
  var host=document.getElementById('hr-body');host.textContent='';
  var box=el('div',null,'hr-down');
  var h=el('strong','Headroom proxy unreachable');box.appendChild(h);
  box.appendChild(el('div','Tried '+(d.url||'the proxy')+(d.error?' \\u2014 '+d.error:'')));
  box.appendChild(el('div','Start it with: headroom install start --profile default'));
  host.appendChild(box);
}
function renderAgents(agents){
  var host=document.getElementById('hr-agents');host.textContent='';
  if(!agents||!agents.length){host.appendChild(el('div','no per-agent usage yet','empty'));return;}
  var table=el('table',null,'hr');
  var thead=el('thead'),htr=el('tr');
  ['agent','label','requests','before tok','after tok','tokens saved','saved %','models'].forEach(function(c){htr.appendChild(el('th',c));});
  thead.appendChild(htr);table.appendChild(thead);
  var tb=el('tbody');
  agents.forEach(function(a){
    var tr=el('tr');
    tr.appendChild(el('td',a.agent,'k'));
    tr.appendChild(el('td',a.label,'meta'));
    tr.appendChild(el('td',num(a.requests)));
    tr.appendChild(el('td',num(a.before_tokens)));
    tr.appendChild(el('td',num(a.after_tokens)));
    tr.appendChild(el('td',num(a.tokens_saved)));
    tr.appendChild(el('td',pctRaw(a.savings_percent)));
    var models=a.models?Object.keys(a.models).map(function(m){return m+' ('+a.models[m]+')';}).join(', '):'';
    tr.appendChild(el('td',models,'meta'));
    tb.appendChild(tr);
  });
  table.appendChild(tb);host.appendChild(table);
}
function render(d){
  var s=d.summary||{};var comp=s.compression||{};var cost=s.cost||{};
  var br=cost.breakdown||{};var unc=s.uncompressed_requests||{};var mcp=s.mcp||{};
  var au=d.agent_usage||{};
  document.getElementById('hr-summary').textContent=
    'mode '+(s.mode||'?')+' \\u00b7 '+(s.primary_model||'?')+' \\u00b7 '+num(s.api_requests)+' API requests';
  document.getElementById('hr-body').style.display='';
  cardsInto('hr-top',[
    ['API requests',num(s.api_requests)],
    ['Compressed',num(comp.requests_compressed)],
    ['Avg compression',pctRaw(comp.avg_compression_pct)],
    ['Best compression',pctRaw(comp.best_compression_pct),comp.best_detail],
    ['Tokens removed',num(comp.total_tokens_removed)],
    ['Cost saved',money(cost.total_saved_usd),pctRaw(cost.savings_pct)+' vs no Headroom',true]
  ]);
  cardsInto('hr-cost',[
    ['Without Headroom',money(cost.without_headroom_usd)],
    ['With Headroom',money(cost.with_headroom_usd)],
    ['Compression savings',money(br.compression_savings_usd),null,true],
    ['Cache savings',money(br.cache_savings_usd),null,true]
  ]);
  cardsInto('hr-unc',[
    ['Prefix-frozen',num(unc.prefix_frozen)],
    ['Too small',num(unc.too_small)],
    ['Passthrough',num(unc.passthrough)],
    ['No compressible',num(unc.no_compressible_content)]
  ]);
  cardsInto('hr-mcp',[
    ['MCP compressions',num(mcp.compressions)],
    ['MCP retrievals',num(mcp.retrievals)],
    ['MCP tokens removed',num(mcp.tokens_removed)]
  ]);
  renderAgents(au.agents||[]);
}
async function load(){
  try{
    var r=await fetch('/api/headroom/stats');
    var d=await r.json();
    if(!d.ok){showDown(d);return;}
    render(d);
  }catch(e){document.getElementById('hr-summary').textContent='failed to load: '+e;}
}
load();
setInterval(load,15000);
"""


def render_headroom_stats_page_html(*, top_nav: str = "", nav_css: str = "", ds_link: str = "") -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Headroom - KubeDojo Local Monitor</title>
  {ds_link}
  <style>
{nav_css}
{_PAGE_CSS}
  </style>
</head>
<body>
  {top_nav}
  <main class="hr-main">
    <div class="hr-head">
      <h1>Headroom</h1>
      <div class="hr-sub" id="hr-summary">loading proxy stats&hellip;</div>
    </div>

    <div id="hr-body" style="display:none">
      <div class="hr-section">
        <h2>Compression &amp; savings</h2>
        <div id="hr-top" class="hr-cards"></div>
      </div>

      <div class="hr-section">
        <h2>Cost</h2>
        <div id="hr-cost" class="hr-cards"></div>
        <div class="hr-note">Cache savings come from provider prompt-caching; compression savings come from Headroom shrinking each request. Dollar figures use model list price.</div>
      </div>

      <div class="hr-section">
        <h2>Uncompressed requests</h2>
        <div class="hr-note">Requests Headroom left untouched, by reason.</div>
        <div id="hr-unc" class="hr-cards"></div>
      </div>

      <div class="hr-section">
        <h2>MCP tools</h2>
        <div class="hr-note">On-demand <code>headroom_compress</code> / <code>headroom_retrieve</code> usage this session.</div>
        <div id="hr-mcp" class="hr-cards"></div>
      </div>

      <div class="hr-section">
        <h2>Per-agent usage</h2>
        <div id="hr-agents"><div class="empty">loading&hellip;</div></div>
      </div>
    </div>

    <div class="hr-note" style="margin-top:1.4rem;border-top:1px solid var(--border);padding-top:.6rem">
      Live view of the local Headroom proxy (<code>127.0.0.1:8787/stats</code>); refreshes every 15s.
      Stats are per proxy-session. See <code>.claude/rules/headroom.md</code>.
    </div>
  </main>
  <script>
{_PAGE_JS}
  </script>
</body>
</html>"""
