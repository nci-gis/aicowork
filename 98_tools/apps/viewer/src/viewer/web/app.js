const CIRCLE_COLOR = { work:'var(--work)', family:'var(--family)',
                       friend:'var(--friend)', health:'var(--health)' };
const KIND_ICON = { event:'📅', email:'✉️', persona:'👤', project:'📁',
                    log:'📓', note:'🗂', practice:'🔁', decision:'⚖️', reminder:'⏰' };
/* v1.3 visibility — may this file leave the machine? Rendering is fail-closed:
   anything that is not exactly internal/public shows as private (CONVENTIONS
   'Visibility & egress'; PHILOSOPHY #11). */
const VIS = { private:{i:'🔒', l:'private'}, internal:{i:'🏢', l:'internal'}, public:{i:'🌐', l:'public'} };
const VIS_ORDER = ['private','internal','public'];
const visOf = v => VIS[v] ? v : 'private';
const visBadge = v => { v = visOf(v);
  return `<span class="vis vis-${v}" title="visibility: ${VIS[v].l}">${VIS[v].i}</span>`; };
let DATA=null, calY, calM, TAB='dash', CUR=null, qTimer=null, MODE='all';
let energyChart=null, lessonsAll=false;
const LIFE = ['family','friend','health'];
const inMode = c => MODE==='all' ? true
  : MODE==='work' ? c==='work' : LIFE.includes(c);
const $ = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/[&<>"']/g,
  c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

/* ---------- event delegation ----------
   No inline handlers anywhere (the CSP forbids inline script). Markup carries
   data-act="name" (+ data-* args); one listener per event type dispatches. */
const ACT = {
  open:        el => openItem(el.dataset.path),
  browseKind:  el => browseWith(el.dataset.kind),
  browseCircle:el => browseWith(undefined, $('f-circle').value===el.dataset.circle ? '' : el.dataset.circle),
  balance:     el => browseWith('', el.dataset.circle),
  tab:         el => setTab(el.dataset.tab),
  mode:        el => setMode(el.dataset.mode),
  sec:         el => toggleSec(el),
  cal:         el => navCal(+el.dataset.step),
  calToday:    () => goToday(),
  lessons:     () => toggleLessons(),
  chipRemove:  el => chipRemove(+el.dataset.i),
  visApply:    el => visApply(el.dataset.v),
  visCancel:   () => CUR && openItem(CUR.path, false),
  qaOpen:      () => qaOpen(),
  qaClose:     () => qaClose(),
  qaSave:      () => qaSave(),
  reload:      () => load(),
  side:        () => toggleSide(),
  close:       () => closeDrawer(),
  back:        () => drawerBack(),
  edit:        () => toggleEdit(),
  cancelEdit:  () => cancelEdit(),
  save:        () => saveItem(),
  remDone:     el => reminderDone(el.dataset.path, +el.dataset.mtime),
  openCtx:     (el, e) => { e.stopPropagation(); openItem(el.dataset.path, true); },
  planApply:   el => triagePlan(el.dataset.name, 'apply'),
  planDismiss: el => triagePlan(el.dataset.name, 'dismiss'),
};
const ON_CHANGE = { search: () => doSearch(), vis: el => visPick(el.value) };
const ON_INPUT = { search: () => onSearchInput() };
document.addEventListener('click', e => {
  const el = e.target.closest('[data-act]');
  if (el && ACT[el.dataset.act]) ACT[el.dataset.act](el, e);
});
document.addEventListener('change', e => {
  const k = e.target.dataset && e.target.dataset.change;
  if (k && ON_CHANGE[k]) ON_CHANGE[k](e.target, e);
});
document.addEventListener('input', e => {
  const k = e.target.dataset && e.target.dataset.input;
  if (k && ON_INPUT[k]) ON_INPUT[k](e.target, e);
});

/* ---------- UI language (aicowork.yaml language.ui -> web/i18n/<lang>.json) ---------- */
let I18N = {};
const LOCALE = { en:'en-GB', vi:'vi-VN' };
const t = (k, vars) => { let s = I18N[k] || k; for (const [n,v] of Object.entries(vars||{})) s = s.replace('{'+n+'}', v); return s; };
async function loadI18n(lang){
  try { I18N = await (await fetch('/static/i18n/' + (LOCALE[lang] ? lang : 'en') + '.json')).json(); }
  catch(e){ I18N = {}; }
  document.documentElement.lang = LOCALE[lang] ? lang : 'en';
  document.querySelectorAll('[data-i18n]').forEach(el => { if (I18N[el.dataset.i18n]) el.textContent = I18N[el.dataset.i18n]; });
  document.querySelectorAll('[data-i18n-ph]').forEach(el => { if (I18N[el.dataset.i18nPh]) el.placeholder = I18N[el.dataset.i18nPh]; });
}
const locale = () => LOCALE[(DATA && DATA.ui && DATA.ui.lang)] || 'en-GB';

/* ---------- toast (vanilla, ~25 lines — no lib) ---------- */
function toast(msg, type='ok', ms=2600){
  let host = $('toasts');
  if (!host){ host = document.createElement('div'); host.id='toasts';
              document.body.appendChild(host); }
  const t = document.createElement('div');
  t.className = 'toast ' + type;
  t.textContent = msg;
  host.appendChild(t);
  requestAnimationFrame(()=>t.classList.add('show'));
  setTimeout(()=>{ t.classList.remove('show');
                   setTimeout(()=>t.remove(), 250); }, ms);
}

const tip = $('tip');
function hover(el, html){
  el.addEventListener('mouseenter', e=>{ tip.innerHTML=html; tip.style.display='block'; mv(e); });
  el.addEventListener('mousemove', mv);
  el.addEventListener('mouseleave', ()=>tip.style.display='none');
}
function mv(e){ tip.style.left=Math.min(e.clientX+14, innerWidth-300)+'px';
                tip.style.top=(e.clientY+14)+'px'; }

/* ---------- tabs & sidebar ---------- */
function setTab(t){ TAB=t;
  $('view-dash').style.display = t==='dash' ? '' : 'none';
  $('view-browse').style.display = t==='browse' ? '' : 'none';
  $('nav-dash').classList.toggle('on', t==='dash');
  $('nav-browse').classList.toggle('on', t==='browse');
  if (t==='browse') doSearch();
}
function browseWith(kind, circle){
  if (kind !== undefined) $('f-kind').value = kind;
  if (circle !== undefined) $('f-circle').value = circle;
  setTab('browse');
}
function renderSidebar(){
  const c = DATA.counts;
  const curK = $('f-kind').value;
  $('side-types').innerHTML = [
    ['event','Events'],['email','Emails'],['persona','Personas'],
    ['project','Projects'],['log','Logs'],['note','Archive'],
    ['practice','Practices'],['decision','Decisions'],['reminder','Reminders'],
  ].map(([k,l]) => `<button class="side-type ${TAB==='browse'&&curK===k?'on':''}" data-act="browseKind" data-kind="${k}">
      <span>${KIND_ICON[k]}&nbsp; ${l}</span><span class="n">${c[k]||0}</span>
    </button>`).join('');
  const curC = $('f-circle').value;
  $('side-circles').innerHTML = ['work','family','friend','health'].map(x =>
    `<button class="pill ${curC===x?'on':''}" data-act="browseCircle" data-circle="${x}">
       <span class="dot" style="background:${CIRCLE_COLOR[x]}"></span>${x}</button>`).join('');
  $('side-foot').textContent = DATA.base_name || '';
}

/* ---------- data ---------- */
let LOADED_AT = 0;
async function load(){
  document.body.classList.add('loading-data');
  let r, data;
  try {
    r = await fetch('/api/data');
    if (r.status === 401){ toast('Session expired — reopen the link printed by aicowork viz', 'err', 8000); return; }
    if (!r.ok) throw new Error('HTTP ' + r.status);
    data = await r.json();
  } catch(e){
    toast(t('load_failed'), 'err', 6000);          // keep what is on screen
    return;
  } finally { document.body.classList.remove('loading-data'); }
  const first = DATA === null;
  DATA = data; LOADED_AT = Date.now();
  if (first) await loadI18n(DATA.ui && DATA.ui.lang);
  const td = new Date(DATA.today+'T00:00:00');
  if (calY===undefined){ calY=td.getFullYear(); calM=td.getMonth(); }
  occSeed();
  renderSidebar();
  renderDash();
  if (TAB==='browse') doSearch();
}

/* a tab left open overnight shows yesterday's "today": reload when it comes back
   after the date changed or more than five minutes passed */
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState !== 'visible' || !DATA) return;
  const dateChanged = new Date().toISOString().slice(0,10) !== DATA.today && new Date().toDateString() !== new Date(DATA.today+'T00:00:00').toDateString();
  if (dateChanged || Date.now() - LOADED_AT > 5 * 60 * 1000) load();
});

