// Hero drawings for the kit packaging: a flat side view of the kit's rocket in the
// brand's line style (Night outlines, Paper-white parts, orange fins = fletching),
// with the flight-arc motif. Sizes are the real kit designs in mm (README "Kit designs").
// Swap for a traced render from the generator (docs/assembly) when one suits.
//
// <div class="k-hero" data-kit="starter" data-angle="0" data-scene="tall"></div>

const KITS = {
  // L overall, od body, nose (showing), top (the top body section B showing, 0 when
  // the body is one print: no joint line), chev (where the chevron decals sit,
  // below the nose), fin root/tip/span/sweep
  mini:    { L: 190, od: 16.4, nose: 51, top: 0, chev: 28, root: 45, tip: 22, span: 22, sweep: 22 },
  starter: { L: 300, od: 21.4, nose: 66, top: 0, chev: 31, root: 49, tip: 24, span: 25, sweep: 24 },
  big:     { L: 360, od: 27.4, nose: 83, top: 38, chev: 38, root: 76, tip: 38, span: 38, sweep: 38 },
};
const C = { night: '#12203A', paper: '#FFFDF8', orange: '#F2652B', sky: '#3D8BFD', grey: '#6E6E73' };

// The rocket, nose tip at (0,0), pointing to -y, in mm.
function rocketPath(k) {
  const R = k.od / 2, cap = 5, yE = k.L - cap, n = k.nose;
  const fin = (s) => `M${s * R} ${yE - k.root}L${s * (R + k.span)} ${yE - k.root + k.sweep}` +
    `L${s * (R + k.span)} ${yE - k.root + k.sweep + k.tip}L${s * R} ${yE}Z`;
  const ln = 'vector-effect="non-scaling-stroke"';
  return `
    <path d="${fin(1)} ${fin(-1)}" fill="${C.orange}" stroke="${C.night}" stroke-width="1.6" stroke-linejoin="round" ${ln}/>
    <path d="M0 0C${R * 0.42} ${n * 0.22} ${R} ${n * 0.55} ${R} ${n}V${yE}H${-R}V${n}C${-R} ${n * 0.55} ${-R * 0.42} ${n * 0.22} 0 0Z"
      fill="${C.paper}" stroke="${C.night}" stroke-width="1.6" stroke-linejoin="round" ${ln}/>
    <path d="M${-R} ${n}H${R}${k.top ? `M${-R} ${n + k.top}H${R}` : ''}" stroke="${C.night}" stroke-width=".8" ${ln}/>
    <path d="M0 ${n + 6}V${yE - 4}" stroke="${C.grey}" stroke-width=".6" stroke-dasharray="7 2 1.5 2" ${ln}/>
    <rect x="${-R * 0.78}" y="${yE}" width="${R * 1.56}" height="${cap}" rx="1" fill="${C.paper}" stroke="${C.night}" stroke-width="1.4" ${ln}/>
    <path d="M${-R * 0.78} ${yE + cap * 0.5}H${R * 0.78}" stroke="${C.night}" stroke-width=".7" ${ln}/>
    <path d="M${-R * 0.55} ${n + k.chev + 14}l${R * 0.55} -6l${R * 0.55} 6v4l${-R * 0.55} -6l${-R * 0.55} 6z
             M${-R * 0.55} ${n + k.chev + 22}l${R * 0.55} -6l${R * 0.55} 6v4l${-R * 0.55} -6l${-R * 0.55} 6z" fill="${C.orange}"/>`;
}

function puffs(x, y, s) {
  const ln = 'vector-effect="non-scaling-stroke"';
  return `<g fill="${C.paper}" stroke="${C.night}" stroke-width="1.4" ${ln}>
    <circle cx="${x - 9 * s}" cy="${y - 5 * s}" r="${5 * s}"/><circle cx="${x + 9 * s}" cy="${y - 4.5 * s}" r="${4.5 * s}"/>
    <circle cx="${x}" cy="${y - 7 * s}" r="${7 * s}"/></g>
    <path d="M${x - 40 * s} ${y}H${x + 40 * s}" stroke="${C.night}" stroke-width="1.6" ${ln}/>`;
}

