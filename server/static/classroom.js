// Classroom tools in the designer (owner approved 2026-10-19; server side: server/classroom.py).
// index.html imports this once it has started and set window.rbDesigner (its hook into the
// page's state). Kept in its own file so the designer's main script only grows by a few lines.
//  - ⋯ → Hand in to my class: a class code + a first name or nickname sends the rocket on
//    screen to the teacher (POST /api/join/<code>). No account; we keep only the nickname.
//  - ⋯ → Altitude calculator: /tools/altitude in a dialog.
//  - ▾ → Mission card (print): /mission/<build id>, a one-page printable card.
//  - ⋯ → Launch simulator: /launch?build=<id> in a new tab.
//  - /?classsub=<id>: a teacher opens a handed-in rocket (GET /api/class-submissions/<id>).
const D = window.rbDesigner;
const $ = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
const store = (kind, k, v) => { try { v === undefined ? null : kind.setItem(k, v); return kind.getItem(k) || ''; } catch { return ''; } };

const css = document.createElement('style');
css.textContent = `
  #classdlg, #altdlg { border:1px solid var(--line); border-radius:10px; padding:16px 18px; color:var(--ink); background:var(--panel); }
  #classdlg { width:min(420px, 94vw); }
  #classdlg h2, #altdlg h2 { font-size:18px; margin:0 0 4px; }
  #classdlg p { font-size:13.5px; margin:0 0 8px; }
  #classdlg .hint { color:var(--muted); }
  #classdlg label.stack { display:flex; flex-direction:column; align-items:stretch; text-align:left; gap:4px; margin:8px 0 4px; font-size:13px; font-weight:600; }
  #classdlg input { width:100%; padding:8px 10px; border:1px solid var(--line); border-radius:6px; font:inherit; font-size:16px; font-weight:400; color:var(--ink); background:var(--field); }
  #c_code { font:700 22px var(--font-head) !important; letter-spacing:.18em; text-transform:uppercase; }
  .cl-found { min-height:1.2em; font-weight:600; } .cl-found.ok { color:var(--ok); } .cl-found.bad { color:var(--err); }
  .cl-note { padding:8px 10px; border-left:4px solid var(--rb-orange); background:var(--warnbg); border-radius:0 8px 8px 0; color:var(--ink); }
  .cl-rocket { padding:8px 10px; border-radius:8px; background:var(--card); border:1px solid var(--line); }
  #classdlg .autherr { color:var(--err); min-height:1em; margin:6px 0 0; }
  #classdlg menu, #altdlg menu { display:flex; flex-direction:row-reverse; gap:8px; margin:12px 0 0; padding:0; }
  #classdlg menu button, #altdlg .althead button { flex:none; padding:8px 16px; border-radius:6px; font:600 14px var(--font-body); cursor:pointer; border:1px solid var(--line); background:transparent; color:var(--ink); }
  #c_go, #c_ok { background:var(--ink) !important; color:var(--bg) !important; border-color:var(--ink) !important; }
  #c_go:disabled { opacity:.6; cursor:wait; }
  #altdlg { width:min(940px, 96vw); height:min(820px, 92dvh); padding:0; overflow:hidden; }
  #altdlg[open] { display:flex; flex-direction:column; }
  #altdlg .althead { display:flex; align-items:center; gap:12px; padding:10px 14px; border-bottom:1px solid var(--line); }
  #altdlg .althead h2 { margin:0; flex:1; }
  #altdlg .althead a { font-size:13.5px; }
  #altdlg iframe { flex:1; width:100%; border:0; background:var(--bg); }
`;
document.head.append(css);

document.body.insertAdjacentHTML('beforeend', `
<dialog id="classdlg" aria-labelledby="classtitle">
  <form id="classform" novalidate>
    <h2 id="classtitle">Hand in to my class</h2>
    <p class="hint">Your teacher gives you a class code. This sends the rocket on your screen to your teacher.</p>
    <label class="stack">Class code <input id="c_code" maxlength="9" autocomplete="off" autocapitalize="characters" spellcheck="false" placeholder="ABC234" aria-describedby="c_class"></label>
    <p class="cl-found" id="c_class" aria-live="polite"></p>
    <label class="stack">Your first name or a nickname <input id="c_nick" maxlength="20" autocomplete="off" spellcheck="false" aria-describedby="c_note"></label>
    <p class="cl-note" id="c_note"><b>Don't use your full name.</b> Just a first name or a nickname your teacher will know. Nothing else about you is sent.</p>
    <p class="cl-rocket" id="c_rocket"></p>
    <p class="autherr" id="c_err" role="alert"></p>
    <menu><button type="submit" id="c_go">Hand it in</button><button type="button" id="c_cancel">Cancel</button></menu>
  </form>
  <div id="c_done" hidden>
    <h2 id="c_donetitle">Handed in!</h2>
    <p id="c_donetext"></p>
    <menu><button type="button" id="c_ok">Done</button></menu>
  </div>
</dialog>
<dialog id="altdlg" aria-labelledby="alttitle">
  <div class="althead"><h2 id="alttitle">Altitude calculator</h2><a href="/tools/altitude" target="_blank" rel="noopener">Open as a page ↗</a><button type="button" id="altclose">Close</button></div>
  <iframe id="altframe" title="Altitude calculator"></iframe>
</dialog>`);