function setMode(m){ MODE=m;
  for (const x of ['all','work','life'])
    $('mode-'+x).classList.toggle('on', x===m);
  renderDash();
}

function renderToday(){
  const d = DATA;
  $('today-h').textContent = t('today') + ' — ' +
    new Date(d.today+'T00:00:00').toLocaleDateString(locale(),
      {weekday:'long', day:'numeric', month:'long'});
  const late = d.upcoming.filter(e => e.kind==='reminder' && e.days_left<0 && inMode(e.circle));
  let html = late.length ? `<div class="up-group">${esc(t('rem.overdue_group'))}</div><ul class="plain">` + late.map(e => `
      <li data-act="open" data-path="${esc(e.path)}"><div class="li-top">
        <span class="dot" style="background:${CIRCLE_COLOR[e.circle]||'var(--muted)'}"></span>${visBadge(e.visibility)}
        <span class="when">${esc(e.date)}</span>${remBadge(e)}
      </div><div class="li-title rem-row"><span>${KIND_ICON.reminder} ${esc(e.title)}</span>${remDoneBtn(e)}</div></li>`).join('') + '</ul>' : '';
  const evs = d.upcoming.filter(e => e.days_left===0 && inMode(e.circle));
  html += evs.length ? '<ul class="plain">' + evs.map(e => `
      <li data-act="open" data-path="${esc(e.path)}"><div class="li-top">
        <span class="dot" style="background:${CIRCLE_COLOR[e.circle]||'var(--muted)'}"></span>${visBadge(e.visibility)}
        <span class="when">${e.time?esc(e.time):'all day'}</span>
      </div><div class="li-title">${e.kind==='reminder'?KIND_ICON.reminder+' ':''}${esc(e.title)}</div></li>`).join('') + '</ul>'
    : `<div class="empty">${esc(t('no_events_today'))}</div>`;
  html += d.daily_log_today
    ? '<div class="hint">✓ Daily log exists — big rocks first (#q2 your tasks).</div>'
    : '<div class="hint">No daily log yet — ask the agent for a morning brief, or run: aicowork new daily-log</div>';
  const otd = d.on_this_day.filter(i => inMode(i.circle));
  if (otd.length)
    html += '<div class="up-group">On this day</div><ul class="plain">' + otd.map(i => `
      <li data-act="open" data-path="${esc(i.path)}"><div class="li-top">
        ${visBadge(i.visibility)}<span class="badge">${i.months_ago} month${i.months_ago>1?'s':''} ago</span>
        <span class="when">${esc(i.date)}</span>${i.kind==='lesson' ? lessonCtx(i) : ''}
      </div><div class="li-title">${i.kind==='lesson' ? '🎓 ' : ''}${esc(i.title)}</div></li>`).join('') + '</ul>';
  $('today').innerHTML = html;
}

function renderSignals(){
  const d = DATA, q = d.q_stats;
  const over = d.overdue_contacts.filter(o => inMode(o.circle));
  const tiles = [
    [d.inbox.length, 'in inbox', d.inbox.length?'':'ok'],
    [d.upcoming.filter(e=>inMode(e.circle)&&e.days_left>=0).length, `upcoming ${ui('horizon_days',14)}d`, '',
     d.upcoming.filter(e=>inMode(e.circle)&&e.days_left<0).length],
    [q.q2_pct===null?'—':q.q2_pct+'%', `Q2 share ${ui('horizon_days',14)}d`, q.q2_pct>=50?'ok':''],
    [over.length, 'overdue contacts', over.length?'':'ok'],
    [d.daily_log_today?'✓':'—', "today's log", d.daily_log_today?'ok':''],
  ];
  $('signals').innerHTML = tiles.map(([n,l,c,over]) =>
    `<div class="tile"><div class="num ${c}">${n}${over?`<span class="sub-badge">${over} overdue</span>`:''}</div><div class="lbl">${l}</div></div>`).join('');
  renderEnergy();
}