function chute(x, y, s) {
  const ln = 'vector-effect="non-scaling-stroke"';
  return `<g stroke="${C.night}" stroke-width="1.2" ${ln}>
    <path d="M${x - 14 * s} ${y}A${14 * s} ${11 * s} 0 0 1 ${x + 14 * s} ${y}Z" fill="${C.orange}" stroke-linejoin="round"/>
    <path d="M${x - 14 * s} ${y}L${x} ${y + 17 * s}L${x + 14 * s} ${y}M${x - 5 * s} ${y}L${x} ${y + 17 * s}L${x + 5 * s} ${y}" fill="none"/>
    <rect x="${x - 2 * s}" y="${y + 17 * s}" width="${4 * s}" height="${9 * s}" fill="${C.paper}"/></g>`;
}

function stars(list) {
  return list.map(([x, y]) => `<path d="M${x - 4} ${y}H${x + 4}M${x} ${y - 4}V${y + 4}" stroke="${C.sky}" stroke-width="1.3"/>`).join('');
}

// Tall scene for narrow panels: rocket straight up, trail to the pad, arc over to a parachute.
function tallScene(k, W, H) {
  const pad = H - 14, scale = (H * 0.6) / k.L, x = W * 0.36, top = H * 0.2;
  const base = top + k.L * scale;
  const arc = `M${x} ${top - 8}Q${x + 6} ${H * 0.05} ${W * 0.62} ${H * 0.06}Q${W * 0.86} ${H * 0.08} ${W * 0.84} ${H * 0.26}`;
  return `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg">
    ${stars([[W * 0.82, H * 0.42], [W * 0.12, H * 0.12], [W * 0.9, H * 0.6], [W * 0.14, H * 0.5]])}
    <path d="${arc}" fill="none" stroke="${C.night}" stroke-width="1.6" stroke-dasharray="6 5" stroke-linecap="round"/>
    ${chute(W * 0.84, H * 0.29, Math.min(1.4, W / 120))}
    <path d="M${x} ${base + 10}V${pad - 16}" stroke="${C.orange}" stroke-width="2" stroke-dasharray="1.5 5" stroke-linecap="round"/>
    ${puffs(x, pad, Math.min(1.3, W / 150))}
    <g transform="translate(${x} ${top}) scale(${scale})">${rocketPath(k)}</g>
  </svg>`;
}

// Wide scene: the rocket at 45 degrees up and to the right, as on covers.
function wideScene(k, W, H) {
  const scale = (Math.min(W, H) * 0.88) / k.L, x0 = W * 0.18, y0 = H - 10;
  const cx = W * 0.5, cy = H * 0.52;
  return `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg">
    ${stars([[W * 0.9, H * 0.18], [W * 0.15, H * 0.2], [W * 0.93, H * 0.7]])}
    <path d="M${x0} ${y0 - 14}L${cx - k.L * scale * 0.42} ${cy + k.L * scale * 0.42}" stroke="${C.orange}" stroke-width="2" stroke-dasharray="1.5 5" stroke-linecap="round"/>
    <path d="M${cx + k.L * scale * 0.4} ${cy - k.L * scale * 0.4}Q${W * 0.86} ${H * 0.02} ${W * 0.97} ${H * 0.3}" fill="none" stroke="${C.night}" stroke-width="1.5" stroke-dasharray="6 5" stroke-linecap="round"/>
    ${puffs(x0, y0, 0.8)}
    <g transform="translate(${cx} ${cy}) rotate(45) translate(0 ${-k.L * scale / 2}) scale(${scale})">${rocketPath(k)}</g>
  </svg>`;
}

for (const el of document.querySelectorAll('.k-hero')) {
  const k = KITS[el.dataset.kit || 'starter'];
  const r = el.getBoundingClientRect();
  const W = Math.round(r.width), H = Math.round(r.height);
  el.innerHTML = el.dataset.scene === 'wide' ? wideScene(k, W, H) : tallScene(k, W, H);
}
if (new URLSearchParams(location.search).get('dieline')) document.body.classList.add('show-dieline');
