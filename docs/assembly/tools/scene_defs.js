// The guide's drawings. Each scene's build(root) adds objects to root (rocket
// coordinates: mm, z up the rocket axis, z = 0 at the tail) and returns the
// view: dir (from the subject toward the camera), up, W (final pixel width),
// line (outline width in px), margin (mm), focus (a world Box3: only what is
// inside it is framed; the rest runs off the edge) and points (labels).
//
// Not to scale: the parachute, cord and wadding are drawn small so they fit.
export function defineScenes(h) {
  const { THREE, V, COL, R, part, cyl, lathe, tube, rope, dashed, ball, knot, arrow, turnArrow, motor, igniter,
          chuteOpen, chuteRolled, wadding, mark, viewDir, deg, mesh } = h;

  // Rocket axis horizontal, nose to the right: rocket z -> world x, rocket x -> world -z.
  const sideways = (root, g = new THREE.Group()) => {
    g.rotation.y = Math.PI / 2; root.add(g); g.updateMatrixWorld(true); return g;
  };
  // A section plane given in rocket coordinates (keeps the side the normal
  // points to), moved into the world through group g.
  const cutPlane = (g, n = V(1, 0, 0), c = 0) => {
    g.updateMatrixWorld(true);
    return [new THREE.Plane(n.clone().normalize(), c).applyMatrix4(g.matrixWorld)];
  };
  // Focus boxes: a stretch of the axis (rocket z0..z1), radius r.
  const focusSide = (z0, z1, r) => new THREE.Box3(V(z0, -r, -r), V(z1, r, r));
  const focusUp = (z0, z1, r) => new THREE.Box3(V(-r, -r, z0), V(r, r, z1));
  const P = (key, name) => R[key].info.parts.find(p => p.name === name);
  const cordR = 1.5;   // 1/8 in (3.2 mm) round elastic; flat elastic is the same width
  const lineR = 0.45;  // the parachute's lines, gathered: drawn as one strand
  const line = (pts, opts = {}) => rope(pts, lineR, { color: COL.night, braid: 0, ends: [false, false], ...opts });

  // Points of a cord wrapped round a straight one (the "two overhand knots",
  // drawn as two snug turns): `turns` turns round the axis through c along
  // a, starting on side u; rw = centre distance (the two cords touching).
  function wraps(c, a, u, { turns = 2, rw = 2 * cordR + 0.1, pitch = 2.3 * cordR, sense = 1, n = 28 } = {}) {
    a = a.clone().normalize();
    u = u.clone().sub(a.clone().multiplyScalar(u.dot(a))).normalize();
    const w = a.clone().cross(u).multiplyScalar(sense);
    const pts = [];
    for (let i = 0; i <= turns * n; i++) {
      const th = i / n * Math.PI * 2;
      pts.push(c.clone().addScaledVector(a, pitch * th / (2 * Math.PI)).addScaledVector(u, rw * Math.cos(th)).addScaledVector(w, rw * Math.sin(th)));
    }
    return pts;
  }

  // The cord at the anchor strap: the long part comes down the slot behind
  // the bar, under it, up in front, and the end is tied round the long part
  // just above the bar. `top`: how far above the bar the long part is drawn.
  // Returns the group and the points the labels and other cords need.
  function strapRig(I, { top = 22 } = {}) {
    const S = I.strap, zt = S.z_top, apex = S.z_bot + S.spring;
    const yb = S.front + S.t + S.hole_depth / 2;   // in the slot behind the bar
    const yf = S.front - cordR - 0.35;              // in front of the bar
    const yc = 2.4, xf = -3.2;                      // the long part above the bar; the end, beside it
    const hz = zt + 6.2, rw = 2 * cordR + 0.1, pitch = 2.3 * cordR;
    const w = wraps(V(0, yc, hz), V(0, 0, 1), V(-1, 0, 0), { rw, pitch });
    const zEnd = hz + 2 * pitch;
    const pts = [V(0, yc, zt + top), V(0, yc, zEnd + 5), V(0, yc, zt + 7), V(0.35, 3.5, zt + 3.6), V(0.85, 5.7, zt + 1.1),
      V(0.9, yb, zt - 1.6), V(0.9, yb, apex - 0.3), V(0.5, yb - 0.9, apex - cordR - 0.9), V(-1.2, S.front + 0.9, apex - cordR - 1.4),
      V(xf + 0.4, yf + 0.2, apex - cordR - 0.7), V(xf, yf, apex + 0.6), V(xf, yf, zt - 0.4), V(xf + 0.1, yf + 0.3, zt + 2.6),
      ...w.slice(1), V(-rw - 1.6, yc - 1.4, zEnd + 1.0), V(-rw - 4.4, yc - 2.2, zEnd + 0.5)];
    const g = new THREE.Group();
    g.add(rope(pts, cordR, { ends: [false, true] }));
    return { group: g, top: V(0, yc, zt + top), knot: V(-rw * 0.7, yc - rw * 0.7, hz + pitch), yc };
  }

  // The cord at the nose's tie bar (bar along x, z = nz .. nz + 2, y = -1 .. 1):
  // up behind the bar, over it, down in front, tied round the long part
  // below. The long part leaves straight down at (x, ys) to z = nz - down.
  function noseRig(nz, { x = 0, down = 30 } = {}) {
    const yo = 1 + cordR + 0.15, over = nz + 2 + cordR + 0.1, ys = -1.0;
    const rw = 2 * cordR + 0.1, pitch = 2.3 * cordR, hz = nz - 4.4;
    const w = wraps(V(x, ys, hz), V(0, 0, -1), V(0, 1, 0), { rw, pitch });
    const zEnd = hz - 2 * pitch;
    const pts = [V(x, ys, nz - down), V(x, ys, zEnd - 6), V(x, ys, nz - 4.2), V(x, -yo + 0.35, nz - 1.5), V(x, -yo, nz + 0.7),
      V(x, -yo * 0.7, over - 0.5), V(x, 0, over), V(x, yo * 0.7, over - 0.5), V(x, yo, nz + 0.7), V(x, yo - 0.1, nz - 1.6),
      ...w.slice(1), V(x + 1.6, ys + rw + 1.1, zEnd - 1.0), V(x + 4.2, ys + rw + 1.9, zEnd - 1.3)];
    const g = new THREE.Group();
    g.add(rope(pts, cordR, { ends: [false, true] }));
    return { group: g, x, ys, knot: V(x + rw * 0.7, ys + rw * 0.7, hz - pitch), below: zEnd - 2.6, bottom: V(x, ys, nz - down) };
  }

  // The parachute's gathered lines girth-hitched (lark's head) round the
  // cord at (x, ys, z0). state 'loop': the loop passed round behind the
  // cord, its end hanging open in front; 'through': the parachute pushed
  // through that end; 'snug': pulled tight. `far`: where the lines go (to
  // the parachute). Returns the group and a few label points.
  function larks(x, ys, z0, state, far) {
    const g = new THREE.Group();
    const rr = cordR + lineR + 0.05, d = lineR * 1.2;
    const side = (dz, s) => [V(x + rr + 0.45, ys - 0.8, z0 + dz), V(x + rr * 0.7, ys - rr * 0.72, z0 + dz), V(x, ys - rr, z0 + dz),
      V(x - rr, ys, z0 + dz), V(x - rr * 0.6, ys + rr * 0.8, z0 + dz)];
    // The legs (to the parachute). 'through': they run from the hitch down
    // through the loop's end and away to the parachute (far, in front).
    const via = state === 'through'
      ? (dz) => [V(x - 9.5, ys + rr + 12, z0 - 19 + dz), V(x - 4.5, ys + rr + 7.5, z0 - 14 + dz), V(x - 1.6, ys + rr + 3.4, z0 - 11.5 + dz * 0.5),
                 V(x + 1.6, ys + rr - 0.2, z0 - 8.5 + dz * 0.5), V(x + 3.4, ys - 0.4, z0 - 5 + dz * 0.5)]
      : (dz) => [V(x + rr + 4.5, ys - 1.2, z0 + dz * 0.6 - 4)];
    const legs = (dz) => [far.clone().add(V(0, 0, dz * 0.4)), ...via(dz), ...side(dz)];
    const pts = { };
    if (state === 'snug') {
      const A = [...legs(d), V(x, ys + rr, z0 + d), V(x + rr * 0.78, ys + rr * 0.68, z0 + d), V(x + rr + 0.85, ys + 0.95, z0 + 0.25 * d)];
      const B = [...legs(-d), V(x, ys + rr, z0 - d), V(x + rr * 0.78, ys + rr * 0.68, z0 - d), V(x + rr + 0.85, ys + 0.95, z0 - 0.25 * d)];
      g.add(line([...A, ...B.reverse()]));
      pts.hitch = V(x, ys + rr, z0);
    } else {
      // The loop's end hangs open in front of the cord.
      const drop = 17, wdt = 8;
      const A = [...legs(d), V(x + 0.2, ys + rr + 0.2, z0 + d - 0.4), V(x - 1.0, ys + rr + 1.4, z0 - 2.5), V(x - wdt * 0.55, ys + rr + 3.6, z0 - drop * 0.55),
        V(x - wdt * 0.5, ys + rr + 5.4, z0 - drop * 0.92), V(x - wdt * 0.15, ys + rr + 5.6, z0 - drop)];
      const B = [...legs(-d), V(x + 0.2, ys + rr + 0.2, z0 - d - 0.4), V(x - 0.4, ys + rr + 0.8, z0 - 3.0), V(x + wdt * 0.15, ys + rr + 2.4, z0 - drop * 0.55),
        V(x + wdt * 0.3, ys + rr + 4.4, z0 - drop * 0.9), V(x + wdt * 0.05, ys + rr + 5.4, z0 - drop - 0.2)];
      g.add(line([...A, ...B.reverse()]));
      pts.loop = V(x - wdt * 0.5, ys + rr + 4.5, z0 - drop * 0.75);
    }
    return { group: g, points: pts };
  }

  // A cord break mark: two short slanted bars across a gap at p (the cord
  // runs along `dir`), meaning "longer than drawn".
  function breakMark(p, dir, { len = 7, gap = 3.2, t = 0.9 } = {}) {
    const g = new THREE.Group();
    const d = dir.clone().normalize();
    for (const s of [-1, 1]) {
      const b = new THREE.BoxGeometry(len, t, t);
      const m = mesh(b, COL.night, { flat: true, outline: false });
      m.position.copy(p).addScaledVector(d, s * gap / 2);
      const across = V(1, 0, 0).sub(d.clone().multiplyScalar(d.x)).normalize();
      m.quaternion.setFromUnitVectors(V(1, 0, 0), across.clone().applyAxisAngle(V(0, 1, 0), 0).add(d.clone().multiplyScalar(0.45)).normalize());
      g.add(m);
    }
    return g;
  }

  // A curved arrow through points (in launch orange, flat).
  function curvedArrow(pts, r = 1.0, color = COL.orange) {
    const curve = new THREE.CatmullRomCurve3(pts, false, 'centripetal');
    const L = curve.getLength(), head = r * 6;
    const tEnd = 1 - head / L;
    const body = [];
    for (let i = 0; i <= 40; i++) body.push(curve.getPointAt(tEnd * i / 40));
    const grp = new THREE.Group();
    grp.add(tube(body, r, color, { flat: true }));
    const base = curve.getPointAt(tEnd), tip = curve.getPointAt(1);
    const cone = new THREE.ConeGeometry(r * 2.6, head, 24);
    const m = mesh(cone, color, { flat: true });
    m.position.copy(base.clone().add(tip).multiplyScalar(0.5));
    m.quaternion.setFromUnitVectors(V(0, 1, 0), tip.clone().sub(base).normalize());
    grp.add(m);
    return grp;
  }

  // A motor cut in half, as a flat drawing in the y = 0 plane: casing,
  // clay nozzle, propellant (with the igniter cavity), delay, ejection
  // charge, clay cap. Proportions are typical of a black-powder motor.
  function motorCut(I) {
    const r = I.mtr_d / 2, L = I.mtr_len, w = 1.0;
    const g = new THREE.Group();
    const throat = Math.max(1.2, r * 0.18), mouth = Math.max(3, r * 0.55);
    const zN = r * 0.9, zP = L * 0.55, zD = L * 0.82, zE = L * 0.9;
    const shape = (pts, color, dy = 0) => {
      const geo = new THREE.ShapeGeometry(new THREE.Shape(pts.map(([x, z]) => new THREE.Vector2(x, z))));
      geo.rotateX(Math.PI / 2);
      geo.translate(0, dy, 0);
      return mesh(geo, color, { flat: true });
    };
    const both = (f, color) => { g.add(shape(f(1), color)); g.add(shape(f(-1), color)); };
    both(sg => [[sg * (r - w), 0], [sg * r, 0], [sg * r, L], [sg * (r - w), L]], COL.motor);           // casing
    both(sg => [[sg * mouth, 0], [sg * (r - w), 0], [sg * (r - w), zN], [sg * throat, zN]], COL.clay);   // nozzle
    both(sg => [[sg * throat, zN], [sg * (r - w), zN], [sg * (r - w), zP], [0, zP], [0, zN + 6]], '#7A7A80'); // propellant
    g.add(shape([[-(r - w), zP], [r - w, zP], [r - w, zD], [-(r - w), zD]], '#A9A9AE'));                // delay
    g.add(shape([[-(r - w), zD], [r - w, zD], [r - w, zE], [-(r - w), zE]], COL.night));                // ejection charge
    g.add(shape([[-(r - w), zE], [r - w, zE], [r - w, L], [-(r - w), L]], COL.clay));                   // cap
    return g;
  }

  return {
    // Cover: the M24 rocket, assembled.
    hero: {
      build(root) {
        const k = 'm24';
        for (const p of ['Aft', 'Seg_2', 'Anchor_Seg', 'Nose', 'Motor_Cap']) root.add(part(k, p, { rot: 200 }));
        return { dir: viewDir(-75, 12), up: V(0, 0, 1), W: 420, line: 2.0 };
      },
    },

    // Parts layout (A–F): every printed part pulled apart along the axis.
    layout: {
      build(root) {
        const k = 'm24', I = R[k].info;
        const g = sideways(root);
        const rot = 48, gap = 34;
        const dz = { Aft: 0, Seg_2: gap, Anchor_Seg: 2 * gap, Nose: 3 * gap, Motor_Cap: -gap * 0.9, Rod_Standoff: -gap * 2.2 };
        for (const p of Object.keys(dz)) g.add(part(k, p, { dz: dz[p], rot }));
        const at = (name, f = 0.5, x = -I.body_od / 2) => { const p = P(k, name); return mark(g, x, 0, p.zmin + dz[name] + (p.zmax - p.zmin) * f); };
        const lr = I.lug.center_r, la = deg(I.lug_angle_deg + rot);
        return {
          dir: V(0.28, 1, 0.42), up: V(0, 0, 1), W: 2400, line: 2.4,
          points: {
            A: at('Nose', 0.45), B: at('Anchor_Seg', 0.6), C: at('Seg_2', 0.5), D: at('Aft', 0.62),
            E: at('Motor_Cap', 0.5, -I.thread.r_cap_out),
            F: mark(g, lr * Math.cos(la) - 3, lr * Math.sin(la), -I.lug.standoff_h / 2 + dz.Rod_Standoff),
          },
        };
      },
    },

    // Supplies you add (G–L): shock cord, parachute, wadding, motor, igniter + plug.
    supplies: {
      build(root) {
        const I = R.m18.info;
        const pts = [];
        // G: shock cord, a loose coil
        const coil = [];
        for (let i = 0; i <= 200; i++) {
          const a = i / 200 * Math.PI * 2 * 3.2;
          const rr = 26 + 3 * Math.sin(i / 9);
          coil.push(V(rr * Math.cos(a), rr * Math.sin(a) * 0.55, i * 0.06 + 2 * Math.sin(a * 0.5)));
        }
        root.add(tube(coil, 1.0, COL.cord));
        pts.G = V(-30, 0, 0);
        // H: parachute, open, lines gathered to a loop
        const ch = new THREE.Group();
        ch.add(chuteOpen(V(0, 0, 30), 34, V(0, 0, -30), { gores: 8, depth: 0.3 }));
        const tl = new THREE.TorusGeometry(2.6, 0.6, 10, 30); tl.rotateX(Math.PI / 2); tl.translate(0, 0, -32);
        ch.add(mesh(tl, COL.night, { flat: true }));
        ch.position.set(100, 0, 0);
        root.add(ch);
        pts.H = V(66, 0, 30);
        // I: wadding sheets
        const w = new THREE.Group();
        for (let i = 0; i < 3; i++) {
          const b = new THREE.BoxGeometry(34, 34, 0.6);
          const m = mesh(b, COL.wad);
          m.position.set(i * 5, i * 4, i * 2);
          m.rotation.z = deg(-8 + i * 9);
          w.add(m);
        }
        w.position.set(185, 0, -18);
        root.add(w);
        pts.I = V(170, 0, -18);
        // J: motor, lying down; K: igniter; L: igniter plug
        const mo = motor(I, 0);
        mo.rotation.y = Math.PI / 2;
        mo.position.set(235, 0, -10);
        root.add(mo);
        pts.J = V(270, 0, 0);
        const ig = new THREE.Group();
        ig.add(tube([V(0, 0, 0), V(25, 0, 3), V(55, 0, 0), V(75, 0, 2)], 0.35, COL.red));
        ig.add(tube([V(0, 0, 0.9), V(25, 0, 5), V(55, 0, 4), V(75, 0, 7)], 0.35, COL.night));
        ig.add(ball(V(-0.8, 0, 0.45), 1.1, COL.night));
        ig.position.set(235, 0, 18);
        root.add(ig);
        pts.K = V(290, 0, 22);
        const plug = lathe([[0.6, 0], [4.6, 0], [3.0, 12], [0.6, 12]], COL.orange, {}, 32);
        plug.rotation.y = Math.PI / 2;
        plug.position.set(330, 0, -6);
        root.add(plug);
        pts.L = V(336, 0, -6);
        return { dir: V(0, -1, 0.9), up: V(0, 0, 1), W: 2400, line: 2.4, margin: 4, points: pts };
      },
    },

    // Step: the body joint, dry fit (shoulder slides into the socket).
    joint: {
      build(root) {
        const k = 'm24', I = R[k].info;
        const g = sideways(root);
        const aft = P(k, 'Aft'), seg = P(k, 'Seg_2');
        const gap = 26;
        g.add(part(k, 'Aft', { rot: 48 }));
        g.add(part(k, 'Seg_2', { rot: 48, dz: gap, color: COL.focus }));
        const zj = aft.zmax;
        g.add(arrow(V(-I.body_od / 2 - 9, 0, zj + gap * 0.85), V(-I.body_od / 2 - 9, 0, zj + 3), 1.2));
        return {
          dir: V(0.25, 1, 0.5), up: V(0, 0, 1), W: 1400, line: 2.6, margin: 3,
          focus: focusSide(zj - 55, zj + gap + I.shoulder_len + 40, 40),
          points: {
            shoulder: mark(g, -I.shoulder_od / 2, 0, seg.zmin + gap + I.shoulder_len * 0.5),
            socket: mark(g, -I.body_od / 2, 0, zj - 4),
          },
        };
      },
    },

    // Step: join the body sections with the launch rod through both lugs.
    join: {
      build(root) {
        const k = 'm24', I = R[k].info;
        const g = sideways(root);
        const rot = 0;
        const gap = 30;
        const dz = { Aft: 0, Seg_2: gap, Anchor_Seg: 2 * gap };
        for (const p of Object.keys(dz)) g.add(part(k, p, { dz: dz[p], rot }));
        const la = deg(I.lug_angle_deg + rot), lr = I.lug.center_r;
        const rodTop = P(k, 'Anchor_Seg').zmax + 2 * gap + 10;
        g.add(cyl(I.rod_diameter / 2, -25, rodTop, COL.steel).translateX(lr * Math.cos(la)).translateY(lr * Math.sin(la)));
        const seg = P(k, 'Seg_2'), anc = P(k, 'Anchor_Seg');
        return {
          dir: V(0.15, 1, 0.75), up: V(0, 0, 1), W: 2400, line: 2.4, margin: 4,
          points: {
            rod: mark(g, lr * Math.cos(la), lr * Math.sin(la), rodTop - 12),
            j1: mark(g, -I.body_od / 2, 0, seg.zmin + gap * 0.5 + I.shoulder_len * 0.5),
            j2: mark(g, -I.body_od / 2, 0, anc.zmin + gap * 1.5 + I.shoulder_len * 0.5),
          },
        };
      },
    },

    // Step 4: the shock cord through the anchor strap. The near half of the
    // anchor section is cut away; we look at the bar face-on.
    anchor_cord: {
      build(root) {
        const k = 'm18', I = R[k].info, S = I.strap;
        const clip = cutPlane(root, V(0, 1, 0), 1);
        root.add(part(k, 'Anchor_Seg', { clip }));
        const c = strapRig(I, { top: 26 });
        root.add(c.group);
        return {
          dir: viewDir(-104, 14), up: V(0, 0, 1), W: 1300, line: 2.6, margin: 2,
          focus: focusUp(S.z_bot - 7, S.z_top + 22, 15),
          points: {
            bar: V(S.spring * 0.55, S.front, S.z_top - 1.2), slot: V(0, S.front + S.t + S.hole_depth / 2, S.z_top + 1),
            knot: c.knot, free: V(0, c.yc, S.z_top + 19),
          },
        };
      },
    },

    // Step 5: the other end round the nose's tie bar. The front of the
    // shoulder is cut away; we look up at the bar from the side, below.
    nose_cord: {
      build(root) {
        const k = 'm18', I = R[k].info;
        const nz = I.nose.placement_z;
        root.add(part(k, 'Nose', { clip: cutPlane(root, V(0, -1, 0), 1.3) }));
        const c = noseRig(nz, { down: 40 });
        root.add(c.group);
        return {
          dir: viewDir(68, -20), up: V(0, 0, 1), W: 1300, line: 2.6, margin: 2,
          focus: focusUp(nz - 24, nz + I.nose_shoulder_len + 6, 15),
          points: { bar: V(-4.2, 0, nz + 1), knot: c.knot, body: V(0, c.ys, nz - 21) },
        };
      },
    },

    // Step 6: the parachute's lines girth-hitched round the cord, just under
    // the nose knot: three pictures side by side.
    chute_tie: {
      build(root) {
        const k = 'm18', I = R[k].info;
        const nz = I.nose.placement_z;
        const pts = {};
        const states = ['loop', 'through', 'snug'];
        states.forEach((st, i) => {
          const g = new THREE.Group();
          // Side by side along the screen's horizontal (seen from +y, +x runs to the left).
          g.position.set(-i * 40 * Math.sin(deg(62)), i * 40 * Math.cos(deg(62)), 0);
          root.add(g);
          g.updateMatrixWorld(true);
          g.add(part(k, 'Nose', { clip: cutPlane(g, V(0, -1, 0), 1.3) }));
          const c = noseRig(nz, { down: 46 });
          g.add(c.group);
          const z0 = c.below - 1.4;
          // The hitch is drawn mirrored (scale x -1) so the parachute's side is on the right.
          const mg = new THREE.Group();
          mg.scale.x = -1;
          g.add(mg);
          mg.updateMatrixWorld(true);
          const far = st === 'through' ? V(-13, c.ys + cordR + 16, z0 - 25) : V(15, c.ys + 2, z0 - 36);
          const h = larks(0, c.ys, z0, st, far);
          mg.add(h.group);
          if (st === 'through') {
            // The parachute (bundled up) being pulled away through the loop.
            const rg = new THREE.Group();
            rg.add(chuteRolled(0, 13, 3.0, { wrap: false }));
            rg.quaternion.setFromUnitVectors(V(0, 0, 1), V(-0.45, 0.35, -0.82).normalize());
            rg.position.copy(far);
            mg.add(rg);
            mg.add(curvedArrow([far.clone().add(V(-4.5, 1, 4)), far.clone().add(V(-7.5, 2, -3)), far.clone().add(V(-8, 2.5, -9))], 0.6));
          }
          mg.updateMatrixWorld(true);
          const at = p => p.clone().applyMatrix4(mg.matrixWorld);
          pts[`n${i + 1}`] = V(9, 0, nz + 6).applyMatrix4(g.matrixWorld);
          if (h.points.loop) pts[`loop${i + 1}`] = at(h.points.loop);
          if (h.points.hitch) pts.hitch = at(h.points.hitch);
          pts[`knot${i + 1}`] = c.knot.clone().applyMatrix4(g.matrixWorld);
          if (st === 'snug') pts.lines = at(V(9, c.ys + 1, z0 - 16));
          if (st === 'through') pts.chute = at(far.clone().add(V(1, 0, -4)));
        });
        return {
          dir: viewDir(62, -14), up: V(0, 0, 1), W: 2400, line: 2.6, margin: 2,
          focus: new THREE.Box3(V(-80 - 18, -16, nz - 44), V(18, 80, nz + I.nose_shoulder_len + 2)),
          points: pts,
        };
      },
    },

    // Overview: how it all hangs under the parachute. Nose on top, the lines
    // girth-hitched to the cord just under the nose, the cord (shortened, with
    // a break mark) down to the strap in the top of the body. The nose and the
    // anchor section are cut open to show the tie bar and the strap.
    recovery: {
      build(root) {
        const k = 'm18', I = R[k].info, S = I.strap;
        const lift = 92;
        root.add(part(k, 'Anchor_Seg', { clip: cutPlane(root, V(0, 1, 0), 1) }));
        root.add(part(k, 'Aft', { rot: 30 }));
        root.add(part(k, 'Nose', { dz: lift, clip: cutPlane(root, V(0, 1, 0), 1.3) }));
        const nz = I.nose.placement_z + lift;
        const sr = strapRig(I, { top: 9 });
        root.add(sr.group);
        const nr = noseRig(nz, { down: 30 });
        root.add(nr.group);
        // The cord between them, broken in the middle.
        const a = sr.top, b = nr.bottom;
        const mid = a.clone().lerp(b, 0.5).add(V(-5, 0, 0));
        const dir = b.clone().sub(a).normalize();
        const gap = 7;
        root.add(rope([a, a.clone().add(V(-1, 0, 10)), mid.clone().addScaledVector(dir, -gap / 2)], cordR, { ends: [false, true] }));
        root.add(rope([mid.clone().addScaledVector(dir, gap / 2), b.clone().add(V(-1.5, 0, -10)), b], cordR, { ends: [true, false] }));
        root.add(breakMark(mid, dir, { len: 13, gap: gap + 3, t: 1.6 }));
        // The parachute: canopy above, its lines down round the nose to the hitch.
        const z0 = nr.below - 1.4;
        const conf = V(nr.x + 4, nr.ys, z0 - 2);
        const h = larks(nr.x, nr.ys, z0, 'snug', conf.clone());
        root.add(h.group);
        const rc = 96, apex = nz + 178;
        root.add(chuteOpen(V(0, 0, apex), rc, conf, { gores: 8, depth: 0.32 }));
        return {
          dir: viewDir(-90, 6), up: V(0, 0, 1), W: 1100, line: 2.2, margin: 3,
          focus: new THREE.Box3(V(-rc - 2, -rc - 2, 112), V(rc + 2, rc + 2, apex + 4)),
          points: {
            nose: V(-I.body_od / 2, 0, nz + 32), body: V(-I.body_od / 2, 0, S.z_bot - 6),
            chute: V(-rc * 0.55, 0, apex - 12), cord: mid.clone().add(V(0, 0, -14)), lines: V(-38, 0, nz + 80), brk: mid,
            tiebar: V(-3, 0, nz + 1), strap: V(-S.spring * 0.4, S.front, S.z_top - 1.5), hitch: V(nr.x, nr.ys, z0),
          },
        };
      },
    },

    // Step 7: folding the parachute, four pictures: flat (fold line), half
    // (fold line), thin wedge with the lines laid back along it (side fold
    // lines), rolled next to the anchor section B for size.
    chute_fold: {
      build(root) {
        const pts = {};
        const Rr = 34, conv = 78;   // canopy radius, where the lines meet
        const off = Math.PI / 8;    // gores turned half a gore: the fold lines run down gore middles, not seams
        const gore = (cx, a0, a1, color, sc = 1) => {
          const sh = new THREE.Shape([new THREE.Vector2(0, 0), new THREE.Vector2(sc * Rr * Math.cos(a0), sc * Rr * Math.sin(a0)),
                                      new THREE.Vector2(sc * Rr * Math.cos(a1), sc * Rr * Math.sin(a1))]);
          const g = new THREE.ShapeGeometry(sh);
          g.translate(cx, 0, 0);
          return mesh(g, color, { flat: true });
        };
        const strings = (cx, rim, to) => rim.map(p => line([V(cx + p.x, p.y, -1.2), V(cx + to.x, to.y, -1.2)]));
        const A8 = i => i / 8 * Math.PI * 2 + off;
        const rimPt = (i, sc = 1) => V(sc * Rr * Math.cos(A8(i)), sc * Rr * Math.sin(A8(i)), 0);
        const fold = (a, b) => root.add(dashed([[a, b]], { normal: V(0, 0, 1) }));
        // 1. flat, lines straight and even; fold line: the vertical diameter
        for (let i = 0; i < 8; i++) root.add(gore(0, A8(i), A8(i + 1), i % 2 ? COL.chuteA : COL.chuteB));
        for (const s of strings(0, [0, 1, 2, 3, 4, 5, 6, 7].map(i => rimPt(i)), V(conv, 0, 0))) root.add(s);
        fold(V(0, -Rr - 6, 0.8), V(0, Rr + 6, 0.8));
        root.add(curvedArrow([V(-22, Rr + 3, 1), V(-8, Rr + 12, 1), V(8, Rr + 12, 1), V(20, Rr + 4, 1)], 1.1));
        pts.f1 = V(-Rr * 0.72, -Rr * 0.72, 0);
        // 2. in half (the right half, two layers); fold line: the horizontal radius
        const x2 = 128;
        for (let i = 6; i < 9; i++) root.add(gore(x2, A8(i), A8(i + 1), i % 2 ? COL.chuteA : COL.chuteB));
        for (const sg of [-1, 1]) {  // the half gores at the fold: their corner is on the octagon's edge
          const c = Rr * Math.cos(off), v = rimPt(sg < 0 ? 6 : 9);
          const hg = new THREE.ShapeGeometry(new THREE.Shape(sg < 0
            ? [new THREE.Vector2(0, 0), new THREE.Vector2(0, -c), new THREE.Vector2(v.x, v.y)]
            : [new THREE.Vector2(0, 0), new THREE.Vector2(v.x, v.y), new THREE.Vector2(0, c)]));
          hg.translate(x2, 0, 0);
          root.add(mesh(hg, COL.chuteA, { flat: true }));
        }
        for (const s of strings(x2, [6, 7, 8, 9].map(i => rimPt(i)), V(conv, 0, 0))) root.add(s);
        fold(V(x2 - 6, 0, 0.8), V(x2 + Rr + 4, 0, 0.8));
        root.add(curvedArrow([V(x2 - 5, Rr - 6, 1), V(x2 - 14, 12, 1), V(x2 - 14, -12, 1), V(x2 - 6, -Rr + 7, 1)], 1.1));
        pts.f2 = V(x2 + Rr * 0.3, -Rr * 0.98, 0);
        // Second row: pictures 3 and 4 under 1 and 2.
        const dy2 = -88;
        const row2 = new THREE.Group();
        row2.position.y = dy2;
        root.add(row2);
        row2.updateMatrixWorld(true);
        // 3. a thin wedge (drawn bigger), the lines laid back along its middle; fold lines: its thirds
        const x3 = 4, ha = Math.PI / 9, Lw = 54, wy = Lw * Math.sin(ha);
        const wedge = new THREE.Shape([new THREE.Vector2(0, 0), new THREE.Vector2(Lw * Math.cos(ha), -wy),
                                       new THREE.Vector2(Lw, 0), new THREE.Vector2(Lw * Math.cos(ha), wy)]);
        const wg = new THREE.ShapeGeometry(wedge); wg.translate(x3, 0, 0);
        row2.add(mesh(wg, COL.chuteA, { flat: true }));
        const ex = x3 + Lw;
        row2.add(line([V(x3 + 10, 0.6, 1.0), V(ex - 6, 0.6, 1.0), V(ex + 6, 0.6, 1.0), V(ex + 10.5, -1.6, 1.0), V(ex + 6, -3.8, 1.0), V(ex - 1, -3.8, 0.4)]));
        row2.add(dashed([[V(x3 + 5, 1.7, 0.8), V(ex - 1, wy / 3 + 0.4, 0.8)], [V(x3 + 5, -1.7, 0.8), V(ex - 1, -wy / 3 - 0.4, 0.8)]],
                        { normal: V(0, 0, 1) }));
        const ax = x3 + Lw * 0.62;
        row2.add(curvedArrow([V(ax - 3, wy + 9, 1), V(ax + 2, wy + 6, 1), V(ax + 3, wy * 0.45, 1)], 0.9));
        row2.add(curvedArrow([V(ax - 3, -wy - 9, 1), V(ax + 2, -wy - 6, 1), V(ax + 3, -wy * 0.45, 1)], 0.9));
        pts.f3 = V(x3 + 8, -wy - 4 + dy2, 0);
        // 4. rolled, lines wrapped, beside B (anchor section, cut open) for size: real scale
        const x4 = 120;
        const I = R.m18.info, ri = I.body_id / 2;
        const rollLen = 46, rollR = ri * 0.74;
        const roll = chuteRolled(0, rollLen, rollR);
        roll.rotation.y = Math.PI / 2;
        roll.position.set(x4, 0, 0);
        row2.add(roll);
        const tubeG = new THREE.Group();
        tubeG.rotation.y = Math.PI / 2;
        row2.add(tubeG);
        const anc = P('m18', 'Anchor_Seg');
        tubeG.position.set(x4 + rollLen + 26 - anc.zmin, 0, 0);
        tubeG.updateMatrixWorld(true);
        tubeG.add(part('m18', 'Anchor_Seg', { clip: [new THREE.Plane(V(0, 0, -1), 0)] }));
        row2.add(arrow(V(x4 + rollLen + 4, 0, 4), V(x4 + rollLen + 22, 0, 4), 1.0));
        pts.f4 = V(x4 + 6, -rollR + dy2, 0);
        pts.B = V(x4 + rollLen + 26 + (anc.zmax - anc.zmin) * 0.55, -I.body_od / 2 + dy2, 0);
        return { dir: V(0, 0, 1), up: V(0, 1, 0), W: 2400, line: 3.0, margin: 4, points: pts };
      },
    },

    // Packing: wadding on top of the motor, then the parachute, then the cord; nose on.
    pack: {
      build(root) {
        const k = 'm18', I = R[k].info;
        const g = sideways(root);
        const clip = cutPlane(g);
        g.add(part(k, 'Aft', { clip }));
        g.add(part(k, 'Anchor_Seg', { clip }));
        const lift = 34;
        g.add(part(k, 'Nose', { dz: lift, clip }));
        g.add(part(k, 'Motor_Cap', { clip }));
        g.add(motor(I, I.thread.z_face));
        const top = I.bay_len + 3;
        const ri = I.body_id / 2 - 0.6;
        g.add(wadding(V(0, 0, top + 6), ri * 1.8, 3, 7));
        const rollZ = top + 22, rollL = 62;
        g.add(chuteRolled(rollZ, rollL, ri - 0.4));
        // Cord: tied at the strap, folded zig-zag down into the body on top of
        // the parachute, then back up to the nose.
        const S = I.strap;
        const sr = strapRig(I, { top: 4 });
        g.add(sr.group);
        const nz = I.nose.placement_z + lift;
        const nr = noseRig(nz, { down: 22 });
        g.add(nr.group);
        const z0 = rollZ + rollL + 3;
        const zz = [sr.top, V(-2, -2, S.z_top + 2), V(-3, -5, S.z_bot - 4)];
        for (let i = 0; i < 7; i++) zz.push(V(0, i % 2 ? ri - 2.2 : -ri + 2.2, S.z_bot - 10 - i * ((S.z_bot - 10 - z0) / 6)));
        zz.push(V(0, -ri + 3, z0 + 6), V(-3, -6, S.z_bot), V(-3, -6, S.z_top + 4), nr.bottom);
        g.add(rope(zz, cordR, { ends: [false, false] }));
        // The parachute's lines, from the roll up to their hitch under the nose.
        const zh = nr.below - 1.4;
        const h = larks(nr.x, nr.ys, zh, 'snug', V(2, 2, rollZ + rollL + 1));
        g.add(h.group);
        g.add(arrow(V(0, I.body_od / 2 + 9, I.nose.placement_z + lift + 18), V(0, I.body_od / 2 + 9, I.nose.placement_z + 4), 1.1));
        return {
          dir: V(0, 0.3, 1), up: V(0, -1, 0), W: 2400, line: 2.4, margin: 3,
          focus: focusSide(-14, I.nose.tip_z + lift + 2, 30),
          points: {
            motor: V(25, 0, 0).applyMatrix4(g.matrixWorld), wad: V(top + 8, 0, 0),
            chute: V(rollZ + rollL * 0.45, 0, 0), cord: V(z0 + 20, 0, 0), nose: V(I.nose.placement_z + lift + 30, 0, 0),
            strap: V(S.z_top - 3, 0, 0),
          },
        };
      },
    },

    // Motor: slide it into the tail (section), then screw the cap on.
    motor_in: {
      build(root) {
        const k = 'm18', I = R[k].info;
        const g = sideways(root);
        const clip = cutPlane(g);
        g.add(part(k, 'Aft', { clip, rot: 0 }));
        const drop = I.mtr_len + 18;
        g.add(motor(I, I.thread.z_face - drop));
        g.add(part(k, 'Motor_Cap', { dz: -drop - 30, color: COL.focus }));
        g.add(arrow(V(0, I.body_od / 2 + 9, -drop + I.mtr_len * 0.15), V(0, I.body_od / 2 + 9, -6), 1.1));
        return {
          dir: V(0, 0.3, 1), up: V(0, -1, 0), W: 2400, line: 2.4, margin: 3,
          focus: focusSide(I.thread.z_face - drop - 45, I.bay_len + 16, 30),
          points: {
            stop: V(I.bay_len + 1.5, 0, 0), bay: V(I.bay_len * 0.5, 0, 0),
            motor: V(I.thread.z_face - drop + I.mtr_len * 0.5, 0, 0),
            cap: V(I.thread.z_face - drop - 34, 0, 0), thread: V(-6, 0, 0),
          },
        };
      },
    },

    // Cap on: screw it onto the tail's thread, finger tight.
    cap_on: {
      build(root) {
        const k = 'm18', I = R[k].info;
        root.add(part(k, 'Aft', { rot: 0 }));
        root.add(part(k, 'Motor_Cap', { dz: -9, color: COL.focus }));
        root.add(turnArrow(I.thread.r_cap_out + 7, -12, -150, -30, 0.9));
        return {
          dir: viewDir(-90, -22), up: V(0, 0, 1), W: 1100, line: 2.6, margin: 3,
          focus: focusUp(-26, 32, 40),
          points: { cap: V(0, -I.thread.r_cap_out, -14) },
        };
      },
    },

    // Igniter: the motor alone, cut in half: tip all the way up against the
    // propellant, plug pushed in, leads bent apart.
    igniter: {
      build(root) {
        const I = R.m18.info;
        root.add(motorCut(I));
        root.add(igniter(I, 0, { leadLen: 40, spread: 1.0 }));
        const r = I.mtr_d / 2;
        return {
          dir: viewDir(-90, 14), up: V(0, 0, 1), W: 1000, line: 2.6, margin: 3,
          focus: focusUp(-48, 72, 40),
          points: { tip: V(0, 0, r * 0.9 + 6.6), plug: V(-3, 0, -3), leads: V(-20, 0, -40), nozzle: V(-r * 0.7, 0, r * 0.45), prop: V(r * 0.5, 0, I.mtr_len * 0.4),
                    delay: V(r * 0.5, 0, I.mtr_len * 0.7), charge: V(r * 0.5, 0, I.mtr_len * 0.86) },
        };
      },
    },

    // On the pad: standoff on the rod, rocket's aft lug resting on it.
    pad: {
      build(root) {
        const k = 'm18', I = R[k].info;
        const rot = 0;
        const la = deg(I.lug_angle_deg + rot), lr = I.lug.center_r;
        const rx = lr * Math.cos(la), ry = lr * Math.sin(la);
        const base = -I.lug.standoff_h;
        for (const p of ['Aft', 'Motor_Cap', 'Anchor_Seg', 'Nose']) root.add(part(k, p, { rot }));
        root.add(part(k, 'Rod_Standoff', { rot, color: COL.focus }));
        root.add(cyl(I.rod_diameter / 2, base - 4, 360, COL.steel).translateX(rx).translateY(ry));
        const plate = new THREE.BoxGeometry(110, 110, 2);
        plate.translate(rx, ry, base - 1);
        root.add(mesh(plate, COL.deflector));
        root.add(igniter(I, I.thread.z_face, { leadLen: 18, spread: 1.6, plug: true }));
        return {
          dir: viewDir(-25, 16), up: V(0, 0, 1), W: 1100, line: 2.4, margin: 3,
          focus: focusUp(base - 3, 70, 60),
          points: { standoff: V(rx, ry, base / 2), lug: V(rx, ry, 4), rod: V(rx, ry, 64), deflector: V(rx + 40, ry - 40, base) },
        };
      },
    },
  };
}