function renderEnergy(){
  const el = $('energy-chart');
  if (typeof echarts === 'undefined' || !el) return;
  if (!DATA.energy.length){ el.innerHTML=''; $('energy-wrap').style.display='none'; return }
  $('energy-wrap').style.display='';
  if (energyChart) energyChart.dispose();
  const css = getComputedStyle(document.documentElement);
  energyChart = echarts.init(el, null, {renderer:'svg'});
  energyChart.setOption({
    grid:{left:24,right:8,top:8,bottom:20},
    xAxis:{type:'category', data:DATA.energy.map(e=>e.date.slice(5)),
           axisLabel:{fontSize:10, color:css.getPropertyValue('--muted')}},
    yAxis:{min:1, max:5, interval:1,
           axisLabel:{fontSize:10, color:css.getPropertyValue('--muted')}},
    series:[{type:'line', data:DATA.energy.map(e=>e.energy), smooth:true,
             symbolSize:6, lineStyle:{width:2}}],
    color:[css.getPropertyValue('--work').trim()||'#4a7cff'],
    tooltip:{trigger:'axis'},
  });
}
new ResizeObserver(()=>{ if (energyChart) energyChart.resize(); })
  .observe(document.body);

function renderApps(){
  $('apps').innerHTML = DATA.apps.filter(a => !['dashboard','browse'].includes(a.id))
    .map(a => a.kind==='route'
      ? `<button class="app-tile" data-act="tab" data-tab="${a.target==='/'?'dash':'browse'}">
           <span class="app-name">${esc(a.name)}</span><span class="app-kind">${esc(a.kind)}</span></button>`
      : `<a class="app-tile" href="${esc(a.target)}" target="_blank" rel="noopener" ${a.kind==='service'&&a.command?`title="${esc(t('app.start', {id: a.id}))}"`:''}>
           <span class="app-name">${esc(a.name)}</span><span class="app-kind">${esc(a.kind)} ↗${a.kind==='service'&&a.command?' · '+esc(t('app.start', {id: a.id})):''}</span></a>`)
    .join('') || '<div class="empty">Add apps under apps: in aicowork.yaml — one entry per tool.</div>';
}

/* ---------- collapsible sections (state per-browser via localStorage) ---------- */
const SEC_KEY = 'aicowork.collapsed';
function collapsedSet(){
  try { return new Set(JSON.parse(localStorage.getItem(SEC_KEY) || '[]')) }
  catch(e){ return new Set() }
}
function toggleSec(h){
  const s = collapsedSet();
  const closed = h.parentElement.classList.toggle('closed');
  // A section can render in two homes (e.g. lessons: rail + grid fallback);
  // keep every copy of the same data-sec in step.
  document.querySelectorAll(`h2[data-sec="${h.dataset.sec}"]`).forEach(x =>
    x.parentElement.classList.toggle('closed', closed));
  closed ? s.add(h.dataset.sec) : s.delete(h.dataset.sec);
  try { localStorage.setItem(SEC_KEY, JSON.stringify([...s])) } catch(e){}
  // ECharts inited inside a display:none box has zero size — redraw on reopen.
  if (!closed && h.dataset.sec === 'signals') renderEnergy();
}
function initCollapse(){
  const s = collapsedSet();
  document.querySelectorAll('h2[data-sec]').forEach(h => {
    if (s.has(h.dataset.sec)) h.parentElement.classList.add('closed');
  });
}

function renderRail(){
  const el = $('rail-practices');
  if (!el) return;
  const days = iso => Math.round((new Date(iso) - new Date(DATA.today)) / 864e5);
  const rows = (DATA.practices || [])
    .filter(pr => (pr.status || 'active') === 'active' && inMode(pr.circle));
  el.innerHTML = rows.length ? rows.map(pr => {
    let sub = pr.cadence || '';
    let barHtml = '';
    if (pr.until && pr.start){
      const total = days(pr.until) - days(pr.start);           // challenge length
      const done  = -days(pr.start);                           // days since start
      if (total > 0 && done >= 0 && days(pr.until) >= 0){
        sub = `Day ${Math.min(done + 1, total)}/${total}` + (sub ? ' · ' + sub : '');
        barHtml = `<div class="pr-days"><i style="width:${Math.min(100, (done + 1) / total * 100)}%"></i></div>`;
      } else if (days(pr.until) < 0){
        sub = `ended ${pr.until}` + (sub ? ' · ' + sub : '');
      }
    }
    return `<div class="pr-item" data-act="open" data-path="${esc(pr.path)}">
      <div class="pr-name"><span class="dot" style="background:${CIRCLE_COLOR[pr.circle]||'var(--muted)'}"></span>
        <span>${esc(pr.title)}</span>${visBadge(pr.visibility)}</div>
      <div class="pr-sub">${esc(sub)}</div>${barHtml}</div>`;
  }).join('')
  : '<div class="empty">No active practices — add one in 08_practices/.</div>';
}

function toggleLessons(){ lessonsAll = !lessonsAll; renderLessons(); }

// a lesson's [context] that names a file opens that file (E8); the click must not bubble to the lesson's own row
const lessonCtx = l => l.context
  ? ` <span class="badge link" data-act="openCtx" data-path="${esc(l.context)}" title="${esc(l.context)}">📎 ${esc(l.context.split('/').pop())}</span>` : '';

function renderLessons(){
  const all = DATA.lessons, cap = ui('lessons_shown', 3);
  const total = DATA.lessons_total != null ? DATA.lessons_total : all.length;
  // Same list in two homes: #rail-lessons (>=1480px) and #lessons (grid
  // fallback below that). CSS shows exactly one; we just fill both.
  const targets = [$('lessons'), $('rail-lessons')].filter(Boolean);
  if (!all.length){
    targets.forEach(el => el.innerHTML =
      '<div class="empty">Tag a line with #lesson anywhere — it shows up here.</div>');
    return;
  }
  const rows = lessonsAll ? all : all.slice(0, cap);
  // Only claim "all" when the served page really is everything; otherwise say
  // what is on screen vs what exists, so the count never overstates.
  const toggle = total <= cap ? ''
    : lessonsAll
      ? `<div class="show-more" data-act="lessons">⌃ show less</div>`
      : (total <= all.length
          ? `<div class="show-more" data-act="lessons">⌄ show all (${total})</div>`
          : `<div class="show-more" data-act="lessons">⌄ show ${all.length} newest (of ${total})</div>`);
  targets.forEach(el => el.innerHTML =
    '<ul class="plain">' + rows.map(l => `
        <li data-act="open" data-path="${esc(l.path)}">
          <div class="li-top"><span class="when">${esc(l.date)}</span>${lessonCtx(l)}</div>
          <div class="li-title">${esc(l.text)}</div></li>`).join('') + '</ul>' + toggle);
}