// ---------- hand in to a class ----------
const dlg = $('classdlg'), codeEl = $('c_code'), nickEl = $('c_nick'), err = $('c_err'), found = $('c_class');
let lookedUp = null;  // {code, name, open} once the typed code is found
const norm = s => s.replace(/[\s-]/g, '').toUpperCase();
async function lookup() {
  const code = norm(codeEl.value);
  lookedUp = null; found.className = 'cl-found'; found.textContent = '';
  if (code.length < 6) return;
  try {
    const r = await fetch(`/api/join/${encodeURIComponent(code)}`), d = await r.json().catch(() => ({}));
    if (norm(codeEl.value) !== code) return;  // typed on meanwhile
    if (!r.ok) { found.className = 'cl-found bad'; found.textContent = typeof d.detail === 'string' ? d.detail : 'Check the code.'; return; }
    lookedUp = d;
    found.className = d.open ? 'cl-found ok' : 'cl-found bad';
    found.textContent = d.open ? `✓ ${d.name}` : `${d.name} isn't taking rockets any more. Ask your teacher.`;
  } catch { found.className = 'cl-found bad'; found.textContent = 'Could not reach the server.'; }
}
codeEl.addEventListener('input', () => { codeEl.value = codeEl.value.toUpperCase(); lookup(); });
function openClass() {
  $('classform').hidden = false; $('c_done').hidden = true; err.textContent = '';
  codeEl.value = codeEl.value || store(localStorage, 'rbClassCode');
  nickEl.value = nickEl.value || store(sessionStorage, 'rbClassNick');
  const r = D.report();
  $('c_rocket').innerHTML = r
    ? `Handing in <b>${esc(D.baseName())}</b>: ${esc(r.stability.length_mm.toFixed(0))} mm tall, score <b>${r.stability.margin_cal.toFixed(2)} cal</b>.${D.dirty() ? ' <b>You changed it since the last build:</b> press Build first so your teacher sees the latest.' : ''}`
    : 'Build your rocket first (press <b>Build my rocket</b>), then hand it in.';
  lookup();
  dlg.showModal();
  (codeEl.value ? nickEl : codeEl).focus();
}
$('c_cancel').onclick = () => dlg.close();
$('c_ok').onclick = () => dlg.close();
$('classform').addEventListener('submit', async e => {
  e.preventDefault();
  const r = D.report(), code = norm(codeEl.value), nick = nickEl.value.trim();
  if (!r) { err.textContent = 'Press Build first, then hand in your rocket.'; return; }
  if (D.dirty()) { err.textContent = 'You changed your rocket since the last build. Press Build first, then hand it in.'; return; }
  if (code.length !== 6) { err.textContent = 'The class code has 6 letters and numbers.'; codeEl.focus(); return; }
  if (!nick) { err.textContent = 'Type your first name or a nickname.'; nickEl.focus(); return; }
  const go = $('c_go'); go.disabled = true; err.textContent = '';
  try {
    const res = await fetch(`/api/join/${encodeURIComponent(code)}`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nickname: nick, build_id: r.id, design_name: D.name() }) });
    const d = await res.json().catch(() => ({}));
    if (!res.ok) { err.textContent = typeof d.detail === 'string' ? d.detail : (d.detail || []).map(x => x.msg).join('; ') || `Error ${res.status}`; return; }
    store(localStorage, 'rbClassCode', code); store(sessionStorage, 'rbClassNick', d.nickname);
    $('classform').hidden = true; $('c_done').hidden = false;
    $('c_donetitle').textContent = d.replaced ? 'Updated!' : 'Handed in!';
    $('c_donetext').innerHTML = `${d.replaced ? 'Your newer rocket replaced the one you handed in before' : 'Your rocket is in'} <b>${esc(d.class)}</b> as <b>${esc(d.nickname)}</b>. Your teacher can see it now. Changed it again? Build it and hand it in with the same name.`;
  } catch { err.textContent = 'Could not reach the server; check your connection and try again.'; }
  finally { go.disabled = false; }
});
$('classjoin').onclick = openClass;

// ---------- altitude calculator ----------
const alt = $('altdlg');
$('altcalc').onclick = () => {
  if (!$('altframe').src) $('altframe').src = '/tools/altitude?embed=1';
  alt.showModal();
};
$('altclose').onclick = () => alt.close();

// ---------- mission card and launch simulator: follow the rocket on screen ----------
const card = $('missioncard'), sim = $('launchsim');
function follow() {
  const r = D.report();
  card.classList.toggle('off', !r); sim.classList.toggle('off', !r);
  if (!r) return;
  const q = new URLSearchParams({ name: D.baseName() });
  if (D.designId()) q.set('design', D.designId());
  card.href = `/mission/${encodeURIComponent(r.id)}?${q}`;
  sim.href = `/launch?build=${encodeURIComponent(r.id)}`;
}
addEventListener('rb:built', follow);
card.addEventListener('click', follow);  // picks up a renamed or newly saved design
follow();

// ---------- a teacher opening a handed-in rocket: /?classsub=<id> ----------
const sub = new URLSearchParams(location.search).get('classsub');
if (sub) {
  try {
    const r = await fetch(`/api/class-submissions/${encodeURIComponent(sub)}`), d = await r.json().catch(() => ({}));
    if (r.ok) {
      D.unlock();
      D.openParams(d.params, d.design_name);
      D.say(`Opened ${d.nickname}'s rocket from your class. It's a copy: changes here don't change what they handed in.`, 'ok');
    } else {
      D.say(r.status === 401 ? 'Sign in as the class\'s teacher to open a handed-in rocket.' : (d.detail || 'That rocket could not be opened.'), 'err');
    }
  } catch {}
}
