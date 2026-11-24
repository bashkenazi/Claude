"""AI one page: every numbered section collapses and can be re-ordered (arrows or drag); layout kept per viewer
in localStorage 'op-layout'. Marker "op-layout v1"."""
import sys
P = sys.argv[1]; s = open(P, encoding='utf-8').read()
if 'op-layout v1' in s: print('already'); sys.exit(0)
def rep(old, new):
    global s
    assert s.count(old) == 1, (old[:90], s.count(old)); s = s.replace(old, new)
rep("""const sec = (id, title, srcTxt, body) => `<section class="panel" id="op-${id}"><div class="panel-h"><h2>${title}</h2><span class="sub">${srcTxt}</span></div>${body}</section>`;""",
"""/* op-layout v1 */
const sec = (id, title, srcTxt, body) => `<section class="panel op-sec" id="op-${id}" data-sec="${id}"><div class="panel-h op-sec-h"><button type="button" class="op-tog" aria-expanded="true" aria-controls="op-b-${id}" title="Collapse or expand">▾</button><h2>${title}</h2><span class="sub">${srcTxt}</span><span class="op-mv" role="group" aria-label="Move section"><button type="button" class="op-up" title="Move up" aria-label="Move up">↑</button><button type="button" class="op-dn" title="Move down" aria-label="Move down">↓</button><span class="op-grip" draggable="true" title="Drag to reorder" aria-hidden="true">⠿</span></span></div><div class="op-body" id="op-b-${id}">${body}</div></section>`;""")
rep("""C.innerHTML = h;
C.querySelectorAll('[data-opj]').forEach(a => a.addEventListener('click', e => { e.preventDefault(); const t = document.getElementById('op-' + a.dataset.opj); if (t) t.scrollIntoView({ behavior: 'smooth', block: 'start' }); }));""",
"""C.innerHTML = h;
opLayout(C);
C.querySelectorAll('[data-opj]').forEach(a => a.addEventListener('click', e => { e.preventDefault(); const t = document.getElementById('op-' + a.dataset.opj); if (t) { if (t.classList.contains('op-col')) opLayoutSet(C, t.dataset.sec, false); t.scrollIntoView({ behavior: 'smooth', block: 'start' }); } }));""")
# helpers before opRender
rep("function opRender() {", r"""const opLGet = () => { let o = {}; try { o = JSON.parse(localStorage.getItem('op-layout') || '{}') || {}; } catch (e) {} return { order: Array.isArray(o.order) ? o.order : [], col: o.col && typeof o.col === 'object' ? o.col : {} }; };
const opLPut = L => { try { localStorage.setItem('op-layout', JSON.stringify(L)); } catch (e) {} };
function opLayoutSet(C, id, collapse) {
  const L = opLGet(); if (collapse) L.col[id] = 1; else delete L.col[id]; opLPut(L);
  const S = C.querySelector(`.op-sec[data-sec="${id}"]`); if (!S) return;
  S.classList.toggle('op-col', !!collapse); const b = S.querySelector('.op-tog'); b.setAttribute('aria-expanded', String(!collapse)); b.textContent = collapse ? '▸' : '▾';
}
function opLayout(C) {
  const secs = [...C.querySelectorAll(':scope > .op-sec')]; if (!secs.length) return;
  const anchor = secs[0].previousElementSibling, L = opLGet(), def = secs.map(x => x.dataset.sec);
  const rank = id => { const i = L.order.indexOf(id); return i < 0 ? 1000 + def.indexOf(id) : i; };
  const place = order => { let prev = anchor; order.forEach(id => { const el = C.querySelector(`.op-sec[data-sec="${id}"]`); if (!el) return; if (prev) prev.after(el); else C.prepend(el); prev = el; });
    const nav = C.querySelector('.op-jump'); if (nav) order.forEach(id => { const a = nav.querySelector(`[data-opj="${id}"]`); if (a) nav.appendChild(a); }); };
  const cur = () => [...C.querySelectorAll(':scope > .op-sec')].map(x => x.dataset.sec);
  const save = () => { const L2 = opLGet(); L2.order = cur(); opLPut(L2); };
  place(def.slice().sort((a, b) => rank(a) - rank(b)));
  secs.forEach(S => {
    const id = S.dataset.sec; if (L.col[id]) opLayoutSet(C, id, true);
    S.querySelector('.op-tog').addEventListener('click', () => opLayoutSet(C, id, !S.classList.contains('op-col')));
    S.querySelector('.op-sec-h h2').addEventListener('click', () => opLayoutSet(C, id, !S.classList.contains('op-col')));
    const mv = d => { const o = cur(), i = o.indexOf(id), j = i + d; if (j < 0 || j >= o.length) return; [o[i], o[j]] = [o[j], o[i]]; place(o); save(); S.scrollIntoView({ block: 'nearest' }); S.querySelector(d < 0 ? '.op-up' : '.op-dn').focus(); };
    S.querySelector('.op-up').addEventListener('click', () => mv(-1)); S.querySelector('.op-dn').addEventListener('click', () => mv(1));
    const g = S.querySelector('.op-grip');
    g.addEventListener('dragstart', e => { e.dataTransfer.effectAllowed = 'move'; try { e.dataTransfer.setData('text/plain', id); } catch (x) {} try { e.dataTransfer.setDragImage(S.querySelector('.op-sec-h'), 20, 20); } catch (x) {} C.dataset.opDrag = id; S.classList.add('op-dragging'); });
    g.addEventListener('dragend', () => { delete C.dataset.opDrag; C.querySelectorAll('.op-sec').forEach(x => x.classList.remove('op-dragging', 'op-drop-a', 'op-drop-b')); });
    S.addEventListener('dragover', e => { const src = C.dataset.opDrag; if (!src || src === id) return; e.preventDefault(); const r = S.getBoundingClientRect(), after = e.clientY > r.top + Math.min(r.height / 2, 80); S.classList.toggle('op-drop-a', after); S.classList.toggle('op-drop-b', !after); });
    S.addEventListener('dragleave', () => S.classList.remove('op-drop-a', 'op-drop-b'));
    S.addEventListener('drop', e => { const src = C.dataset.opDrag; if (!src || src === id) return; e.preventDefault(); const after = S.classList.contains('op-drop-a'); const o = cur().filter(x => x !== src); o.splice(o.indexOf(id) + (after ? 1 : 0), 0, src); S.classList.remove('op-drop-a', 'op-drop-b'); place(o); save(); });
  });
  const bar = C.querySelector('.op-jump');
  if (bar && !C.querySelector('.op-lay')) bar.insertAdjacentHTML('afterend', `<div class="op-lay" role="group" aria-label="Section layout"><button type="button" class="nav-reset" data-oplay="col">Collapse all</button><button type="button" class="nav-reset" data-oplay="exp">Expand all</button><button type="button" class="nav-reset" data-oplay="reset">Reset order</button><span class="sub">Click a section title to collapse it; drag ⠿ or use the arrows to reorder.</span></div>`);
  C.querySelectorAll('[data-oplay]').forEach(b => b.addEventListener('click', () => { const k = b.dataset.oplay;
    if (k === 'reset') { const L2 = opLGet(); L2.order = []; opLPut(L2); place(def); return; }
    cur().forEach(id => opLayoutSet(C, id, k === 'col')); }));
}
function opRender() {""")
css = """
/* op-layout v1 */
.op-sec-h { justify-content: flex-start; align-items: center; }
.op-sec-h h2 { cursor: pointer; user-select: none; }
.op-sec-h .sub { flex: 1 1 240px; }
.op-tog { border: 0; background: none; cursor: pointer; font-size: 14px; width: 22px; padding: 0; color: var(--ink-2); }
.op-mv { display: inline-flex; gap: 4px; align-items: center; margin-left: auto; }
.op-mv button { border: 1px solid var(--rule-2); background: var(--surface); color: var(--ink-2); border-radius: 5px; width: 26px; height: 24px; cursor: pointer; padding: 0; font-size: 13px; }
.op-mv button:hover { background: var(--surface-2); }
.op-grip { cursor: grab; color: var(--muted); font-size: 16px; padding: 0 4px; user-select: none; }
.op-sec.op-col > .op-body { display: none; }
.op-sec.op-col { gap: 0; }
.op-sec.op-dragging { opacity: .45; }
.op-sec.op-drop-b { box-shadow: 0 -3px 0 var(--accent); }
.op-sec.op-drop-a { box-shadow: 0 3px 0 var(--accent); }
.op-body { display: flex; flex-direction: column; gap: 12px; min-width: 0; }
.op-lay { display: flex; flex-wrap: wrap; gap: 6px 8px; align-items: center; }
"""
i = s.find('/* op-roi-co v1 */\ntable'); assert i > 0; s = s[:i] + css + s[i:]
open(P, 'w', encoding='utf-8').write(s); print('applied')