/* ---------- trust anchor banner ----------
   A steering file (policy, config security, instruction file, check_tokens,
   modules.lock) changed since the owner anchored it: say so at the top. */
function renderAnchor(){
  let el = $('anchor-banner');
  if (!el){ el = document.createElement('div'); el.id = 'anchor-banner';
            const tb = document.querySelector('.topbar'); (tb ? tb.parentNode : document.body).insertBefore(el, tb ? tb.nextSibling : null); }
  const a = DATA.anchor || {state:'unchecked', drifted:[]};
  if (a.state === 'drift'){
    el.className = 'anchor drift';
    el.textContent = t('anchor.drift', {files: a.drifted.join(', ')});
  } else if (a.state === 'none' || a.state === 'legacy'){
    el.className = 'anchor none';
    el.textContent = t('anchor.none');
  } else { el.className = ''; el.textContent = ''; }
}

function renderDash(){
  renderAnchor(); renderToday(); renderSignals(); renderApps(); renderLessons(); renderRail();
  const d = DATA;
  $('foot').textContent = 'scanned ' + d.generated_at +
    ' · last triage: ' + d.last_triage;
  // keep-an-eye, grouped
  const groups = [[t('rem.overdue_group'), e=>e.days_left<0],
                  ['Today', e=>e.days_left===0], ['Tomorrow', e=>e.days_left===1],
                  ['This week', e=>e.days_left>1&&e.days_left<=7],
                  ['Later', e=>e.days_left>7]];
  let html = '';
  for (const [label, f] of groups){
    const es = d.upcoming.filter(e => inMode(e.circle)).filter(f);
    if (!es.length) continue;
    html += `<div class="up-group">${label}</div><ul class="plain">` + es.map(e => `
      <li data-act="open" data-path="${esc(e.path)}"><div class="li-top">
        <span class="dot" style="background:${CIRCLE_COLOR[e.circle]||'var(--muted)'}"></span>${visBadge(e.visibility)}
        <span class="when">${esc(e.date)}${e.time?' '+esc(e.time):''}</span>
        ${e.kind==='reminder' ? remBadge(e)
          : `<span class="badge">${e.days_left===0?'today':e.days_left===1?'tomorrow':'in '+e.days_left+'d'}</span>`}
      </div>${e.kind==='reminder'
        ? `<div class="li-title rem-row"><span>${KIND_ICON.reminder} ${esc(e.title)}</span>${remDoneBtn(e)}</div>`
        : `<div class="li-title">${esc(e.title)}</div>`}</li>`).join('') + '</ul>';
  }
  const upTitle = $('upcoming-title'), enTitle = $('energy-title');
  if (upTitle) upTitle.textContent = t('keep_eye', {n: ui('horizon_days',14)});
  if (enTitle) enTitle.textContent = t('energy', {n: ui('energy_days',30)});
  $('upcoming').innerHTML = html ||
    `<div class="empty">Nothing in the next ${ui('horizon_days',14)} days. Quick-add or drop into 00_inbox.</div>`;

  const bal = d.balance, max = Math.max(1, ...Object.values(bal)
    .map(b => Object.values(b).reduce((a,x)=>a+x,0)));
  $('balance').innerHTML = ['family','work','friend','health'].map(c => {
    const b = bal[c], total = Object.values(b).reduce((a,x)=>a+x,0);
    return `<div class="bar-row" data-c="${c}" data-act="balance" data-circle="${c}">
      <span class="lbl">${c}</span>
      <div class="bar-track"><div class="bar-fill"
        style="width:${total/max*100}%;background:${CIRCLE_COLOR[c]}"></div></div>
      <span class="val">${total}</span></div>`;
  }).join('') + (d.unassigned ?
    `<div class="bar-note">${d.unassigned} item(s) without a circle yet</div>` : '');
  document.querySelectorAll('.bar-row').forEach(row => {
    const b = bal[row.dataset.c];
    hover(row, `<b>${row.dataset.c}</b><br>${b.event} events · ${b.email} emails<br>` +
               `${b.persona} personas · ${b.project} projects<br>` +
               `${b.practice} practices`);
  });

  showMonth();

  $('inbox').innerHTML = (d.inbox.length
    ? d.inbox.map(f => `<div class="file">${esc(f)}</div>`).join('') +
      `<div class="hint">Say “triage my inbox” in an agent session.</div>`
    : `<div class="empty">${esc(t('inbox_empty'))}</div>`) + renderTriagePlans(d.triage_plans || []);

  $('results').innerHTML = d.results.length
    ? d.results.map(r => `<div class="file ${r.is_md?'link':''}"
        ${r.is_md?`data-act="open" data-path="${esc(r.path)}"`:''}>
        <span>${esc(r.name)}</span><span class="date">${esc(r.modified)}</span></div>`).join('')
    : `<div class="empty">${esc(t('no_results'))}</div>`;
}

/* ---------- calendar ---------- */
function navCal(s){ calM+=s; if(calM<0){calM=11;calY--} if(calM>11){calM=0;calY++}
  showMonth(); }
function goToday(){ const t=new Date(DATA.today+'T00:00:00');
  calY=t.getFullYear(); calM=t.getMonth(); showMonth(); }

/* ---------- calendar occurrences: one cache per month (D7, plan 2) ----------
   /api/data brings the current month ±1; any other month is fetched on demand
   (only the calendar card is masked), ±1 around it is prefetched when idle.
   load() clears the cache: the files are the truth, the cache is a convenience. */
let OCC = {};                  // 'YYYY-MM' -> [rows]
const ym = (y, m) => `${y}-${String(m+1).padStart(2,'0')}`;
function occStore(items){ for (const it of items){ const k = it.date.slice(0,7); (OCC[k] = OCC[k] || []).push(it); } }
function occSeed(){ OCC = {}; const o = DATA.occurrences; if (!o) return;
  // mark every month of the served range as known, even when empty
  let [y, m] = o.from.split('-').map(Number); const end = o.to.slice(0,7);
  for (;;){ const k = ym(y, m-1); OCC[k] = OCC[k] || []; if (k === end) break; m++; if (m > 12){ m = 1; y++; } }
  occStore(o.items); }
