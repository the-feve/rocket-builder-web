// The guide's drawings. Each scene's build(root) adds objects to root (rocket
// coordinates: mm, z up the rocket axis, z = 0 at the tail) and returns the
// view: dir (from the subject toward the camera), up, W (final pixel width),
// line (outline width in px), margin (mm), focus (a world Box3: only what is
// inside it is framed; the rest runs off the edge) and points (labels).
//
// Not to scale: the parachute, cord and wadding are drawn small so they fit.
export function defineScenes(h) {
  const { THREE, V, COL, R, part, cyl, lathe, tube, ball, knot, arrow, turnArrow, motor, igniter,
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
  const cordR = 0.8;  // about 1.5 mm cord (Kevlar or braided)

  // The cord threaded through the anchor strap: down behind the bar, under
  // it, up in front, and tied back onto itself above the bar. Returns the
  // tube(s) and the point where the long end leaves the knot.
  function strapCord(I, { up = 14 } = {}) {
    const S = I.strap;
    const yb = S.front + S.t + S.hole_depth / 2;  // in the slot behind the bar
    const yf = S.front - 1.6;                       // in front of the bar
    const apex = S.z_bot + S.spring;                 // the bar's underside at its middle
    const zt = S.z_top;
    const g = new THREE.Group();
    const kp = V(0.6, yb - 1.2, zt + 4.5);
    g.add(tube([V(1.2, yb, zt + up), V(1.2, yb, zt + 6), V(1.2, yb, zt), V(1.0, yb, apex - 1.2), V(0, (yb + yf) / 2, apex - 3.4),
                V(-1.6, yf, apex - 1.2), V(-1.8, yf, zt + 0.5), kp.clone().add(V(-0.6, -0.6, -0.8))], cordR, COL.cord));
    g.add(tube([kp.clone().add(V(-0.4, 0.4, 0.6)), V(-2.5, yb - 3.2, zt + 8.5), V(-4, yb - 4.6, zt + 10)], cordR, COL.cord));
    g.add(knot(kp, 1.25, COL.cord, V(0, 1, 0.6)));
    return { group: g, top: V(1.2, yb, zt + up), knot: kp };
  }
  // The cord tied round the nose's tie bar (bar along x at the bottom of the
  // shoulder, z = nz .. nz + 2): up one side, over, down, knotted below.
  function noseCord(nz, from) {
    const g = new THREE.Group();
    const kp = V(0, 0.3, nz - 5);
    g.add(tube([from, V(0, 2.6, nz - 9), V(0, 2.4, nz), V(0, 1.4, nz + 3.0), V(0, -1.4, nz + 3.0), V(0, -2.4, nz),
                V(0, -1.4, nz - 4), kp.clone().add(V(0, -0.6, 0.2))], cordR, COL.cord));
    g.add(knot(kp, 1.2, COL.cord, V(1, 0, 0.3)));
    g.add(tube([kp.clone().add(V(0, 0.8, -0.6)), V(0, -1.0, nz - 9), V(0, -2.5, nz - 11)], cordR, COL.cord));
    return g;
  }
  // A small loop knot in the cord (for the parachute), at p.
  function loopKnot(p, r = 3) {
    const g = new THREE.Group();
    const tg = new THREE.TorusGeometry(r, cordR, 12, 48);
    tg.rotateY(Math.PI / 2);
    tg.translate(p.x, p.y + r * 0.2, p.z - r - 1.2);
    g.add(mesh(tg, COL.cord));
    g.add(knot(p, 1.25, COL.cord, V(0, 1, 0)));
    return g;
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

    // Step: the shock cord through the anchor strap. The near half of the
    // anchor section is cut away; we look at the bar face-on.
    anchor_cord: {
      build(root) {
        const k = 'm18', I = R[k].info, S = I.strap;
        const clip = cutPlane(root, V(0, 1, 0), 1);
        root.add(part(k, 'Anchor_Seg', { clip }));
        const c = strapCord(I, { up: 20 });
        root.add(c.group);
        return {
          dir: viewDir(-100, 16), up: V(0, 0, 1), W: 1300, line: 2.6, margin: 2,
          focus: focusUp(S.z_bot - 8, S.z_top + 21, 16),
          points: {
            bar: V(S.spring * 0.55, S.front, S.z_top - 1.2), slot: V(0, S.front + S.t + S.hole_depth / 2, S.z_top + 1),
            knot: c.knot, free: c.top,
          },
        };
      },
    },

    // Step: the other end of the cord round the nose's tie bar (section view, from below).
    nose_cord: {
      build(root) {
        const k = 'm18', I = R[k].info;
        const nz = I.nose.placement_z;
        const clip = cutPlane(root);
        root.add(part(k, 'Nose', { clip, color: COL.part }));
        root.add(noseCord(nz, V(0, 3, nz - 30)));
        return {
          dir: viewDir(200, -18), up: V(0, 0, 1), W: 1300, line: 2.6, margin: 2,
          focus: focusUp(nz - 13, nz + I.nose_shoulder_len + 8, 16),
          points: { bar: V(0, 0, nz + 1), knot: V(0, 0.3, nz - 5) },
        };
      },
    },

    // Overview: how the recovery system hangs together (anchor section cut open, nose pulled up).
    recovery: {
      build(root) {
        const k = 'm18', I = R[k].info, S = I.strap;
        const lift = 70;
        const clip = cutPlane(root);
        const anc = P(k, 'Anchor_Seg');
        root.add(part(k, 'Anchor_Seg', { clip }));
        root.add(part(k, 'Aft', { clip }));
        root.add(part(k, 'Nose', { dz: lift, clip }));
        const nz = I.nose.placement_z + lift;
        const c = strapCord(I, { up: 8 });
        root.add(c.group);
        const loopAt = V(0, 4, nz - 38);
        root.add(tube([c.top, V(0, c.top.y + 2, c.top.z + 18), V(0, 9, c.top.z + 40), loopAt.clone().add(V(0, 0, -6)), loopAt], cordR, COL.cord));
        root.add(tube([loopAt, V(0, 2, nz - 22)], cordR, COL.cord));
        root.add(noseCord(nz, V(0, 2, nz - 22)));
        root.add(loopKnot(loopAt));
        const conf = loopAt.clone().add(V(0, 1, -5));
        root.add(chuteOpen(V(0, 46, nz - 6), 22, conf, { gores: 8, depth: 0.3 }));
        return {
          dir: viewDir(180, 8), up: V(0, 0, 1), W: 1100, line: 2.4, margin: 4,
          focus: new THREE.Box3(V(-40, -30, S.z_bot - 20), V(40, 100, nz + 90)),
          points: { strap: V(0, S.front + 1, S.z_top), loop: loopAt, nose: V(0, -I.body_od / 2, nz + 30),
                    chute: V(0, 46, nz - 4), cord: V(0, 9, c.top.z + 40) },
        };
      },
    },

    // Folding the parachute: flat, folded to a wedge, rolled.
    chute_fold: {
      build(root) {
        const pts = {};
        // 1. flat, lines pulled straight together
        const flat = new THREE.Group();
        for (let i = 0; i < 8; i++) {
          const a0 = i / 8 * Math.PI * 2, a1 = (i + 1) / 8 * Math.PI * 2;
          const sh = new THREE.Shape([new THREE.Vector2(0, 0), new THREE.Vector2(34 * Math.cos(a0), 34 * Math.sin(a0)), new THREE.Vector2(34 * Math.cos(a1), 34 * Math.sin(a1))]);
          flat.add(mesh(new THREE.ShapeGeometry(sh), i % 2 ? COL.chuteA : COL.chuteB, { flat: true }));
        }
        for (let i = 0; i < 8; i++) {
          const a = i / 8 * Math.PI * 2;
          flat.add(tube([V(34 * Math.cos(a), 34 * Math.sin(a), -0.4), V(70, 0, -0.4)], 0.3, COL.night, { outline: false }));
        }
        root.add(flat);
        pts.f1 = V(0, 36, 0);
        // 2. folded in half, then in half again: a long wedge
        const wedge = new THREE.Shape([new THREE.Vector2(0, -3), new THREE.Vector2(34, -13), new THREE.Vector2(34, 13), new THREE.Vector2(0, 3)]);
        const wg = new THREE.ExtrudeGeometry(wedge, { depth: 3, bevelEnabled: false });
        const wm = mesh(wg, COL.chuteA, { flat: true });
        wm.position.set(110, 0, 0);
        root.add(wm);
        root.add(tube([V(144, 0, 1.5), V(185, 0, 1.5)], 0.3, COL.night, { outline: false }));
        root.add(tube([V(144, 5, 1.5), V(185, 0, 1.5)], 0.3, COL.night, { outline: false }));
        root.add(tube([V(144, -5, 1.5), V(185, 0, 1.5)], 0.3, COL.night, { outline: false }));
        pts.f2 = V(110, 14, 3);
        // 3. rolled up, lines wrapped round
        const roll = chuteRolled(0, 34, 6);
        roll.rotation.y = Math.PI / 2;
        roll.position.set(215, 0, 0);
        root.add(roll);
        pts.f3 = V(215, 8, 0);
        root.add(arrow(V(62, 22, 0), V(88, 22, 0), 1.1));
        root.add(arrow(V(170, 22, 0), V(196, 22, 0), 1.1));
        return { dir: V(0, -0.4, 1), up: V(0, 1, 0), W: 2000, line: 2.4, margin: 4, points: pts };
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
        const roll = chuteRolled(top + 22, 62, ri - 0.4);
        g.add(roll);
        // Cord: zig-zag on top of the chute, to the strap and up to the nose.
        const S = I.strap;
        const c = strapCord(I, { up: 4 });
        g.add(c.group);
        const z0 = top + 22 + 62 + 2, nz = I.nose.placement_z + lift;
        const zz = [V(0, -3, z0)];
        for (let i = 0; i < 7; i++) zz.push(V(0, i % 2 ? -ri + 2 : ri - 2, z0 + 4 + i * 6));
        zz.push(V(0, -4, S.z_bot - 2), V(0, -4, S.z_top + 4), V(0, 0, nz - 12));
        g.add(tube(zz, cordR, COL.cord));
        g.add(tube([V(0, -3, z0), V(0, 0, top + 22 + 62)], cordR, COL.cord));  // to the chute's lines
        g.add(noseCord(nz, V(0, 0, nz - 12)));
        g.add(arrow(V(0, I.body_od / 2 + 9, I.nose.placement_z + lift + 18), V(0, I.body_od / 2 + 9, I.nose.placement_z + 4), 1.1));
        return {
          dir: V(0, 0.3, 1), up: V(0, -1, 0), W: 2400, line: 2.4, margin: 3,
          focus: focusSide(-14, I.nose.tip_z + lift + 2, 30),
          points: {
            motor: V(25, 0, 0).applyMatrix4(g.matrixWorld), wad: V(top + 8, 0, 0),
            chute: V(top + 50, 0, 0), cord: V(z0 + 20, 0, 0), nose: V(I.nose.placement_z + lift + 30, 0, 0),
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
