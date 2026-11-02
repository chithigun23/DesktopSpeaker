/* Desktop Speaker project site.
   Part 1 renders the page sections from data/specs.json, data/bom.json and data/files.json.
   Part 2 is the 3D viewer: it reads cad/meta.json and loads the glTF files it names (default cad/enclosure.glb
   and cad/pcb.glb), and stays usable, with a clear message, when any of them is missing.
   No build step, no external runtime dependency (three.js r128 is vendored in lib/). */
'use strict';
const $ = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmtBytes = b => b == null ? '' : b >= 1e6 ? (b / 1e6).toFixed(1) + ' MB' : b >= 1e3 ? Math.round(b / 1e3) + ' kB' : b + ' B';
async function getJSON(url) {
  const r = await fetch(url, {cache: 'no-cache'});
  if (!r.ok) throw new Error(url + ': HTTP ' + r.status);
  return r.json();
}
const STATE = {specs: null, bom: null, files: null, meta: null, cadStatus: null, srcMap: new Map(), refIndex: new Map()};

/* ------------------------------------------------------------------ theme */
{
  const btn = $('theme'), root = document.documentElement;
  const label = () => { btn.textContent = 'Theme: ' + (root.dataset.theme || 'auto'); };
  btn.addEventListener('click', () => {
    const next = {undefined: 'light', light: 'dark', dark: undefined}[root.dataset.theme];
    if (next) root.dataset.theme = next; else delete root.dataset.theme;
    try { next ? localStorage.setItem('dsTheme', next) : localStorage.removeItem('dsTheme'); } catch (e) {}
    label();
  });
  label();
}