async function occFetch(y, m){
  const k = ym(y, m);
  if (OCC[k]) return OCC[k];
  const from = `${k}-01`, last = new Date(y, m+1, 0).getDate(), to = `${k}-${String(last).padStart(2,'0')}`;
  const r = await fetch(`/api/occurrences?from=${from}&to=${to}`);
  if (!r.ok) throw new Error('occurrences ' + r.status);
  const d = await r.json();
  OCC[k] = [];                 // known from now on, even when empty
  occStore(d.items);
  return OCC[k];
}
async function showMonth(){
  const k = ym(calY, calM), card = $('calendar');
  if (!OCC[k]){
    card.classList.add('loading');
    try { await occFetch(calY, calM); }
    catch(e){ card.classList.remove('loading'); toast(t('cal.load_failed'), 'err'); return; }
    card.classList.remove('loading');
  }
  renderCalendar();
  const idle = window.requestIdleCallback || (fn => setTimeout(fn, 300));
  idle(() => { for (const s of [-1, 1]){ let y = calY, m = calM + s; if (m < 0){ m = 11; y--; } if (m > 11){ m = 0; y++; }
                 occFetch(y, m).catch(() => {}); } });
}

/* runtime knobs from the instance's aicowork.yaml, served via /api/data.ui.
   Defaults mirror config.py _DEFAULTS. */
function ui(k, dflt){ return (DATA && DATA.ui && DATA.ui[k] != null) ? DATA.ui[k] : dflt; }

function renderCalendar(){
  const byDay = {};
  // the month shown and its neighbours (the grid shows a few days of each); events before reminders
  for (const s of [-1, 0, 1]){ let y = calY, m = calM + s; if (m < 0){ m = 11; y--; } if (m > 11){ m = 0; y++; }
    (OCC[ym(y, m)] || []).filter(e => inMode(e.circle)).forEach(e => { (byDay[e.date]=byDay[e.date]||[]).push(e); }); }
  for (const k in byDay) byDay[k].sort((a, b) => (a.kind==='reminder') - (b.kind==='reminder'));
  const first = new Date(calY, calM, 1);
  const off = (first.getDay()+6)%7, dim = new Date(calY,calM+1,0).getDate(),
        dimPrev = new Date(calY,calM,0).getDate();
  $('calmonth').textContent = first.toLocaleDateString(locale(),{month:'long',year:'numeric'});
  let cells = [];
  for (let i=0;i<42;i++){
    let n=i-off+1, y=calY, m=calM, dimd=false;
    if (n<1){ n=dimPrev+n; m--; dimd=true } else if (n>dim){ n=n-dim; m++; dimd=true }
    if (m<0){m=11;y--} if (m>11){m=0;y++}
    const iso = `${y}-${String(m+1).padStart(2,'0')}-${String(n).padStart(2,'0')}`;
    cells.push({iso,n,dimd,ev:byDay[iso]||[]});
  }
  if (cells.slice(35).every(c=>c.dimd)) cells = cells.slice(0,35);
  const rows=[];
  for (let r=0;r<cells.length/7;r++){
    rows.push('<tr>'+cells.slice(r*7,r*7+7).map(c=>{
      const cls=[c.dimd&&'dim', c.iso===DATA.today&&'today'].filter(Boolean).join(' ');
      const cap=ui('max_events_per_day',2), hotDays=ui('hot_days',2);
      const shown=c.ev.slice(0,cap).map(e=>{
        const st=(e.status||'').toLowerCase();
        const diff=(new Date(e.date)-new Date(DATA.today))/864e5;
        if (e.kind === 'reminder'){
          // a reminder window: done ✓ dimmed, overdue red, open/upcoming within hot_days hot
          const cls = e.state==='done' ? ' done' : e.state==='overdue' ? ' overdue'
            : (diff>=0&&diff<=hotDays) ? ' hot' : '';
          const span = e.span ? ` (${e.span})` : '';
          return `<div class="chip rem${cls}" data-act="open" data-path="${esc(e.path)}"
            title="${esc(e.title)}${span} — ${esc(e.state)}">
            <span class="ico">${KIND_ICON.reminder}</span>
            <span style="overflow:hidden;text-overflow:ellipsis">${e.state==='done'?'✓ ':''}${esc(e.title)}${span}</span></div>`;
        }
        const cls = st==='done' ? ' done'
          : ['cancelled','canceled','postponed'].includes(st) ? ' cancelled'
          : (diff>=0&&diff<=hotDays) ? ' hot' : '';
        return `<div class="chip${cls}" data-act="open" data-path="${esc(e.path)}"
          title="${esc(e.title)}${st?' — '+esc(st):''}">
          <span class="dot" style="background:${CIRCLE_COLOR[e.circle]||'var(--muted)'}"></span>
          <span style="overflow:hidden;text-overflow:ellipsis">${st==='done'?'✓ ':''}${esc(e.title)}</span></div>`;
      }).join('');
      const more=c.ev.length>cap?`<div class="more">+${c.ev.length-cap} more</div>`:'';
      return `<td class="${cls}"><span class="d">${c.n}</span>${shown}${more}</td>`;
    }).join('')+'</tr>');
  }
  $('calendar').innerHTML =
    `<table class="cal"><thead><tr>${['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
      .map(x=>`<th>${x}</th>`).join('')}</tr></thead><tbody>${rows.join('')}</tbody></table>`;
}

/* ---------- browse ---------- */
function onSearchInput(){
  if (TAB!=='browse') setTab('browse');
  clearTimeout(qTimer); qTimer=setTimeout(doSearch, 220);
}
async function doSearch(){
  const q = $('q').value, params = new URLSearchParams({
    q, kind:$('f-kind').value, circle:$('f-circle').value, status:$('f-status').value });
  const r = await (await fetch('/api/search?'+params)).json();
  if (DATA) renderSidebar();
  $('rcount').textContent = r.total + ' item' + (r.total===1?'':'s') +
    (q?` for “${q}”`:'');
  /* i.snippet is escaped server-side (store.search -> security.safe_snippet);
     only its <mark> highlights are markup. */
  $('rlist').innerHTML = r.items.map(i => `
    <div class="result" data-act="open" data-path="${esc(i.path)}">
      <div class="r-top">
        <span class="dot" style="background:${CIRCLE_COLOR[i.circle]||'var(--muted)'}"></span>${visBadge(i.visibility)}
        <span class="kindtag">${KIND_ICON[i.kind]||''} ${esc(i.kind)}</span>
        ${i.date?`<span>${esc(i.date)}</span>`:''}
        ${i.status?`<span>· ${esc(i.status)}</span>`:''}
        <span class="rpath">${esc(i.path)}</span>
      </div>
      <div class="r-title">${esc(i.title)}</div>
      ${i.snippet?`<div class="r-snip">${i.snippet}</div>`:''}
    </div>`).join('') || '<div class="empty">No matches.</div>';
}

/* ---------- drawer ---------- */
let NAV = [];
function drawerBack(){ const p = NAV.pop(); updateBack(); if (p) openItem(p, false); }
function updateBack(){ $('dr-back').style.display = NAV.length ? '' : 'none'; }

async function openItem(path, push){
  const body = $('dr-body');
  body.classList.add('loading');
  const r = await fetch('/api/item?path='+encodeURIComponent(path));
  if (!r.ok){ body.classList.remove('loading'); toast('Cannot open: '+path, 'err'); return }
  if (push !== false && CUR && CUR.path !== path){ NAV.push(CUR.path); }
  updateBack();
  CUR = await r.json();
  $('dr-path').textContent = CUR.path;
  const m = CUR.meta||{};
  $('dr-meta').innerHTML = [
    m.type && `<span class="kindtag">${KIND_ICON[m.type]||''} ${esc(m.type)}</span>`,
    m.circle && `<span class="kindtag" style="border-color:${CIRCLE_COLOR[m.circle]||'var(--grid)'}">
      ● ${esc(m.circle)}</span>`,
    m.date && `<span class="kindtag">${esc(m.date)}${m.time?' '+esc(m.time):''}</span>`,
    m.status && `<span class="kindtag">${esc(m.status)}</span>`,
    visControl(m.visibility),
  ].filter(Boolean).join('');
  // CUR.html is sanitised server-side (security.SafeHtmlExtension): raw HTML
  // in notes arrives escaped, links/images are scheme-filtered.
  $('dr-body').innerHTML = CUR.html || '<p class="empty">(empty)</p>';
  $('dr-edit').style.display = CUR.editable === false ? 'none' : '';
  $('dr-body').scrollTop = 0;
  requestAnimationFrame(() => $('dr-body').classList.remove('loading'));
  exitEditUI();
  $('ovl').style.display='block';
  $('drawer').classList.add('open');
}
function closeDrawer(){ $('drawer').classList.remove('open');
  $('ovl').style.display='none'; CUR=null; NAV=[]; updateBack(); }
function toggleEdit(){
  if (!CUR) return;
  $('editor').value = CUR.raw;
  $('dr-body').style.display='none';
  $('editor').style.display='block';
  $('dr-foot').style.display='flex';
  $('dr-edit').style.display='none';
  $('dr-msg').textContent='';
}
function exitEditUI(){
  $('dr-body').style.display='block';
  $('editor').style.display='none';
  $('dr-foot').style.display='none';
  $('dr-edit').style.display = CUR && CUR.editable === false ? 'none' : '';
}
function cancelEdit(){ exitEditUI(); }
async function saveItem(){
  const r = await fetch('/api/item', { method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ path:CUR.path, raw:$('editor').value, mtime:CUR.mtime }) });
  if (r.status===409){ $('dr-msg').textContent='⚠ File changed on disk — close and reopen.'; return }
  if (r.status===413){ $('dr-msg').textContent='⚠ Too large for the viewer editor — edit it in your editor.'; return }
  if (!r.ok){ $('dr-msg').textContent='⚠ Save failed ('+r.status+')'; return }
  await openItem(CUR.path);
  load();
}

/* ---------- reminders (CONVENTIONS "Reminders") ----------
   The state is computed by the server from the file; Done writes `last_done`
   (today) and nothing else, then the dashboard reloads. */
function remBadge(e){
  const s = e.state;
  const txt = s==='overdue' ? t('rem.overdue', {n: -e.days_left}) + (e.missed>1 ? ' · ' + t('rem.missed', {n: e.missed}) : '')
            : s==='expired' ? t('rem.expired')
            : s==='due' ? t('rem.due_today')
            : t('rem.in_days', {n: e.days_left});
  const cls = s==='overdue' || s==='expired' ? 'badge warn' : 'badge';
  return `<span class="${cls}">${esc(txt)}</span>`;
}
// Done only where a window is open now: on an upcoming one it would change nothing
const remDoneBtn = e => e.state==='due' || e.state==='overdue'
  ? `<button class="rem-done" data-act="remDone" data-path="${esc(e.path)}" data-mtime="${esc(e.mtime)}">${esc(t('rem.done'))}</button>` : '';
/* ---------- triage plans: the agent proposed, the owner applies (rc.6, E7) ---------- */
function renderTriagePlans(plans){
  if (!plans.length) return '';
  return plans.map(p => `<div class="plan"><div class="up-group">${esc(t('plan.title', {name: p.name}))}</div>` +
    (p.error ? `<div class="empty">${esc(t('plan.error'))}: ${esc(p.error)}</div>` :
      '<ul class="plain">' + p.moves.map(m => `<li><div class="li-top"><span class="badge">${esc(m.type||'note')}</span>` +
        `<span class="dot" style="background:${CIRCLE_COLOR[m.circle]||'var(--muted)'}"></span></div>` +
        `<div class="li-title">${esc(m.from)} → ${esc(m.to)}</div>${m.note?`<div class="hint">${esc(m.note)}</div>`:''}</li>`).join('') + '</ul>') +
    `<div class="plan-actions">${p.error ? '' : `<button class="btn primary" data-act="planApply" data-name="${esc(p.name)}">${esc(t('plan.apply'))}</button>`}` +
    `<button class="btn" data-act="planDismiss" data-name="${esc(p.name)}">${esc(t('plan.dismiss'))}</button></div></div>`).join('');
}

async function triagePlan(name, action){
  const btns = [...document.querySelectorAll(`[data-name="${CSS.escape(name)}"]`)];
  if (btns.some(b => b.disabled)) return;
  btns.forEach(b => { b.disabled = true; });
  let r;
  try {
    r = await fetch('/api/triage/apply', { method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ name, action }) });
  } catch(e){ btns.forEach(b => { b.disabled = false; }); toast(t('load_failed'), 'err'); return; }
  if (!r.ok){ let m=''; try { m=(await r.json()).detail||'' } catch(_){}
              btns.forEach(b => { b.disabled = false; }); toast(t('plan.failed') + ' ('+r.status+') '+m, 'err'); return }
  let res = {}; try { res = await r.json(); } catch(_){}
  toast(action === 'apply' ? '✓ ' + t('plan.applied', {n: res.moves || 0}) : t('plan.dismissed'));
  load();
}