/* ------------------------------------------------------------------ helpers for rendering */
function srcLink(src) {
  if (!src) return '';
  const parts = String(src).split(/\s*[;,]\s*/).filter(Boolean);
  return '<span class="src">' + parts.map(p => {
    const path = p.replace(/\s*\(.*\)$/, '').replace(/#.*$/, '').replace(/:\d+(-\d+)?$/, '');
    const href = STATE.srcMap.get(path);
    return href ? `<a href="${esc(href)}">${esc(p)}</a>` : esc(p);
  }).join('<br>') + '</span>';
}
function statusTag(s) {
  if (!s) return '';
  const t = String(s).toLowerCase();
  let cls = '';
  if (/^(pass|verified|done|decided|maker|accepted|in-stock)/.test(t) || /\bverified\b(?! *(no|not))/.test(t) && !/unverified/.test(t)) cls = 'good';
  if (/unverified|assum|estimate|open|pending|proposal|recommend|calculated|research|not run|partial|in progress|unproven|draft|stale|substitut|below/.test(t)) cls = 'find';
  if (/^fixed/.test(t)) cls = 'good';
  if (/^decision|^note|^info/.test(t)) cls = 'src';
  if (/^fail|stock-zero|unresolved|missing|superseded|conflict|not fab|^problem/.test(t)) cls = 'bad';
  return `<span class="tag ${cls}">${esc(s)}</span>`;
}
function rows(tbodyId, list, cols) {
  const tb = $(tbodyId);
  if (!tb) return;
  if (!list || !list.length) { tb.innerHTML = `<tr><td colspan="${cols.length}" class="note">No entries.</td></tr>`; return; }
  tb.innerHTML = list.map(o => '<tr>' + cols.map(c => {
    if (typeof c === 'function') return c(o);
    if (c === 'src') return `<td>${srcLink(o.src)}</td>`;
    if (c === 'status' || c === 'result') return `<td>${statusTag(o[c])}</td>`;
    return `<td class="tx">${esc(o[c])}</td>`;
  }).join('') + '</tr>').join('');
}
function dlist(id, list, kk = 'k', vk = 'v') {
  const el = $(id);
  if (!el) return;
  el.innerHTML = (list || []).map(o => `<dt>${esc(o[kk])}</dt><dd>${esc(o[vk])}${o.status ? ' ' + statusTag(o.status) : ''}${o.src ? '<br>' + srcLink(o.src) : ''}</dd>`).join('') || '<dt>none</dt><dd></dd>';
}

/* ------------------------------------------------------------------ specs */
function renderSpecs(s) {
  if (s.generated) { $('updated').textContent = s.generated; $('specsmeta').textContent = 'facts as of ' + s.generated; }
  dlist('overview', s.overview);
  dlist('mech', s.mechanical);
  $('blocks').innerHTML = (s.blocks || []).map(b => `<div class="blk"><b>${esc(b.name)}</b><span class="p">${esc(b.parts)}</span><span>${esc(b.role)}</span>${b.connects_to ? `<span class="c">→ ${esc(b.connects_to)}</span>` : ''}${b.status ? `<span>${statusTag(b.status)}</span>` : ''}${srcLink(b.src)}</div>`).join('');
  rows('audio', s.audio, ['item', 'value', 'detail', 'status', 'src']);
  rows('rails', s.rails, ['rail', 'voltage', 'source', 'load_or_budget', 'enable', 'status', 'src']);
  rows('budget', s.power_budget, ['k', 'v', 'detail', 'status', 'src']);
  rows('charge', s.charge_policy, ['k', 'v', 'detail', 'status', 'src']);
  rows('fwstates', s.firmware_states, [o => `<td class="m">${esc(o.state)}</td>`, 'description', 'src']);
  rows('fwopen', s.firmware_open, ['item', 'detail', 'src']);
  const p = s.pcb || {};
  dlist('pcbfacts', p.facts);
  rows('stackup', p.stackup, [o => `<td class="m">${esc(o.layer)}</td>`, 'role']);
  rows('rules', p.rules, ['k', 'v', 'src']);
  rows('routing', p.routing_status, ['k', 'v', 'status', 'src']);
  rows('fab', p.fab_outputs, ['k', 'v', 'status', 'src']);
  const a = s.assembly || {};
  $('asmsum').textContent = a.summary || '';
  dlist('asmsteps', a.steps);
  dlist('asmprofile', a.profile, 'stage', 'v');
  $('asmnotes').innerHTML = (a.notes || []).map(n => `<li>${esc(n.v)} ${srcLink(n.src)}</li>`).join('');
  renderVerification();
  renderOpen();
}
function renderVerification() {
  const list = [...((STATE.specs && STATE.specs.verification) || [])];
  const cs = STATE.cadStatus;
  if (cs && Array.isArray(cs.checks)) for (const c of cs.checks) list.unshift({area: 'CAD export', check: c.check || c.name || '', result: c.result || c.status || '', detail: c.detail || '', src: 'cad/cad_status.json'});
  const m = STATE.meta, ver = m && m.version ? 'CAD ' + m.version : 'CAD export';
  if (m && Array.isArray(m.fit_findings)) for (const c of m.fit_findings) {
    const sv = String(c.severity || c.result || '').toLowerCase();
    list.unshift({area: ver, check: c.title || c.check || '', result: sv === 'ok' || sv === 'pass' ? 'PASS' : sv === 'open' || sv === 'owner' ? 'OPEN' : sv.toUpperCase(), detail: c.detail || '', src: 'cad/meta.json'});
  }
  if (cs && cs.unintended_overlaps != null) list.unshift({area: ver, check: 'Pairwise interference of all solids', result: cs.unintended_overlaps === 0 ? 'PASS' : 'FAIL', detail: `${cs.solids} solids, ${cs.unintended_overlaps} unintended and ${cs.intended_overlaps} intended overlaps; board ${cs.board || ''}`, src: 'cad/cad_status.json'});
  const order = r => { const t = String(r.result).toUpperCase(); return t.startsWith('FAIL') ? 0 : t.startsWith('OPEN') ? 1 : t.startsWith('NOT') ? 2 : t.startsWith('ACC') ? 3 : 4; };
  list.sort((a, b) => order(a) - order(b));
  rows('verrows', list, [o => `<td>${statusTag(o.result)}</td>`, o => `<td class="m">${esc(o.area)}</td>`, 'check', 'detail', 'src']);
  const cnt = {};
  for (const r of list) { const k = String(r.result).toUpperCase(); cnt[k] = (cnt[k] || 0) + 1; }
  $('versum').innerHTML = Object.entries(cnt).map(([k, v]) => `<span><b>${v}</b> ${esc(k)}</span>`).join('');
  $('vermeta').textContent = list.length + ' checks';
}
function renderOpen() {
  const list = [...((STATE.specs && STATE.specs.open_items) || [])];
  const m = STATE.meta;
  if (m && Array.isArray(m.open_items)) for (const o of m.open_items) list.push(typeof o === 'string' ? {area: 'CAD', item: o, detail: '', owner: '', src: 'cad/meta.json'} : {area: o.area || 'CAD', item: o.item || o.title || '', detail: o.detail || '', owner: o.owner || '', src: 'cad/meta.json'});
  rows('openrows', list, [o => `<td class="m">${esc(o.area)}</td>`, o => `<td class="tx"><b>${esc(o.item)}</b></td>`, 'detail', o => `<td>${esc(o.owner)}</td>`, 'src']);
  $('openmeta').textContent = list.length + ' items';
}

/* ------------------------------------------------------------------ BOM */
const BOMV = {sort: 'ref', dir: 1, open: new Set()};
function refKey(r) {
  const m = /^([A-Z]+)(\d+)/.exec(r || '');
  return m ? m[1].padEnd(4, ' ') + m[2].padStart(5, '0') : 'ZZZZ' + (r || '');
}
const STATUS_ORDER = ['unresolved', 'stock-zero', 'below-order', 'other-supplier', 'check', 'substituted', 'in-stock', 'excluded'];
function statusCell(r) {
  const cls = {'in-stock': 'good', substituted: 'good', 'stock-zero': 'bad', unresolved: 'bad', 'below-order': 'find', 'other-supplier': 'find', check: 'find', excluded: ''}[r.status] || '';
  return `<span class="tag ${cls}" title="${esc(r.status_why)}">${esc(r.status)}</span>`;
}
function renderBom(b) {
  const sm = b.summary || {};
  $('bomcaveats').innerHTML = (b.caveats || []).map(c => `<li>${esc(c)}</li>`).join('');
  $('bommeta').textContent = `${sm.lines} lines · ${sm.placements_listed} parts`;
  const sc = sm.status_counts || {};
  $('bomsum').innerHTML = [
    `<span><b>${sm.lines}</b> BOM lines</span>`, `<span><b>${sm.placements_listed}</b> parts listed</span>`,
    `<span>partial subtotal <b>US$${(sm.fitted_usd_partial ?? 0).toFixed(2)}</b> fitted / <b>US$${(sm.order_usd_partial ?? 0).toFixed(2)}</b> at order quantities (not a product cost)</span>`,
    ...STATUS_ORDER.filter(k => sc[k]).map(k => `<span><b>${sc[k]}</b> ${esc(k)}</span>`),
    `<span>JLC assembly BOM: <b>${sm.jlc_bom_lines}</b> lines, <b>${sm.jlc_bom_placements}</b> placements</span>`,
  ].join('');
  for (const r of b.rows) for (const ref of r.refs || []) STATE.refIndex.set(ref, r);
  const sheets = [...new Set(b.rows.flatMap(r => r.sheets || []))].sort();
  $('bsheet').innerHTML = '<option value="">All sheets</option>' + sheets.map(s => `<option>${esc(s)}</option>`).join('');
  $('bstatus').innerHTML = '<option value="">All</option>' + STATUS_ORDER.filter(k => sc[k]).map(k => `<option value="${k}">${esc(k)} (${sc[k]})</option>`).join('');
  for (const id of ['bq', 'bsheet', 'bstatus']) $(id).addEventListener('input', drawBom);
  document.querySelectorAll('#bomtable th.sort').forEach(th => th.addEventListener('click', () => {
    const k = th.dataset.k;
    BOMV.dir = BOMV.sort === k ? -BOMV.dir : 1; BOMV.sort = k; drawBom();
  }));
  $('bomrows').addEventListener('click', e => {
    const tr = e.target.closest('tr.row');
    if (!tr || e.target.closest('a')) return;
    const k = tr.dataset.i; BOMV.open.has(k) ? BOMV.open.delete(k) : BOMV.open.add(k); drawBom();
  });
  drawBom();
  const hw = b.hardware || [];
  $('hwsum').innerHTML = `<span><b>${hw.length}</b> lines from ai-files/bom/hardware-buy-list.csv; prices are snapshots in the listed currency</span>`;
  $('hwrows').innerHTML = hw.map(h => `<tr><td class="q">${esc(h.qty)}</td><td class="tx"><b>${esc(h.item)}</b><br><span class="note">${esc(h.category)}</span></td><td class="tx">${esc(h.spec)}</td><td>${h.url ? `<a href="${esc(h.url)}" rel="noopener">${esc(h.source)}</a>` : esc(h.source)}</td><td class="m">${esc(h.part_number)}</td><td class="q">${esc(h.unit_price)}</td><td class="q">${esc(h.line_price)}</td><td>${statusTag(h.price_status)}</td><td class="tx note">${esc(h.stock_date)}</td><td class="tx note">${esc(h.notes)}</td></tr>`).join('');
}
function drawBom() {
  const b = STATE.bom, q = $('bq').value.trim().toLowerCase(), sh = $('bsheet').value, st = $('bstatus').value;
  let list = b.rows.map((r, i) => ({...r, _i: String(i)}));
  if (q) list = list.filter(r => [r.ref, r.value, r.function, r.mpn, r.mfr, r.lcsc, r.availability, r.notes].join(' ').toLowerCase().includes(q));
  if (sh) list = list.filter(r => (r.sheets || []).includes(sh));
  if (st) list = list.filter(r => r.status === st);
  const k = BOMV.sort, d = BOMV.dir;
  const key = r => k === 'ref' ? refKey(r.refs && r.refs[0] || r.ref) : k === 'status' ? STATUS_ORDER.indexOf(r.status) : k === 'sheets' ? (r.sheets || []).join(',') : r[k];
  list.sort((a, c) => { const x = key(a), y = key(c); if (x == null || x === '') return 1; if (y == null || y === '') return -1; return (typeof x === 'number' && typeof y === 'number' ? x - y : String(x).localeCompare(String(y), undefined, {numeric: true})) * d; });
  document.querySelectorAll('#bomtable th.sort').forEach(th => th.setAttribute('aria-sort', th.dataset.k === k ? (d > 0 ? 'ascending' : 'descending') : 'none'));
  $('bcount').textContent = `${list.length} of ${b.rows.length} lines`;
  const n = v => v == null ? '' : Number.isInteger(v) ? v.toLocaleString('en') : v;
  $('bomrows').innerHTML = list.map(r => {
    const main = `<tr class="row" data-i="${r._i}" aria-expanded="${BOMV.open.has(r._i)}"><td class="m tx" style="max-width:190px">${esc(r.ref)}</td><td class="tx">${esc(r.value)}</td><td class="tx">${esc(r.function)}</td><td class="m">${esc(r.mpn)}</td><td>${esc(r.mfr)}</td><td class="m">${r.lcsc ? `<a href="${esc(r.url || 'https://www.lcsc.com/product-detail/' + r.lcsc + '.html')}" rel="noopener">${esc(r.lcsc)}</a>` : ''}</td><td class="q">${n(r.qty)}</td><td class="q">${n(r.stock)}</td><td class="m">${esc(r.snapshot)}</td><td>${statusCell(r)}</td><td class="note">${esc((r.sheets || []).join(', ') || '(none)')}</td></tr>`;
    const more = BOMV.open.has(r._i) ? `<tr class="more"><td colspan="11"><b>Availability:</b> ${esc(r.availability)}${r.notes ? '<br><b>Notes:</b> ' + esc(r.notes) : ''}${r.unit_usd != null ? `<br><b>Price:</b> US$${r.unit_usd} each, US$${r.fitted_usd} fitted, order qty ${n(r.order_qty)} = US$${r.order_usd}` : ''}${r.dnp && r.dnp.length ? '<br><b>DNP:</b> ' + esc(r.dnp.join(', ')) : ''}</td></tr>` : '';
    return main + more;
  }).join('') || '<tr><td colspan="11" class="note">No lines match.</td></tr>';
}

/* ------------------------------------------------------------------ documents and downloads */
function renderFiles(f) {
  for (const d of [...(f.documents || []), ...(f.downloads || [])]) if (d.href && d.source) STATE.srcMap.set(d.source, d.href);
  const specDocs = (STATE.specs && STATE.specs.documents) || [];
  const titles = new Map(specDocs.map(d => [d.path, d]));
  const docs = (f.documents || []).map(d => ({...d, title: (titles.get(d.source) || {}).title || d.desc, what: (titles.get(d.source) || {}).what || d.desc}));
  for (const sd of specDocs) if (!docs.some(d => d.source === sd.path)) docs.push({name: sd.path.split('/').pop(), href: STATE.srcMap.get(sd.path) || null, title: sd.title, what: sd.what, source: sd.path, kind: 'report', note: 'In the repository only'});
  const sch = (f.downloads || []).find(d => /schematic/i.test(d.name));
  if (sch) docs.unshift({name: sch.name, href: sch.href, title: 'Schematic preview (PDF)', what: sch.desc, bytes: sch.bytes, source: sch.source, kind: 'report'});
  STATE.docs = docs;
  let kind = '';
  const draw = () => {
    const q = $('dq').value.trim().toLowerCase();
    const list = docs.filter(d => (!kind || d.kind === kind) && (!q || [d.title, d.name, d.what, d.source].join(' ').toLowerCase().includes(q)));
    $('docrows').innerHTML = list.map(d => `<tr><td class="tx">${d.href ? `<a href="${esc(d.href)}">${esc(d.title || d.name)}</a>` : `<b>${esc(d.title || d.name)}</b>`}<br><span class="src">${esc(d.name)}${d.kind === 'datasheet' ? ' · datasheet' : ''}</span></td><td class="tx">${esc(d.what)}${d.note ? `<br><span class="note warn">${esc(d.note)}</span>` : ''}</td><td class="q">${fmtBytes(d.bytes)}</td><td class="src">${esc(d.source)}</td></tr>`).join('') || '<tr><td colspan="4" class="note">No documents match.</td></tr>';
  };
  $('dq').addEventListener('input', draw);
  document.querySelectorAll('#documents .seg button').forEach(b => b.addEventListener('click', () => {
    kind = b.dataset.kind; document.querySelectorAll('#documents .seg button').forEach(x => x.setAttribute('aria-pressed', x === b)); draw();
  }));
  draw();
  $('docmeta').textContent = docs.length + ' documents';
  const na = f.not_available || [];
  $('docnote').innerHTML = (na.length ? 'Not available: ' + na.map(x => esc(x.name)).join('; ') + '. ' : '') + 'Markdown reports open as plain text. Datasheets are the manufacturers\' documents, copied when 5 MB or smaller; checksums in <a href="docs/SHA256SUMS">docs/SHA256SUMS</a>.';
  $('bomfiles').innerHTML = (f.downloads || []).filter(d => /\.csv$/i.test(d.name)).map(d => `<li><a href="${esc(d.href)}" download>${esc(d.name)}</a> · ${esc(d.desc)} · ${fmtBytes(d.bytes)}</li>`).join('');
  drawDownloads();
  const gal = f.renders || [];
  $('gal').insertAdjacentHTML('beforeend', gal.map(r => `<figure><a href="${esc(r.href)}"><img src="${esc(r.href)}" alt="${esc(r.caption)}" loading="lazy"></a><figcaption>${esc(r.caption)}</figcaption></figure>`).join(''));
}
function drawDownloads() {
  const f = STATE.files || {downloads: []};
  const list = [...(STATE.cadDownloads || []), ...(f.downloads || [])];
  $('dlrows').innerHTML = list.map(d => `<tr><td class="tx"><a href="${esc(d.href)}" download>${esc(d.name)}</a></td><td class="tx">${esc(d.desc)}</td><td class="q">${fmtBytes(d.bytes)}</td><td class="src" title="${esc(d.sha256)}">${d.sha256 ? esc(d.sha256.slice(0, 16)) + '…' : ''}</td></tr>`).join('');
  $('dlmeta').textContent = list.length + ' files';
}
async function loadCadDownloads() {
  let list = [];
  const src = (STATE.cadStatus && STATE.cadStatus.downloads) || (STATE.meta && STATE.meta.downloads);
  const fix = h => /^(https?:|\/)/.test(h) ? null : h.startsWith('cad/') ? h : h.startsWith('downloads/') ? 'cad/' + h : 'cad/downloads/' + h;
  if (Array.isArray(src)) {
    list = src.map(d => typeof d === 'string' ? {name: d.split('/').pop(), href: fix(d)} : {name: d.name || (d.file || d.href || d.path || '').split('/').pop(), href: fix(d.href || d.file || d.path || d.name || ''), bytes: d.bytes ?? d.size, sha256: d.sha256, desc: d.desc || d.description || ''});
  } else {
    try {
      const r = await fetch('cad/downloads/SHA256SUMS', {cache: 'no-cache'});
      if (r.ok) list = (await r.text()).split('\n').map(l => l.trim().split(/\s+\*?/)).filter(p => p.length >= 2 && /^[0-9a-f]{64}$/.test(p[0])).map(([h, n]) => ({name: n, href: 'cad/downloads/' + n, sha256: h}));
      if (r.ok) $('cadsums').innerHTML = ' and <a href="cad/downloads/SHA256SUMS">cad/downloads/SHA256SUMS</a>';
    } catch (e) {}
  }
  list = list.filter(d => d.href);
  for (const d of list) {
    if (!d.desc) d.desc = 'CAD export' + (STATE.meta && STATE.meta.version ? ' ' + STATE.meta.version : '') + ' (newest)';
    if (d.bytes == null) try { const h = await fetch(d.href, {method: 'HEAD'}); if (h.ok) d.bytes = +h.headers.get('content-length') || null; } catch (e) {}
  }
  STATE.cadDownloads = list;
  drawDownloads();
}

/* ------------------------------------------------------------------ boot: page data */
(async () => {
  const [specs, bom, files] = await Promise.allSettled([getJSON('data/specs.json'), getJSON('data/bom.json'), getJSON('data/files.json')]);
  if (files.status === 'fulfilled') STATE.files = files.value;
  if (specs.status === 'fulfilled') STATE.specs = specs.value;
  if (bom.status === 'fulfilled') STATE.bom = bom.value;
  if (STATE.files) for (const d of [...(STATE.files.documents || []), ...(STATE.files.downloads || [])]) if (d.href && d.source) STATE.srcMap.set(d.source, d.href);
  if (STATE.specs) renderSpecs(STATE.specs); else console.error('specs.json', specs.reason);
  if (STATE.bom) renderBom(STATE.bom); else { console.error('bom.json', bom.reason); $('bomrows').innerHTML = '<tr><td colspan="11" class="warn">data/bom.json could not be loaded.</td></tr>'; }
  if (STATE.files) renderFiles(STATE.files); else console.error('files.json', files.reason);
  fillCadSpec();
})();

/* ================================================================== 3D viewer */
const V = {
  ok: false, parts: [], groups: new Map(), world: null, box: null, metaBox: null, up: 'Y',
  hoverObj: null, hoverGroup: null, planes: [], explode: 0,
};
const stage = $('stage'), canvas = $('cv');
let renderer, scene, camera, controls;
try {
  renderer = new THREE.WebGLRenderer({canvas, antialias: true, alpha: false});
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.outputEncoding = THREE.sRGBEncoding;
  renderer.localClippingEnabled = false;
  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(32, 1, 1, 20000);
  scene.add(new THREE.HemisphereLight(0xffffff, 0x445566, 0.75));
  const d1 = new THREE.DirectionalLight(0xffffff, 0.75); d1.position.set(1, 2, 1.5); camera.add(d1);
  const d2 = new THREE.DirectionalLight(0xffffff, 0.35); d2.position.set(-1.5, -0.5, -1); scene.add(d2);
  scene.add(camera);
  controls = new THREE.OrbitControls(camera, canvas);
  controls.enableDamping = false;
  controls.screenSpacePanning = true;
  controls.listenToKeyEvents(stage);
  controls.addEventListener('change', () => { schedule(); });
  controls.addEventListener('start', () => { cancelAnimationFrame(V.anim); hideTip(); });
  V.world = new THREE.Group(); V.world.name = 'world'; scene.add(V.world);
} catch (e) {
  console.error('WebGL unavailable', e);
  showNoCad('This browser could not start WebGL, so the 3D view is not available. The renders below show the model.');
}
function cssVar(n) { return getComputedStyle(document.documentElement).getPropertyValue(n).trim(); }
function applyTheme() { if (renderer) { renderer.setClearColor(new THREE.Color(cssVar('--panel') || '#f8fafb')); schedule(); } }
let pend = 0;
function schedule() { if (!pend && renderer) pend = requestAnimationFrame(() => { pend = 0; draw(); }); }
function draw() { renderer.render(scene, camera); syncCube(); }
function resize() {
  if (!renderer) return;
  const w = stage.clientWidth, h = stage.clientHeight;
  renderer.setSize(w, h, false); camera.aspect = w / Math.max(1, h); camera.updateProjectionMatrix(); schedule();
}
if (renderer) {
  new ResizeObserver(resize).observe(stage);
  new MutationObserver(applyTheme).observe(document.documentElement, {attributes: true, attributeFilter: ['data-theme']});
  matchMedia('(prefers-color-scheme: dark)').addEventListener('change', applyTheme);
  applyTheme(); resize();
}
function showNoCad(why) {
  $('nocad').hidden = false; $('loading').hidden = true;
  if (why) $('nocadwhy').textContent = why;
  for (const id of ['explode', 'clx', 'cly', 'clz', 'reset', 'shot', 't-wire', 't-xray', 'clflip']) $(id).disabled = true;
  document.querySelectorAll('[data-quick]').forEach(c => { c.disabled = true; });
}

/* ------------------------------------------------------------------ meta normalisation */
const AXIS = {X: new THREE.Vector3(1, 0, 0), Y: new THREE.Vector3(0, 1, 0), Z: new THREE.Vector3(0, 0, 1)};
function upOf(s, dflt) { const t = String(s || dflt || 'Y').toUpperCase().replace(/[^XYZ]/g, ''); return 'XYZ'.includes(t) && t ? t[0] : 'Y'; }
function colorOf(c) {
  if (c == null) return null;
  if (typeof c === 'string') { try { return new THREE.Color(c); } catch (e) { return null; } }
  if (Array.isArray(c) && c.length >= 3) { const k = c.some(v => v > 1) ? 255 : 1; return new THREE.Color(c[0] / k, c[1] / k, c[2] / k); }
  if (typeof c === 'number') return new THREE.Color(c);
  return null;
}
function vecOf(v) {
  if (!v) return null;
  if (Array.isArray(v) && v.length >= 3) return new THREE.Vector3(+v[0] || 0, +v[1] || 0, +v[2] || 0);
  if (typeof v === 'object' && ('x' in v || 'y' in v || 'z' in v)) return new THREE.Vector3(+v.x || 0, +v.y || 0, +v.z || 0);
  return null;
}
function normGroups(meta) {
  let g = meta.groups || [];
  if (!Array.isArray(g) && typeof g === 'object') g = Object.entries(g).map(([id, o]) => ({id, ...(typeof o === 'object' ? o : {label: o})}));
  g = [...g];
  if (meta.pcb_group && typeof meta.pcb_group === 'object') g.push({...meta.pcb_group, isPcbGroup: true});   // v12: the PCB group is kept apart
  const colors = meta.colors || meta.colours || {};
  const explode = meta.explode || meta.explode_mm || meta.explode_vectors || {};
  const pretty = s => String(s).replace(/_/g, ' ').replace(/([a-z])([A-Z])/g, '$1 $2').replace(/\bStand Ins\b/, 'stand-ins').trim();
  return g.map(o => {
    if (typeof o === 'string') o = {id: o};
    const id = String(o.id ?? o.key ?? o.name ?? o.group);
    return {
      id, label: o.label || o.title || pretty(o.name || id), isPcbGroup: !!o.isPcbGroup,
      color: colorOf(o.color ?? o.colour ?? colors[id]),
      explode: vecOf(o.explode ?? o.explode_mm ?? o.explode_vector ?? explode[id]),
      visible: o.visible !== false && o.default_visible !== false && o.hidden !== true,
      opacity: o.opacity, nodes: o.nodes || o.members || [], file: o.file, description: o.description || o.desc || '',
      components_without_model: o.components_without_model || [],
    };
  });
}
function normNodes(meta) {
  const out = new Map();
  let n = meta.nodes || {};
  if (Array.isArray(n)) for (const o of n) { if (o && (o.name || o.node)) out.set(o.name || o.node, o); }
  else for (const [k, o] of Object.entries(n)) out.set(k, typeof o === 'string' ? {group: o} : o);
  for (const [k, o] of [...out]) { const sk = sanitizeName(k); if (!out.has(sk)) out.set(sk, o); }   // GLTFLoader renames nodes
  return out;
}
function normFiles(meta) {
  let f = meta.files || meta.glb || null;
  const units = meta.files_units || meta.glb_units || {}, ups = meta.files_up_axis || meta.glb_up_axis || {};
  let list;
  if (Array.isArray(f)) list = f.map((o, i) => typeof o === 'string' ? {key: /pcb/i.test(o) ? 'pcb' : 'file' + i, file: o} : {key: o.key || o.id || o.name || 'file' + i, file: o.file || o.path || o.href || o.url, ...o});
  else if (f && typeof f === 'object') list = Object.entries(f).map(([key, o]) => typeof o === 'string' ? {key, file: o} : {key, ...o, file: o.file || o.path || o.href || o.url});
  else list = [{key: 'enclosure', file: 'enclosure.glb'}, {key: 'pcb', file: 'pcb.glb'}];
  return list.filter(o => o.file && typeof o.file === 'string' && /\.(glb|gltf)$/i.test(o.file)).map(o => ({
    ...o, url: /^(https?:|\/|cad\/)/.test(o.file) ? o.file : 'cad/' + o.file.replace(/^\.\//, ''),
    optional: o.optional === true || o.load === false,
    units: o.units || (typeof units === 'string' ? units : units[o.key]) || null,
    up: o.up_axis || o.up || (typeof ups === 'string' ? ups : ups[o.key]) || null,
    isPcb: /pcb|board/i.test(o.key) || /pcb|board/i.test(o.file),
  }));
}

/* ------------------------------------------------------------------ loading */
function loadGLB(url, onProgress) {
  return new Promise((res, rej) => new THREE.GLTFLoader().load(url, res, onProgress, rej));
}
async function headOk(url) { try { const r = await fetch(url, {method: 'HEAD', cache: 'no-cache'}); return r.ok; } catch (e) { return false; } }
async function bootCad() {
  if (!renderer) return;
  let meta = null, metaErr = null;
  try { meta = await getJSON('cad/meta.json'); } catch (e) { metaErr = e; }
  try { STATE.cadStatus = await getJSON('cad/cad_status.json'); } catch (e) {}
  STATE.meta = meta;
  if (STATE.specs) { renderVerification(); renderOpen(); }
  loadCadDownloads();
  addCadRenders(meta);
  const allFiles = normFiles(meta || {});
  const files = allFiles.filter(f => !f.optional);
  V.optional = allFiles.filter(f => f.optional);
  V.nodes = normNodes(meta || {});
  const present = [];
  for (const f of files) if (await headOk(f.url)) present.push(f);
  if (!present.length) {
    const st = STATE.cadStatus;
    showNoCad((st && st.message ? 'CAD export status: ' + st.message + '. ' : '') + (metaErr ? 'cad/meta.json is missing; ' : '') + 'no model file (' + files.map(f => f.url).join(', ') + ') is published yet.');
    fillCadSpec();
    return;
  }
  V.up = upOf(meta && (meta.up_axis || meta.up), 'Y');
  if (V.up === 'Z') V.world.rotation.x = -Math.PI / 2;      // model frame Z up -> three.js Y up
  else if (V.up === 'X') V.world.rotation.z = Math.PI / 2;
  V.world.updateMatrixWorld(true);
  buildCube();
  const groups = normGroups(meta || {}), nodes = normNodes(meta || {});
  for (const g of groups) addGroup(g);
  const loadEl = $('loading'), bar = $('loadbar'), txt = $('loadtxt');
  loadEl.hidden = false;
  const prog = {};
  const upd = () => { const t = Object.values(prog).reduce((a, p) => [a[0] + p[0], a[1] + p[1]], [0, 0]); bar.style.width = (t[1] ? 100 * t[0] / t[1] : 10) + '%'; txt.textContent = 'Loading CAD ' + fmtBytes(t[0]) + (t[1] ? ' of ' + fmtBytes(t[1]) : ''); };
  const missing = files.filter(f => !present.includes(f)).map(f => f.url);
  const results = await Promise.allSettled(present.map(f => loadGLB(f.url, e => { prog[f.key] = [e.loaded, e.total || 0]; upd(); }).then(g => ({f, g}))));
  for (const r of results) {
    if (r.status === 'fulfilled') addFile(r.value.f, r.value.g, meta || {}, nodes);
    else { console.error('GLB load failed', r.reason); missing.push(String(r.reason && r.reason.message || r.reason)); }
  }
  loadEl.hidden = true;
  if (!V.parts.length) { showNoCad('The model files could not be read: ' + missing.join(', ')); return; }
  // drop empty groups, build chips, colours, explode defaults
  for (const [id, g] of [...V.groups]) if (!g.parts.length) { V.world.remove(g.obj); V.groups.delete(id); }
  autoExplode();
  computeBox();
  buildChips();
  syncQuick();
  V.ok = true;
  if (missing.length) $('hint').textContent = 'Not loaded: ' + missing.join(', ') + ' · ' + $('hint').textContent;
  fillCadSpec(); fillCadNotes(meta); buildOptional(); buildSectionPresets(meta);
  goView('iso', true);
}
function addCadRenders(m) {
  const r = m && ((m.files && Array.isArray(m.files.renders) && m.files.renders) || m.renders);
  if (!Array.isArray(r) || !r.length) return;
  const name = h => String(h).split('/').pop().replace(/\.png$/i, '').replace(/[_-]+/g, ' ');
  const figs = r.map(x => typeof x === 'string' ? {href: x, caption: name(x)} : {href: x.href || x.file || x.path, caption: x.caption || x.title || name(x.href || x.file || x.path)})
    .map(x => ({href: /^(cad\/|https?:)/.test(x.href) ? x.href : 'cad/' + x.href, caption: 'CAD ' + (m.version || 'export') + ': ' + x.caption}));
  $('gal').insertAdjacentHTML('afterbegin', figs.map(f => `<figure><a href="${esc(f.href)}"><img src="${esc(f.href)}" alt="${esc(f.caption)}" loading="lazy"></a><figcaption>${esc(f.caption)}</figcaption></figure>`).join(''));
  $('rendersh').textContent = 'CAD renders (' + (m.version || 'newest') + ' first, then v11 of 2026-10-12)';
}
function buildOptional() {
  // optional layers (for example the copper of a partly routed board) load on demand
  const host = $('optfiles'); host.innerHTML = '';
  for (const f of V.optional || []) {
    const id = 'opt-' + f.key.replace(/\W/g, '');
    const lab = document.createElement('label'); lab.htmlFor = id;
    lab.title = f.content || f.description || f.url;
    lab.innerHTML = `<input type="checkbox" id="${id}"> ${esc(f.label || f.key.replace(/_/g, ' '))}${f.bytes ? ' (' + fmtBytes(f.bytes) + ')' : ''}`;
    host.appendChild(lab);
    const cb = lab.querySelector('input');
    cb.addEventListener('change', async () => {
      if (f.loaded) { for (const p of f.parts) p.visible = cb.checked; schedule(); return; }
      cb.disabled = true; $('loading').hidden = false; $('loadtxt').textContent = 'Loading ' + f.url;
      try {
        const g = await loadGLB(f.url, e => { $('loadbar').style.width = (e.total ? 100 * e.loaded / e.total : 30) + '%'; });
        const before = V.parts.length;
        addFile(f, g, STATE.meta || {}, V.nodes);
        f.parts = V.parts.slice(before); f.loaded = true;
        if ($('t-wire').checked) for (const p of f.parts) p.traverse(o => { if (o.isMesh) for (const m of [].concat(o.material)) m.wireframe = true; });
        applyExplode(); applySections();
      } catch (e) { console.error(e); cb.checked = false; $('hint').textContent = 'Could not load ' + f.url; }
      $('loading').hidden = true; cb.disabled = false; schedule();
    });
  }
}
function buildSectionPresets(meta) {
  const sel = $('clpreset'), list = (meta && (meta.section_planes || meta.sections)) || [];
  if (!list.length) return;
  sel.innerHTML = '<option value="">none</option>' + list.map((p, i) => `<option value="${i}">${esc(p.name || p.label || 'plane ' + (i + 1))}</option>`).join('');
  sel.parentElement.hidden = false;
  V.presets = list;
  sel.addEventListener('change', applySections);
}
function addGroup(g) {
  if (V.groups.has(g.id)) return V.groups.get(g.id);
  const obj = new THREE.Group(); obj.name = 'group:' + g.id;
  obj.visible = g.visible !== false;
  V.world.add(obj);
  const G = {...g, obj, parts: []};
  V.groups.set(g.id, G);
  return G;
}
const QUICK = {
  pcb: /pcb|board/i,
  lid: /lid/i,
  battery: /batt|cell|pack|pcm/i,
  drivers: /driver|\bwoofer\b|speaker|tweeter/i,
  enclosure: /shell|enclos|insert|baffle|case|housing|body|foot|feet|chamber|grille|knob|wall/i,
};
function guessGroup(name, groups) {
  const n = String(name || '').toLowerCase();
  let best = null;
  for (const g of groups.values()) {
    const keys = [g.id, g.label].map(s => String(s).toLowerCase()).filter(Boolean);
    for (const k of keys) {
      const k1 = k.replace(/s$/, '');
      if (k1.length > 2 && n.includes(k1) && (!best || k1.length > best[1])) best = [g.id, k1.length];
    }
  }
  if (best) return best[0];
  for (const [q, re] of Object.entries(QUICK)) if (re.test(n)) return q;
  return 'other';
}
function sanitizeName(n) { return THREE.PropertyBinding ? THREE.PropertyBinding.sanitizeNodeName(String(n)) : String(n).replace(/\s/g, '_').replace(/[\[\]\.:\/]/g, ''); }
function isAncestor(a, o) { for (let p = o.parent; p; p = p.parent) if (p === a) return true; return false; }
function nodeMeta(nodes, name) { return nodes.get(name) || nodes.get(String(name).replace(/_\d+$/, '')) || null; }
function addFile(f, gltf, meta, nodes) {
  const root = gltf.scene;
  // units: explicit per-file units, else guess from size (glTF is metres by spec; < 3 units across means metres)
  const raw = new THREE.Box3().setFromObject(root), size = raw.getSize(new THREE.Vector3());
  const u = String(f.units || '').toLowerCase().trim().split(/[\s(,;]/)[0];   // "mm (root node carries scale 1000)" -> mm
  const scale = u === 'm' || u === 'metre' || u === 'meter' || u === 'meters' ? 1000 : u === 'cm' ? 10 : u === 'in' || u === 'inch' ? 25.4 : u === 'mm' ? 1 : (Math.max(size.x, size.y, size.z) < 3 ? 1000 : 1);
  const fileUp = upOf(f.up, 'Y');
  const holder = new THREE.Group(), axis = new THREE.Group();
  holder.name = 'file:' + f.key; axis.add(root); holder.add(axis); root.scale.multiplyScalar(scale);
  if (fileUp !== V.up) {                                   // rotate the file's up axis onto the model frame's up axis
    const q = new THREE.Quaternion().setFromUnitVectors(AXIS[fileUp], AXIS[V.up]); axis.quaternion.copy(q);
  }
  const tr = f.transform || (f.isPcb ? (meta.pcb_transform || meta.pcb || null) : (meta.transforms && meta.transforms[f.key]));
  const baked = tr && (tr.applied === true || tr.baked === true || /already applied|baked/i.test(String(tr.note || '')));
  if (tr && typeof tr === 'object' && !baked) {
    if (Array.isArray(tr.matrix) && tr.matrix.length === 16) { holder.matrixAutoUpdate = false; holder.matrix.fromArray(tr.matrix); }
    else {
      const p = vecOf(tr.position_mm || tr.translate_mm || tr.translation_mm || tr.position || tr.translate || tr.translation);
      const r = vecOf(tr.rotation_deg || tr.rotate_deg || tr.rotation || tr.rotate);
      if (p) holder.position.copy(p);
      if (r) holder.rotation.set(r.x * Math.PI / 180, r.y * Math.PI / 180, r.z * Math.PI / 180, (tr.order || 'XYZ').toUpperCase());
    }
  }
  V.world.add(holder); V.world.updateMatrixWorld(true);
  // materials per mesh, so highlight and x-ray do not leak between parts
  root.traverse(o => {
    if (!o.isMesh) return;
    o.material = Array.isArray(o.material) ? o.material.map(m => m.clone()) : o.material.clone();
    for (const m of [].concat(o.material)) { m.userData.base = {color: m.color && m.color.clone(), emissive: m.emissive && m.emissive.clone(), opacity: m.opacity, transparent: m.transparent}; m.side = THREE.DoubleSide; }
  });
  // part list: the nodes named in meta.nodes; else the file root for the PCB (one part), else the children of
  // the first non-trivial node
  let top = root;
  while (top.children.length === 1 && !top.isMesh && !(nodeMeta(nodes, top.name))) top = top.children[0];
  const pcbG = [...V.groups.values()].find(g => g.isPcbGroup);
  const fileGroup = f.group || (f.isPcb ? (pcbG ? pcbG.id : 'pcb') : null);
  let items = [];
  if (!f.isPcb && nodes.size) {
    root.traverse(o => { if (o !== root && nodeMeta(nodes, o.name) && !items.some(p => isAncestor(p, o))) items.push(o); });
    let all = 0, covered = 0;                               // use the named nodes only when they hold (nearly) every mesh
    root.traverse(o => { if (o.isMesh) { all++; if (items.some(p => p === o || isAncestor(p, o))) covered++; } });
    if (covered < 0.9 * all) items = [];
  }
  if (!items.length) items = f.isPcb && !f.split ? [top] : (top.children.length ? [...top.children] : [top]);
  for (const o of items) {
    const nm = nodeMeta(nodes, o.name) || {};
    let gid = nm.group || (o.userData && (o.userData.group || o.userData.Group)) || null;
    if (!gid) for (const g of V.groups.values()) if ((g.nodes || []).includes(o.name)) { gid = g.id; break; }
    if (!gid) gid = fileGroup || guessGroup(o.name, V.groups);
    gid = String(gid);
    const G = V.groups.get(gid) || addGroup({id: gid, label: gid === 'other' ? 'Other' : gid.replace(/[_-]+/g, ' '), visible: true});
    G.obj.attach(o);                                       // keeps the world pose, moves the part into the model frame
    const ud = o.userData || {};
    o.userData.part = {name: o.name, label: nm.label || '', group: gid, base: o.position.clone(), isPcb: f.isPcb, file: f.key,
      explode: vecOf(nm.explode || nm.explode_mm || ud.explode_mm || ud.explode),
      source: nm.model_source || ud.model_source || '', accuracy: nm.accuracy || ud.accuracy || ''};
    if (o.userData.part.explode) G.nodeExplode = true;
    G.parts.push(o); V.parts.push(o);
    const col = colorOf(nm.color || nm.colour) || (!f.isPcb && G.color);
    if (col) o.traverse(m => { if (m.isMesh) for (const mm of [].concat(m.material)) { mm.color && mm.color.copy(col); mm.userData.base.color = col.clone(); } });
  }
  V.world.remove(holder);
}
function computeBox() {
  V.world.updateMatrixWorld(true);
  V.box = new THREE.Box3();
  for (const g of V.groups.values()) if (g.obj.visible) V.box.expandByObject(g.obj);
  if (V.box.isEmpty()) for (const g of V.groups.values()) V.box.expandByObject(g.obj);
  if (!V.metaBox) {
    const inv = new THREE.Matrix4().copy(V.world.matrixWorld).invert();
    const all = new THREE.Box3(); for (const g of V.groups.values()) all.expandByObject(g.obj);
    V.metaBox = all.clone().applyMatrix4(inv);
  }
}
function autoExplode() {
  // groups without an explode vector move away from the model centre, scaled by the model size
  const all = new THREE.Box3(); for (const g of V.groups.values()) all.expandByObject(g.obj);
  const inv = new THREE.Matrix4().copy(V.world.matrixWorld).invert();
  const mb = all.clone().applyMatrix4(inv), c = mb.getCenter(new THREE.Vector3()), s = mb.getSize(new THREE.Vector3()).length();
  for (const g of V.groups.values()) {
    if (g.explode || g.nodeExplode) continue;
    const b = new THREE.Box3(); b.expandByObject(g.obj); b.applyMatrix4(inv);
    const d = b.getCenter(new THREE.Vector3()).sub(c);
    g.explode = d.lengthSq() < 1e-6 ? new THREE.Vector3() : d.normalize().multiplyScalar(0.45 * s);
    g.autoExplode = true;
  }
}

/* ------------------------------------------------------------------ groups UI */
function hex(c) { return c ? '#' + c.getHexString() : 'transparent'; }
function groupColour(g) {
  if (g.color) return g.color;
  for (const p of g.parts) { let c = null; p.traverse(m => { if (!c && m.isMesh) { const mm = [].concat(m.material)[0]; if (mm && mm.color) c = mm.color; } }); if (c) return c; }
  return null;
}
function buildChips() {
  const el = $('groups');
  el.innerHTML = '';
  for (const g of V.groups.values()) {
    const b = document.createElement('button');
    b.type = 'button'; b.className = 'chip'; b.dataset.g = g.id;
    b.setAttribute('aria-pressed', g.obj.visible);
    b.title = (g.description || g.label) + ' · ' + g.parts.length + ' part' + (g.parts.length === 1 ? '' : 's');
    b.innerHTML = `<i style="background:${hex(groupColour(g))}"></i>${esc(g.label)}`;
    b.addEventListener('click', () => setGroup(g.id, !g.obj.visible));
    el.appendChild(b);
  }
}
function setGroup(id, on) {
  const g = V.groups.get(id); if (!g) return;
  g.obj.visible = on;
  const b = document.querySelector(`#groups .chip[data-g="${CSS.escape(id)}"]`); if (b) b.setAttribute('aria-pressed', on);
  syncQuick(); schedule();
}
function quickGroups(q) {
  const re = QUICK[q];
  return [...V.groups.values()].filter(g => {
    const s = g.id + ' ' + g.label;
    if (q === 'enclosure') return re.test(s) && !QUICK.lid.test(s) && !QUICK.pcb.test(s) && !QUICK.drivers.test(s) && !QUICK.battery.test(s);
    return re.test(s);
  });
}
function syncQuick() {
  document.querySelectorAll('[data-quick]').forEach(cb => {
    const gs = quickGroups(cb.dataset.quick);
    cb.disabled = !gs.length;
    cb.parentElement.title = gs.length ? 'Groups: ' + gs.map(g => g.label).join(', ') : 'Not in this CAD export';
    cb.checked = gs.length > 0 && gs.every(g => g.obj.visible);
    cb.indeterminate = gs.some(g => g.obj.visible) && !cb.checked;
  });
}
document.querySelectorAll('[data-quick]').forEach(cb => cb.addEventListener('change', () => { for (const g of quickGroups(cb.dataset.quick)) setGroup(g.id, cb.checked); }));
$('gall').onclick = () => { for (const g of V.groups.keys()) setGroup(g, true); };
$('gnone').onclick = () => { for (const g of V.groups.keys()) setGroup(g, false); };
$('gonly').onclick = () => { if (!V.hoverGroup) return; for (const g of V.groups.keys()) setGroup(g, g === V.hoverGroup); };

/* ------------------------------------------------------------------ explode, sections, wireframe, x-ray */
function applyExplode() {
  const f = V.explode;
  // a part's own explode vector (meta.nodes / node extras) replaces its group's vector, so nothing moves twice
  for (const g of V.groups.values()) {
    const gv = g.explode || new THREE.Vector3();
    g.obj.position.copy(gv).multiplyScalar(f);
    for (const p of g.parts) { const u = p.userData.part; p.position.copy(u.base); if (u.explode) p.position.addScaledVector(u.explode.clone().sub(gv), f); }
  }
  schedule();
}
$('explode').addEventListener('input', e => { V.explode = e.target.value / 100; $('explodev').textContent = e.target.value + ' %'; applyExplode(); });
$('explode').addEventListener('change', () => { if (V.ok) goDir(camera.position.clone().sub(controls.target)); });   // refit, same direction
function applySections() {
  if (!V.metaBox) return;
  const flip = $('clflip').checked, planes = [];
  [['clx', 'x'], ['cly', 'y'], ['clz', 'z']].forEach(([id, ax]) => {
    const v = +$(id).value, lo = V.metaBox.min[ax], hi = V.metaBox.max[ax];
    if (v >= 1000) { $(id + 'v').textContent = 'off'; return; }
    const c = lo + (hi - lo) * v / 1000;
    $(id + 'v').textContent = c.toFixed(1) + ' mm';
    const n = new THREE.Vector3(ax === 'x' ? 1 : 0, ax === 'y' ? 1 : 0, ax === 'z' ? 1 : 0);
    const p = flip ? new THREE.Plane(n.clone(), -c) : new THREE.Plane(n.clone().negate(), c);
    p.applyMatrix4(V.world.matrixWorld);
    planes.push(p);
  });
  const pre = $('clpreset').value;
  if (pre !== '' && V.presets && V.presets[+pre]) {               // preset planes are given in the model frame: keeps n.p + constant >= 0
    const P = V.presets[+pre], n = vecOf(P.normal);
    if (n) { const p = new THREE.Plane(n.normalize(), +P.constant || 0); p.applyMatrix4(V.world.matrixWorld); planes.push(p); }
  }
  renderer.clippingPlanes = planes;
  schedule();
}
for (const id of ['clx', 'cly', 'clz', 'clflip']) $(id).addEventListener('input', applySections);
function eachMat(fn, filter) { for (const p of V.parts) if (!filter || filter(p)) p.traverse(o => { if (o.isMesh) for (const m of [].concat(o.material)) fn(m, o, p); }); }
$('t-wire').addEventListener('change', e => { eachMat(m => { m.wireframe = e.target.checked; }); schedule(); });
$('t-xray').addEventListener('change', e => {
  const on = e.target.checked;
  const enc = new Set([...quickGroups('enclosure'), ...quickGroups('lid')].map(g => g.id));
  eachMat(m => { const b = m.userData.base; m.transparent = on || b.transparent; m.opacity = on ? 0.22 : b.opacity; m.depthWrite = !on; m.needsUpdate = true; }, p => enc.has(p.userData.part.group));
  schedule();
});

/* ------------------------------------------------------------------ camera views and the cube */
function metaDir(name) {
  const m = STATE.meta || {}, views = m.views || {};
  if (views[name]) return vecOf(views[name]).normalize();
  const Z = V.up === 'Z';
  const front = vecOf(m.front || m.front_dir) || (Z ? new THREE.Vector3(0, -1, 0) : new THREE.Vector3(0, 0, 1));
  const up = Z ? new THREE.Vector3(0, 0, 1) : new THREE.Vector3(0, 1, 0);
  const right = new THREE.Vector3().crossVectors(front, up).negate().normalize();   // looking at the front, +right is to the viewer's right
  const d = {front, back: front.clone().negate(), top: up.clone(), bottom: up.clone().negate(), right, left: right.clone().negate(),
    iso: front.clone().multiplyScalar(1).add(right.clone().multiplyScalar(0.8)).add(up.clone().multiplyScalar(0.7))}[name] || front;
  return d.clone().normalize();
}
function toWorldDir(v) { return v.clone().transformDirection(V.world.matrixWorld); }
function goDir(dirWorld, instant) {
  hideTip();
  computeBox();
  const box = V.box.isEmpty() ? new THREE.Box3(new THREE.Vector3(-50, -50, -50), new THREE.Vector3(50, 50, 50)) : V.box;
  const c = box.getCenter(new THREE.Vector3()), r = box.getBoundingSphere(new THREE.Sphere()).radius;
  const fov = camera.fov * Math.PI / 180, fit = r / Math.sin(Math.min(fov, fov * camera.aspect) / 2) * 1.02;
  const d = dirWorld.clone().normalize();
  if (Math.abs(d.y) > 0.999) d.add(new THREE.Vector3(0, 0, 0.002)).normalize();       // avoid the orbit pole
  const end = c.clone().addScaledVector(d, fit);
  camera.near = Math.max(0.5, fit / 200); camera.far = fit * 20; camera.updateProjectionMatrix();
  controls.maxDistance = fit * 8; controls.minDistance = r * 0.05;
  cancelAnimationFrame(V.anim);
  if (instant) { camera.position.copy(end); controls.target.copy(c); controls.update(); schedule(); return; }
  const p0 = camera.position.clone(), t0 = controls.target.clone(), st = performance.now(), T = 380;
  // interpolate on the sphere around the target so the camera swings round rather than through the model
  const r0 = p0.clone().sub(t0), r1 = end.clone().sub(c), l0 = r0.length(), l1 = r1.length();
  const q = new THREE.Quaternion().setFromUnitVectors(r0.clone().normalize(), r1.clone().normalize());
  const step = now => {
    const u = Math.min(1, (now - st) / T), z = u < .5 ? 2 * u * u : 1 - Math.pow(-2 * u + 2, 2) / 2;
    const qq = new THREE.Quaternion().slerp(q, z);
    const tgt = t0.clone().lerp(c, z);
    camera.position.copy(tgt).add(r0.clone().normalize().applyQuaternion(qq).multiplyScalar(l0 + (l1 - l0) * z));
    controls.target.copy(tgt); controls.update();
    if (u < 1) V.anim = requestAnimationFrame(step);
  };
  V.anim = requestAnimationFrame(step);
}
function goView(name, instant) {
  document.querySelectorAll('[data-view]').forEach(b => b.setAttribute('aria-pressed', b.dataset.view === name));
  goDir(toWorldDir(metaDir(name)), instant);
}
document.querySelectorAll('[data-view]').forEach(b => b.addEventListener('click', () => goView(b.dataset.view)));
$('home').onclick = () => goView('iso');
$('reset').onclick = () => {
  $('explode').value = 0; $('explode').dispatchEvent(new Event('input'));
  for (const id of ['clx', 'cly', 'clz']) $(id).value = 1000;
  $('clflip').checked = false; $('clpreset').value = ''; applySections();
  if ($('t-wire').checked) { $('t-wire').checked = false; $('t-wire').dispatchEvent(new Event('change')); }
  if ($('t-xray').checked) { $('t-xray').checked = false; $('t-xray').dispatchEvent(new Event('change')); }
  for (const g of V.groups.values()) setGroup(g.id, g.visible !== false);
  goView('iso');
};
stage.addEventListener('keydown', e => { if (e.key === 'Home') { e.preventDefault(); goView('iso'); } });

const W2C = v => [v.x, -v.y, v.z];                     // three.js (y up) to CSS (y down)
function buildCube() {
  const cube = $('cube'); cube.innerHTML = '';
  if (!V.world) return;
  const names = ['front', 'back', 'right', 'left', 'top', 'bottom'];
  const upW = new THREE.Vector3(0, 1, 0);
  for (const n of names) {
    const N = toWorldDir(metaDir(n)).round();
    let U = Math.abs(N.y) > 0.9 ? toWorldDir(metaDir('front')).round().multiplyScalar(N.y > 0 ? -1 : 1) : upW.clone();
    const R = new THREE.Vector3().crossVectors(U, N).normalize();
    const X = W2C(R), Y = W2C(U.clone().negate()), Z = W2C(N), d = 23;
    const el = document.createElement('div');
    el.textContent = n === 'right' ? 'side' : n;
    el.title = 'View from the ' + n;
    el.style.transform = `matrix3d(${[...X, 0, ...Y, 0, ...Z, 0, Z[0] * d, Z[1] * d, Z[2] * d, 1].map(v => +v.toFixed(5)).join(',')})`;
    el.addEventListener('click', () => { if (V.ok) goView(n); });
    cube.appendChild(el);
  }
}
const SG = [1, -1, 1];
function syncCube() {
  const R = new THREE.Matrix4().makeRotationFromQuaternion(camera.quaternion).invert().elements, m = [];
  for (let j = 0; j < 4; j++) for (let i = 0; i < 4; i++) m.push(i < 3 && j < 3 ? SG[i] * SG[j] * R[j * 4 + i] : (i === j ? 1 : 0));
  $('cube').style.transform = 'matrix3d(' + m.map(v => v.toFixed(5)).join(',') + ')';
  // axes of the model frame, projected like the camera sees them
  const qi = camera.quaternion.clone().invert(), cols = {X: '#d23c3c', Y: '#2f9a3f', Z: '#2f6fd0'};
  let s = '';
  for (const a of ['X', 'Y', 'Z']) {
    const v = toWorldDir(AXIS[a]).applyQuaternion(qi);
    const x = v.x * 22, y = -v.y * 22;
    s += `<line x1="0" y1="0" x2="${x.toFixed(1)}" y2="${y.toFixed(1)}" stroke="${cols[a]}" stroke-width="2" stroke-linecap="round"/><text x="${(x * 1.25).toFixed(1)}" y="${(y * 1.25 + 3).toFixed(1)}" fill="${cols[a]}" text-anchor="middle">${a}</text>`;
  }
  $('axes').innerHTML = s;
}
for (const id of ['vcw', 'home']) $(id).addEventListener('pointerdown', e => e.stopPropagation());

/* ------------------------------------------------------------------ hover: name and highlight */
const ray = new THREE.Raycaster(), mouse = new THREE.Vector2();
let hoverT = 0, dragging = false;
function partOf(o) { while (o && !(o.userData && o.userData.part)) o = o.parent; return o; }
function labelOf(hit) {
  // nearest named ancestor below the part (KiCad names component nodes by reference; '=>' nodes are shape refs)
  // prefer a reference designator (R238, U4) over sub-shape names such as FRAME or MOLD
  const P = partOf(hit), useful = n => n && !/^=>|^mesh|^Mesh|^node_?\d*$|^$/.test(n), isRef = n => /^[A-Z]{1,4}\d{1,4}[A-Z]?(_\d+)?$/.test(n);
  let o = hit, first = null, ref = null;
  while (o && o !== P.parent) { if (useful(o.name)) { if (!first) first = o; if (isRef(o.name)) { ref = o; break; } } o = o.parent; }
  const node = ref || first;
  if (node) return {P, node, name: node.name};
  if (P.userData.part.isPcb) return {P, node: hit, name: 'PCB (board, copper, mask or silkscreen)'};
  return {P, node: P, name: P.userData.part.name || '(unnamed)'};
}
function setHighlight(obj) {
  if (V.hoverObj === obj) return;
  const paint = (o, on) => o && o.traverse(m => { if (m.isMesh) for (const mm of [].concat(m.material)) if (mm.emissive) mm.emissive.copy(on ? new THREE.Color(0x7a5a00) : (mm.userData.base.emissive || new THREE.Color(0))); });
  paint(V.hoverObj, false); V.hoverObj = obj; paint(obj, true); schedule();
}
function hideTip() { $('tip').hidden = true; setHighlight(null); }
function describe(name, P) {
  const ref = String(name).replace(/_\d+$/, '');
  const r = STATE.refIndex.get(ref);
  const meta = P.userData.part;
  const G = V.groups.get(meta.group);
  let html = `<b>${esc(meta.isPcb ? ref : (meta.label || name))}</b><span class="muted">group: ${esc(G ? G.label : meta.group)}</span>`;
  if (r) html += `<span>${esc(r.value || r.mpn)} · ${esc(r.function)}</span><span class="muted">${esc(r.mpn)} · ${esc(r.mfr)}${r.lcsc ? ' · ' + esc(r.lcsc) : ''}</span>`;
  else if (meta.isPcb && ref !== meta.name) html += '<span class="muted">not a BOM line (board, test point, hole or logo)</span>';
  const nm = V.nodes && V.nodes.get(name);
  if (nm && (nm.description || nm.desc)) html += `<span>${esc(nm.description || nm.desc)}</span>`;
  const pn = meta.isPcb && STATE.meta && Array.isArray(STATE.meta.pcb_nodes) ? STATE.meta.pcb_nodes.find(x => x.ref === ref) : null;
  const src = pn ? pn.model_source : (meta.name === name ? meta.source : ''), acc = pn ? pn.accuracy : (meta.name === name ? meta.accuracy : '');
  if (src || acc) html += `<span class="muted">3D model: ${esc(src)}${acc ? ' · accuracy ' + esc(acc) : ''}</span>`;
  else if (meta.isPcb && G && G.components_without_model && G.components_without_model.includes(ref)) html += '<span class="muted">no 3D model (stand-in)</span>';
  return {html, short: (meta.isPcb ? ref : (meta.label || name)) + (r ? ' · ' + (r.value || r.mpn) : '')};
}
stage.addEventListener('pointerdown', () => { dragging = true; hideTip(); });
window.addEventListener('pointerup', () => { dragging = false; });
stage.addEventListener('pointerleave', hideTip);
stage.addEventListener('pointermove', e => {
  if (!V.ok || dragging || e.buttons) return;
  const now = performance.now(); if (now - hoverT < 60) return; hoverT = now;
  const rect = canvas.getBoundingClientRect();
  mouse.set(((e.clientX - rect.left) / rect.width) * 2 - 1, -((e.clientY - rect.top) / rect.height) * 2 + 1);
  ray.setFromCamera(mouse, camera);
  const vis = [...V.groups.values()].filter(g => g.obj.visible).map(g => g.obj);
  const planes = renderer.clippingPlanes || [];
  const xray = $('t-xray').checked ? new Set([...quickGroups('enclosure'), ...quickGroups('lid')].map(g => g.id)) : null;
  const hit = ray.intersectObjects(vis, true).find(h => h.object.visible && planes.every(p => p.distanceToPoint(h.point) >= 0) && !(xray && xray.has(partOf(h.object).userData.part.group)));
  if (!hit) { hideTip(); $('part').innerHTML = '<span class="muted">Nothing under the pointer.</span>'; return; }
  const {P, node, name} = labelOf(hit.object);
  V.hoverGroup = P.userData.part.group;
  setHighlight(node);
  const d = describe(name, P);
  $('part').innerHTML = d.html;
  const tip = $('tip'); tip.textContent = d.short; tip.hidden = false;
  const sr = stage.getBoundingClientRect();
  tip.style.left = Math.min(e.clientX - sr.left, sr.width - 200) + 'px'; tip.style.top = (e.clientY - sr.top) + 'px';
});

/* ------------------------------------------------------------------ screenshot */
$('shot').onclick = () => {
  setHighlight(null); draw();
  canvas.toBlob(b => {
    if (!b) return;
    const a = document.createElement('a'); a.href = URL.createObjectURL(b);
    a.download = 'desktop-speaker-' + new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-') + '.png';
    document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 2000);
  }, 'image/png');
};

/* ------------------------------------------------------------------ side panel spec and notes */
function fillCadSpec() {
  const m = STATE.meta, items = [];
  if (m) {
    if (m.version || m.generated || m.date) items.push(['CAD', [m.version, m.generated || m.date].filter(Boolean).join(' · ')]);
    let sp = m.spec || m.specs || [];
    if (!Array.isArray(sp)) sp = Object.entries(sp).map(([k, v]) => ({k, v}));
    for (const o of sp) items.push([o.k || o.key || o.name, o.v ?? o.value]);
    const kd = m.key_dimensions || {}, num = a => Array.isArray(a) ? a.join(' × ') : a;
    if (kd.outer_W_H_D_mm) items.push(['Outer W × H × D', num(kd.outer_W_H_D_mm) + ' mm']);
    if (kd.board_mm) items.push(['Board', num(kd.board_mm) + ' mm']);
    if (kd.woofer_chamber_L && kd.woofer_chamber_L.net != null) items.push(['Woofer chamber', kd.woofer_chamber_L.net + ' L net']);
    if (kd.main_chamber_L && kd.main_chamber_L.net != null) items.push(['Main chamber', kd.main_chamber_L.net + ' L net']);
    const st = STATE.cadStatus || {};
    if (st.unintended_overlaps != null) items.push(['Interference', st.unintended_overlaps + ' unintended overlaps of ' + (st.solids || '?') + ' solids']);
    if (st.board) items.push(['Board in CAD', st.board]);
  }
  if (V.metaBox && !V.metaBox.isEmpty()) { const s = V.metaBox.getSize(new THREE.Vector3()); items.push(['Model extent', `${s.x.toFixed(0)} × ${s.y.toFixed(0)} × ${s.z.toFixed(0)} mm`]); }
  if (V.parts.length) items.push(['Parts loaded', V.parts.length + ' in ' + V.groups.size + ' groups']);
  const st = STATE.cadStatus; if (st && (st.state || st.status)) items.push(['Export status', [st.state || st.status, st.updated].filter(Boolean).join(' · ')]);
  const s = STATE.specs;
  if (s) {
    const pick = (list, re) => (list || []).find(o => re.test(o.k));
    const want = m && m.key_dimensions ? [[s.overview, /driver/i], [s.overview, /battery|pack/i]] : [[s.mechanical, /outer size/i], [s.overview, /board|pcb/i], [s.overview, /driver/i], [s.overview, /battery|pack/i]];
    for (const [l, re] of want) { const o = pick(l, re); if (o && !items.some(i => i[0] === o.k)) items.push([o.k, o.v]); }
  }
  const short = v => { let t = String(v ?? '').split(/;|\s\(/)[0].trim(); if (t.length > 46) t = t.slice(0, 44).replace(/[\s,]+\S*$/, '') + '…'; return t; };
  $('cadspec').innerHTML = items.map(([k, v]) => `<dt>${esc(k)}</dt><dd title="${esc(v)}">${esc(short(v))}</dd>`).join('') || '<dt>CAD</dt><dd>not loaded</dd>';
  $('cadmeta').textContent = m ? [m.version, m.units && 'units ' + m.units, m.up_axis && m.up_axis + ' up'].filter(Boolean).join(' · ') : 'no metadata';
}
function fillCadNotes(m) {
  if (!m) return;
  const st = STATE.cadStatus || {}, fr = m.frame || {};
  const desc = [m.description || m.title, st.verdict, typeof fr === 'object' ? [fr.cad && 'CAD frame: ' + fr.cad, fr.gltf_from_cad && 'glTF frame: ' + fr.gltf_from_cad, fr.front && 'Front: ' + fr.front].filter(Boolean).join('. ') : '']
    .concat(Array.isArray(st.problems) && st.problems.length ? ['Known problems: ' + st.problems.join('; ')] : []).filter(Boolean);
  if (desc.length) $('caddesc').innerHTML = desc.map(d => `<p style="margin:0 0 6px">${esc(d)}</p>`).join('');
  const li = l => (l || []).map(x => `<li>${esc(typeof x === 'string' ? x : (x.item || x.text || x.detail || JSON.stringify(x)))}</li>`).join('');
  if (m.assumptions && m.assumptions.length) $('cadassume').innerHTML = li(m.assumptions);
  if (m.open_items && m.open_items.length) $('cadopen').innerHTML = li(m.open_items);
  const auto = [...V.groups.values()].filter(g => g.autoExplode).map(g => g.label);
  if (auto.length) $('cadfoot').textContent += ' Explode directions guessed from the model (no vector in meta.json) for: ' + auto.join(', ') + '.';
}

if (renderer) { buildCube(); bootCad().catch(e => { console.error(e); showNoCad('The CAD files could not be loaded (' + e.message + ').'); }); }
window.addEventListener('error', e => console.error('page error', e.message));