async function reminderDone(path, mtime){
  // one request at a time per button: a second click would only earn a 409
  const btns = [...document.querySelectorAll(`.rem-done[data-path="${CSS.escape(path)}"]`)];
  if (btns.some(b => b.disabled)) return;
  btns.forEach(b => { b.disabled = true; b.textContent = '…'; });
  // the mtime the dashboard was rendered with: a file changed since -> 409
  let r;
  try {
    r = await fetch('/api/reminder/done', { method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ path, mtime }) });
  } catch(e){ btns.forEach(b => { b.disabled = false; b.textContent = t('rem.done'); }); toast(t('load_failed'), 'err'); return; }
  if (r.status===409){ toast('File changed on disk — reloaded, check and try again', 'err'); load(); return }
  if (!r.ok){ let m=''; try { m=(await r.json()).detail||'' } catch(_){}
              toast('Done failed ('+r.status+') '+m, 'err'); return }
  const row = (DATA.upcoming || []).find(e => e.path === path);
  let res = {}; try { res = await r.json(); } catch(_){}
  toast('✓ ' + (row ? row.title : path) + (res.missed_added ? ` · ${t('rem.missed', {n: res.missed_added})} ` + t('rem.missed_recorded') : ''));
  load();
}

/* Relative links inside rendered markdown: the server has no route for
   /04_projects/... — resolve them against the open item's path and route
   .md files back into the drawer, everything else through /raw. */
$('dr-body').addEventListener('click', e => {
  const link = e.target.closest('a[href]');
  if (!link || !CUR) return;
  const href = link.getAttribute('href');
  if (href.startsWith('#')) return;
  if (/^[a-z][a-z0-9+.-]*:/i.test(href)){ link.target='_blank'; return; }  // http(s), mailto…
  e.preventDefault();
  const resolved = decodeURIComponent(
    new URL(href, 'http://x/' + CUR.path).pathname.slice(1));
  if (resolved.toLowerCase().endsWith('.md')) openItem(resolved);
  else window.open('/raw?path=' + encodeURIComponent(resolved), '_blank');
});

/* ---------- visibility control (drawer) ----------
   The ONLY place a human raises visibility — a deliberate click on a specific
   file they have just read. Lowering applies at once; raising asks once more.
   Writes go through the same POST /api/item as the editor (mtime-guarded). */
function visControl(v){
  v = visOf(v);
  return `<span class="kindtag vis-ctl" id="vis-ctl">${VIS[v].i}
    <select id="vis-sel" data-change="vis" title="visibility — who may this file reach?">
      ${VIS_ORDER.map(o => `<option value="${o}" ${o===v?'selected':''}>${VIS[o].l}</option>`).join('')}
    </select></span>`;
}
function visPick(next){
  if (!CUR) return;
  const cur = visOf((CUR.meta||{}).visibility);
  if (next === cur) return;
  if (VIS_ORDER.indexOf(next) < VIS_ORDER.indexOf(cur)) { visApply(next); return; }   // lowering: just do it
  const ctl = $('vis-ctl');
  ctl.innerHTML = `raise to ${VIS[next].i} ${VIS[next].l}? this file may then leave the machine
    <button class="btn" data-act="visApply" data-v="${next}">yes</button>
    <button class="btn" data-act="visCancel">no</button>`;
}
function visPatchRaw(raw, v){
  // frontmatter = first '---' block; replace or insert the visibility line
  if (!raw.startsWith('---\n')) return '---\nvisibility: ' + v + '\n---\n' + raw;
  const end = raw.indexOf('\n---', 4);
  if (end < 0) return raw;
  let fm = raw.slice(4, end);
  if (/^visibility:.*$/m.test(fm)) fm = fm.replace(/^visibility:.*$/m, 'visibility: ' + v);
  else if (/^type:.*$/m.test(fm)) fm = fm.replace(/^(type:.*)$/m, '$1\nvisibility: ' + v);
  else fm = 'visibility: ' + v + '\n' + fm;
  return '---\n' + fm + raw.slice(end);
}
async function visApply(v){
  if (!CUR) return;
  const r = await fetch('/api/item', { method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ path:CUR.path, raw:visPatchRaw(CUR.raw, v), mtime:CUR.mtime }) });
  if (r.status===409){ toast('File changed on disk — reopen and retry', 'err'); return; }
  if (!r.ok){ toast('Could not set visibility ('+r.status+')', 'err'); return; }
  toast(`visibility → ${VIS[v].i} ${VIS[v].l}`);
  await openItem(CUR.path, false);
  load();
}

/* ---------- quick-add "related to": multi-select combobox with chips ---------- */
let qaRelated = [];    // [{path,title,kind,circle}]
let comboIdx = -1;

const QA_RELATED_MAX = 5;

function comboItems(q){
  if (qaRelated.length >= QA_RELATED_MAX) return [];
  q = q.trim().toLowerCase();
  const picked = new Set(qaRelated.map(r => r.path));
  const all = (DATA?.relatable || [])
    .filter(r => !picked.has(r.path))
    .sort((x,y) => (x.kind==='project'?0:1)-(y.kind==='project'?0:1)
                   || (x.status==='active'?0:1)-(y.status==='active'?0:1)
                   || x.title.localeCompare(y.title));
  return (q ? all.filter(r => (r.title+' '+r.path).toLowerCase().includes(q)) : all)
    .slice(0, 50);   // the list scrolls — show everything reasonable
}

function comboRender(items){
  const list = $('qa-related-list');
  if (!items.length){ list.style.display='none'; comboIdx=-1; return }
  const labels = { project:'📁 Projects', practice:'🔁 Practices' };
  let html = '', lastKind = null, i = 0;
  for (const r of items){
    if (r.kind !== lastKind){ html += `<div class="combo-group">${labels[r.kind]||r.kind}</div>`; lastKind = r.kind; }
    html += `<div class="combo-it ${i===comboIdx?'sel':''}" data-i="${i}">
      <span>${KIND_ICON[r.kind]||''} ${esc(r.title)}${r.status&&r.status!=='active'?' <i>('+esc(r.status)+')</i>':''}</span>
      <span class="cpath">${esc(r.path)}</span></div>`;
    i += 1;
  }
  list.innerHTML = html;
  list.style.display='block';
  list.querySelectorAll('.combo-it').forEach(el => {
    el.onmousedown = e => { e.preventDefault(); comboPick(items[+el.dataset.i]); };
  });
}

function comboPick(r){
  if (qaRelated.length >= QA_RELATED_MAX){
    toast('At most ' + QA_RELATED_MAX + ' related items — remove a chip first', 'err'); return }
  qaRelated.push(r);
  renderChips();
  const inp = $('qa-related-input');
  inp.value = ''; comboIdx = -1;
  if (r.circle && !$('qa-circle').value) $('qa-circle').value = r.circle;
  $('qa-related-list').style.display='none';   // close after pick — the open list
  inp.focus();                                 // covers the save buttons; typing reopens
}

function chipRemove(i){ qaRelated.splice(i,1); renderChips();
  comboRender(comboItems($('qa-related-input').value)); }

function renderChips(){
  $('qa-chips').innerHTML = qaRelated.map((r,i) =>
    `<span class="chip-tag">${KIND_ICON[r.kind]||''} ${esc(r.title)}
       <b data-act="chipRemove" data-i="${i}" title="Remove">×</b></span>`).join('');
}

function comboInit(){
  const inp = $('qa-related-input'), list = $('qa-related-list');
  inp.addEventListener('input', () => { comboIdx=-1; comboRender(comboItems(inp.value)); });
  inp.addEventListener('focus', () => comboRender(comboItems(inp.value)));
  // clicking the already-focused input fires no 'focus' event — reopen on click too
  inp.addEventListener('click', () => {
    if ($('qa-related-list').style.display !== 'block')
      comboRender(comboItems(inp.value));
  });
  inp.addEventListener('blur', () => setTimeout(()=>list.style.display='none', 150));
  inp.addEventListener('keydown', e => {
    const items = comboItems(inp.value);
    if (e.key==='ArrowDown'){ e.preventDefault(); comboIdx=Math.min(comboIdx+1, items.length-1); comboRender(items); }
    else if (e.key==='ArrowUp'){ e.preventDefault(); comboIdx=Math.max(comboIdx-1, 0); comboRender(items); }
    else if (e.key==='Enter' && list.style.display==='block' && comboIdx>=0){
      e.preventDefault(); e.stopPropagation(); comboPick(items[comboIdx]); }
    else if (e.key==='Backspace' && !inp.value && qaRelated.length){
      chipRemove(qaRelated.length-1); }
    else if (e.key==='Escape' && list.style.display==='block'){
      e.stopPropagation(); list.style.display='none'; comboIdx=-1; }
  });
}
comboInit();

/* ---------- quick add ---------- */
function qaOpen(){ $('qa').style.display='flex'; $('qa-title').focus(); }
function qaClose(){ $('qa').style.display='none';
  $('qa-title').value=''; $('qa-text').value=''; $('qa-circle').value='';
  $('qa-related-input').value=''; qaRelated=[]; renderChips(); }
async function qaSave(){
  const title = $('qa-title').value.trim();
  if (!title){ $('qa-title').focus(); return }
  const r = await fetch('/api/quickadd', { method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ title, text:$('qa-text').value,
      circle:$('qa-circle').value, related:qaRelated.map(r=>r.path) }) });
  if (!r.ok){ let why = ''; try { why = (await r.json()).detail || '' } catch(e){}
    toast('Quick add failed ('+r.status+(why?': '+why:'')+')', 'err'); return }
  qaClose(); load();
  toast('Dropped into inbox ✓');
}

/* ---------- sidebar toggle ---------- */
function toggleSide(){
  const hidden = document.body.classList.toggle('side-hidden');
  try { localStorage.setItem('side-hidden', hidden ? '1' : '') } catch(e){}
}
try { if (localStorage.getItem('side-hidden'))
        document.body.classList.add('side-hidden'); } catch(e){}

/* ---------- task-list checkboxes: toggle in raw, save, re-render ---------- */
const TASK_RE = /^([ \t]*[-*][ \t]+)\[( |x|X)\]/gm;
$('dr-body').addEventListener('change', async e => {
  const box = e.target;
  if (box.type !== 'checkbox' || !CUR) return;
  const boxes = [...$('dr-body').querySelectorAll('input[type=checkbox]')];
  const idx = boxes.indexOf(box);
  let n = -1;
  const raw = CUR.raw.replace(TASK_RE, (m, pre, state) => {
    n += 1;
    if (n !== idx) return m;
    return pre + (state === ' ' ? '[x]' : '[ ]');
  });
  if (n < idx){ box.checked = !box.checked; return }   // html/raw out of sync — bail
  const r = await fetch('/api/item', { method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ path: CUR.path, raw, mtime: CUR.mtime }) });
  if (!r.ok){
    box.checked = !box.checked;
    toast(r.status===409 ? 'File changed on disk — reopen it.' :
          r.status===403 ? 'This file is read-only in the viewer.' :
          'Save failed ('+r.status+')', 'err');
    return;
  }
  await openItem(CUR.path);   // refresh raw + mtime + strikethrough styling
});

/* ---------- keyboard ---------- */
const typing = () => ['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName);
document.addEventListener('keydown', e => {
  if (e.key==='Escape'){ if ($('qa').style.display==='flex') qaClose(); else closeDrawer(); }
  if (e.key==='/' && !typing()){ e.preventDefault(); $('q').focus(); }
  /* Quick add: Ctrl/Cmd+I. A bare letter is ambiguous the moment focus is not in a
     field, so the modifier carries it — and because it is unambiguous, it also works
     while typing (e.g. straight from the search box). */
  if ((e.key==='i' || e.key==='I') && (e.ctrlKey||e.metaKey) && !e.shiftKey && !e.altKey
      && $('qa').style.display!=='flex' && !$('drawer').classList.contains('open')){
    e.preventDefault(); qaOpen();
  }
  if (e.key==='Enter' && (e.ctrlKey||e.metaKey)){
    if ($('qa').style.display==='flex') qaSave();
    else if ($('editor').style.display==='block') saveItem();
  }
});

initCollapse();
load();
setInterval(()=>{ if (!CUR && $('qa').style.display!=='flex') load(); }, 60000);

// sticky topbar: show a hairline + shadow only once the page has scrolled
(() => { const tb = document.querySelector('.topbar'); if (!tb) return;
  const f = () => tb.classList.toggle('stuck', window.scrollY > 4);
  addEventListener('scroll', f, { passive:true }); f(); })();
