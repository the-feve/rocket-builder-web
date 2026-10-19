// Assembly-guide drawings: the rockets rocketgen built (tools/.build/*.glb),
// plus simple added geometry for the things that aren't printed (shock cord,
// parachute, wadding, motor, igniter, launch rod), rendered as clean line
// art: flat brand-colour fills with outlines found from normal, depth and
// object-id edges. render.mjs drives this page; each scene returns a PNG and
// the image positions of its labelled points.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { toCreasedNormals, mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

THREE.ColorManagement.enabled = false;  // brand hex values straight through, no linear conversion
const V = (x, y, z) => new THREE.Vector3(x, y, z);
const COL = {
  night: '#12203A', paper: '#F6F1E7', orange: '#F2652B', sky: '#3D8BFD', red: '#E5484D', green: '#2FB67C', grey: '#6E6E73',
  part: '#FFFDF8', focus: '#FDE6DA', focus2: '#DDEAFF', cut: '#D9DFEA', motor: '#EDE6D8', clay: '#CFC3AB',
  chuteA: '#F2652B', chuteB: '#F8A27E', wad: '#FBEFD6', steel: '#A9B4C8', deflector: '#EEF1F6', cord: '#3A4E74',
};

// ---------- data ----------
const R = {};  // key -> { info, geo: {partName: BufferGeometry} }
async function loadRocket(key) {
  const info = await (await fetch(`.build/${key}.json`)).json();
  const gltf = await new GLTFLoader().loadAsync(`.build/${key}.glb`);
  const geo = {};
  gltf.scene.updateMatrixWorld(true);
  gltf.scene.traverse(o => {
    if (!o.isMesh) return;
    let g = o.geometry.clone();
    g.applyMatrix4(o.matrixWorld);
    g.deleteAttribute('normal');
    g = toCreasedNormals(g, THREE.MathUtils.degToRad(30));
    const name = o.name || o.parent?.name;
    geo[name] = g;
  });
  R[key] = { info, geo };
}
// Fillet tangent edges from build_meshes.py: {part: [[[x,y,z,nx,ny,nz], ...], ...]}.
const edgesOf = (key, name) => (R[key].info.fillet_edges?.[name] || []).map(line => ({
  pts: line.map(q => V(q[0], q[1], q[2])), nrm: line.map(q => V(q[3], q[4], q[5])) }));

// ---------- materials ----------
// Two materials per mesh: the colour pass and the normal/depth pass, sharing
// the clipping planes. Back faces (seen through a section cut) are drawn as
// the cut face: flat COL.cut, with a normal no front face can have.
const FAR = 5000;
const clipVS = `#include <clipping_planes_pars_vertex>`;
function colorMat(color, clip = [], opts = {}) {
  return new THREE.ShaderMaterial({
    uniforms: { uColor: { value: new THREE.Color(color) }, uCut: { value: new THREE.Color(opts.cut || COL.cut) },
                uFlat: { value: opts.flat ? 1 : 0 } },
    vertexShader: `${clipVS}
      varying vec3 vN;
      void main() {
        #include <begin_vertex>
        #include <project_vertex>
        #include <clipping_planes_vertex>
        vN = normalize(normalMatrix * normal);
      }`,
    fragmentShader: `#include <clipping_planes_pars_fragment>
      uniform vec3 uColor; uniform vec3 uCut; uniform float uFlat;
      varying vec3 vN;
      void main() {
        #include <clipping_planes_fragment>
        if (!gl_FrontFacing) { gl_FragColor = vec4(uCut, 1.0); return; }
        vec3 L = normalize(vec3(-0.45, 0.65, 0.62));
        float k = 1.0;  // flat fills, no shading (brand.md, Illustration style)
        gl_FragColor = vec4(uColor * k, 1.0);
      }`,
    side: THREE.DoubleSide, clipping: clip.length > 0, clippingPlanes: clip,
  });
}
// Shock cord: flat cord colour with a braid (two darker helices, crossing),
// so it reads as cord rather than as a pipe. Uses the tube's uv (u along,
// v round); uTurns = how many braid repeats along the whole tube.
function ropeMat(color, turns, clip = []) {
  return new THREE.ShaderMaterial({
    uniforms: { uColor: { value: new THREE.Color(color) }, uDark: { value: new THREE.Color(color).multiplyScalar(0.8) },
                uCut: { value: new THREE.Color(COL.cut) }, uTurns: { value: turns } },
    vertexShader: `${clipVS}
      varying vec2 vUv;
      void main() {
        vUv = uv;
        #include <begin_vertex>
        #include <project_vertex>
        #include <clipping_planes_vertex>
      }`,
    fragmentShader: `#include <clipping_planes_pars_fragment>
      uniform vec3 uColor, uDark, uCut; uniform float uTurns;
      varying vec2 vUv;
      void main() {
        #include <clipping_planes_fragment>
        if (!gl_FrontFacing) { gl_FragColor = vec4(uCut, 1.0); return; }
        float a = fract(vUv.x * uTurns + vUv.y * 2.0), b = fract(vUv.x * uTurns - vUv.y * 2.0 + 0.5);
        float k = (a < 0.12 || b < 0.12) ? 1.0 : 0.0;
        gl_FragColor = vec4(mix(uColor, uDark, k), 1.0);
      }`,
    side: THREE.DoubleSide, clipping: clip.length > 0, clippingPlanes: clip,
  });
}
function ndMat(id, clip = []) {
  return new THREE.ShaderMaterial({
    uniforms: { uId: { value: id } },
    vertexShader: `${clipVS}
      varying vec3 vN; varying float vD;
      void main() {
        #include <begin_vertex>
        #include <project_vertex>
        #include <clipping_planes_vertex>
        vN = normalize(normalMatrix * normal);
        vD = -mvPosition.z;
      }`,
    fragmentShader: `#include <clipping_planes_pars_fragment>
      uniform float uId; varying vec3 vN; varying float vD;
      void main() {
        #include <clipping_planes_fragment>
        vec3 n = gl_FrontFacing ? normalize(vN) : vec3(0.0, 0.0, -1.0);
        gl_FragColor = vec4(n * 0.5 + 0.5, vD / ${FAR.toFixed(1)});
      }`,
    side: THREE.DoubleSide, clipping: clip.length > 0, clippingPlanes: clip,
  });
}
function idMat(id, clip = []) {
  return new THREE.ShaderMaterial({
    uniforms: { uId: { value: id } },
    vertexShader: `${clipVS}
      void main() {
        #include <begin_vertex>
        #include <project_vertex>
        #include <clipping_planes_vertex>
      }`,
    fragmentShader: `#include <clipping_planes_pars_fragment>
      uniform float uId;
      void main() {
        #include <clipping_planes_fragment>
        gl_FragColor = vec4(fract(uId / 256.0), floor(uId / 256.0) / 256.0, gl_FrontFacing ? 0.0 : 1.0, 1.0);
      }`,
    side: THREE.DoubleSide, clipping: clip.length > 0, clippingPlanes: clip,
  });
}

// ---------- scene-building helpers ----------
let nextId = 1;
function mesh(geometry, color, { clip = [], flat = false, outline = true, cut, rope } = {}) {
  const m = new THREE.Mesh(geometry, null);
  const id = outline ? nextId++ : 0;
  m.userData = { color: rope ? ropeMat(color, rope, clip) : colorMat(color, clip, { flat, cut }), nd: ndMat(id, clip), id: idMat(id, clip) };
  return m;
}
// A printed part of rocket `key`, moved up by dz and turned by rot (degrees) about the axis.
function part(key, name, { dz = 0, rot = 0, color = COL.part, clip = [], cut } = {}) {
  const g = R[key].geo[name];
  if (!g) throw new Error(`${key} has no part ${name}`);
  const m = mesh(g, color, { clip, cut });
  m.position.z = dz;
  m.rotation.z = THREE.MathUtils.degToRad(rot);
  m.userData.part = name;
  m.userData.dashPolys = edgesOf(key, name);  // fillet tangent edges, drawn dashed
  return m;
}
// Dashed lines (fold lines, hidden outlines...): polylines in the parent's
// coordinates; drawn by render() like the fillet edges. normal: the side to
// lift them toward (default: toward the camera).
function dashed(polys, { clip = [], normal = null, color = COL.night, width = 0.75 } = {}) {
  const o = new THREE.Object3D();
  o.userData.dashPolys = polys.map(pts => ({ pts, nrm: normal ? pts.map(() => normal) : null }));
  o.userData.dashClip = clip;
  o.userData.dashColor = color;
  o.userData.dashWidth = width;
  return o;
}
function cyl(r, z0, z1, color, opts = {}, seg = 48) {
  const g = new THREE.CylinderGeometry(r, r, z1 - z0, seg, 1, opts.open || false);
  g.rotateX(Math.PI / 2);
  g.translate(0, 0, (z0 + z1) / 2);
  return mesh(g, color, opts);
}
function lathe(pts, color, opts = {}, seg = 48) {  // pts: [r, z] from bottom to top
  const g = new THREE.LatheGeometry(pts.map(([r, z]) => new THREE.Vector2(r, z)), seg);
  g.rotateX(Math.PI / 2);  // lathe is about Y; make it about Z
  return mesh(g, color, opts);
}
function tube(points, r, color, opts = {}) {
  const curve = new THREE.CatmullRomCurve3(points, false, 'centripetal');
  const g = new THREE.TubeGeometry(curve, Math.max(64, points.length * 24), r, 12, false);
  return mesh(g, color, opts);
}
// A length of cord: a smooth curve through `points`, round in section, with
// a braid pattern and flat cut ends (light discs). r: cord radius.
function rope(points, r, { color = COL.cord, ends = [true, true], braid = 2.2 * r, clip = [] } = {}) {
  const curve = new THREE.CatmullRomCurve3(points, false, 'centripetal', 0.5);
  const L = curve.getLength();
  const g = new THREE.TubeGeometry(curve, Math.max(48, Math.ceil(L / (r * 0.25))), r, 24, false);
  const grp = new THREE.Group();
  grp.add(mesh(g, color, braid ? { rope: L / braid, clip } : { clip }));
  const cap = (t, sgn) => {
    const p = curve.getPointAt(t), d = curve.getTangentAt(t).multiplyScalar(sgn);
    const cg = new THREE.CircleGeometry(r * 0.999, 32);
    const m = mesh(cg, COL.cut, { flat: true, clip });
    m.position.copy(p);
    m.quaternion.setFromUnitVectors(V(0, 0, 1), d);
    grp.add(m);
  };
  if (ends[0]) cap(0, -1);
  if (ends[1]) cap(1, 1);
  grp.userData.curve = curve;
  return grp;
}
function ball(p, r, color, opts = {}) {
  const g = new THREE.SphereGeometry(r, 24, 16);
  g.translate(p.x, p.y, p.z);
  return mesh(g, color, opts);
}
// A small overhand-style knot: a squashed trefoil, a reads-as-a-knot blob.
function knot(p, size, color, axis = V(0, 0, 1)) {
  const g = new THREE.TorusKnotGeometry(size, size * 0.42, 96, 12, 2, 3);
  g.scale(1, 1, 0.8);
  const m = mesh(g, color);
  m.position.copy(p);
  m.quaternion.setFromUnitVectors(V(0, 0, 1), axis.clone().normalize());
  return m;
}
// A straight arrow from a to b (shaft radius r), in launch orange.
function arrow(a, b, r = 1.2, color = COL.orange) {
  const dir = b.clone().sub(a);
  const len = dir.length();
  const head = Math.min(len * 0.45, r * 6);
  const grp = new THREE.Group();
  const shaft = new THREE.CylinderGeometry(r, r, len - head, 16);
  shaft.translate(0, (len - head) / 2, 0);
  const cone = new THREE.ConeGeometry(r * 2.6, head, 24);
  cone.translate(0, len - head / 2, 0);
  grp.add(mesh(shaft, color, { flat: true }), mesh(cone, color, { flat: true }));
  grp.position.copy(a);
  grp.quaternion.setFromUnitVectors(V(0, 1, 0), dir.normalize());
  return grp;
}
// A curved arrow around the z axis at height z, radius rad, from angle a0 to a1 (degrees).
function turnArrow(rad, z, a0, a1, r = 1.0, color = COL.orange) {
  const pts = [];
  const n = 40, d2r = Math.PI / 180;
  const head = r * 6;
  const aEnd = a1 - Math.sign(a1 - a0) * (head / rad) / d2r;
  for (let i = 0; i <= n; i++) {
    const a = (a0 + (aEnd - a0) * i / n) * d2r;
    pts.push(V(rad * Math.cos(a), rad * Math.sin(a), z));
  }
  const grp = new THREE.Group();
  grp.add(tube(pts, r, color, { flat: true }));
  const tip = V(rad * Math.cos(a1 * d2r), rad * Math.sin(a1 * d2r), z);
  const base = pts[pts.length - 1];
  const cone = new THREE.ConeGeometry(r * 2.6, head, 24);
  const m = mesh(cone, color, { flat: true });
  m.position.copy(base.clone().add(tip).multiplyScalar(0.5));
  m.quaternion.setFromUnitVectors(V(0, 1, 0), tip.clone().sub(base).normalize());
  grp.add(m);
  return grp;
}

// ---------- non-printed things ----------
// A model rocket motor: kraft casing, clay nozzle at the bottom (z0), clay cap on top.
function motor(info, z0, { color = COL.motor, clip = [], band = true } = {}) {
  const r = info.mtr_d / 2, L = info.mtr_len;
  const g = new THREE.Group();
  const throat = Math.max(1.2, r * 0.18), mouth = Math.max(3, r * 0.55);
  g.add(lathe([[mouth, 0], [r - 0.6, 0], [r, 0.6], [r, L - 0.6], [r - 0.6, L], [r * 0.55, L], [r * 0.55, L - 1.5],
               [0, L - 1.5]], color, { clip }, 64));
  // Nozzle cone (clay), seen from below.
  g.add(lathe([[throat, r * 0.9], [mouth, 0.01]], COL.clay, { clip }, 48));
  if (band) g.add(cyl(r + 0.05, L * 0.42, L * 0.62, COL.night, { clip, flat: true }, 64));
  g.position.z = z0;
  return g;
}
// The igniter (two leads, a tip up in the motor) and its plastic plug.
function igniter(info, zNozzle, { leadLen = 60, spread = 1, plug = true } = {}) {
  const g = new THREE.Group();
  const r = info.mtr_d / 2;
  const throat = Math.max(1.2, r * 0.18);
  const top = zNozzle + r * 0.9 + 6;
  const lead = s => [V(s * 0.5, 0, top), V(s * 0.6, 0, zNozzle + 2), V(s * 1.0, 0, zNozzle - 6),
                     V(s * (4 + 10 * spread), 0, zNozzle - 6 - leadLen * 0.45), V(s * (6 + 18 * spread), 0, zNozzle - 6 - leadLen)];
  g.add(tube(lead(1), 0.35, COL.red), tube(lead(-1), 0.35, COL.cord));
  g.add(ball(V(0, 0, top + 0.6), 1.0, COL.night));
  if (plug) g.add(lathe([[0.6, zNozzle - 7], [throat + 1.4, zNozzle - 7], [throat + 0.7, zNozzle + r * 0.75], [0.6, zNozzle + r * 0.75]],
                        COL.orange, {}, 32));
  return g;
}
// Parachute canopy, open: dome of `gores` alternating colours, radius rc, apex at z; lines to `conf`.
function chuteOpen(center, rc, conf, { gores = 8, depth = 0.35 } = {}) {
  const g = new THREE.Group();
  const theta = 1.1;  // dome half-angle
  const R0 = rc / Math.sin(theta);
  for (let i = 0; i < gores; i++) {
    const sg = new THREE.SphereGeometry(R0, 4, 10, (i / gores) * Math.PI * 2, Math.PI * 2 / gores, 0, theta);
    sg.rotateX(Math.PI / 2);
    sg.scale(1, 1, depth / (1 - Math.cos(theta)) * rc / R0);
    sg.translate(center.x, center.y, center.z - R0 * depth / (1 - Math.cos(theta)) * rc / R0);
    g.add(mesh(sg, i % 2 ? COL.chuteA : COL.chuteB));
  }
  for (let i = 0; i < gores; i++) {
    const a = (i + 0.5) / gores * Math.PI * 2 + Math.PI / 2;
    const rim = V(center.x + rc * Math.cos(a), center.y + rc * Math.sin(a), center.z - depth * rc);
    g.add(tube([rim, rim.clone().lerp(conf, 0.5), conf], 0.25, COL.night, { outline: false }));
  }
  return g;
}
// Wadding: crumpled squares (flattened, jittered icosahedra).
function wadding(center, size, n = 3, seed = 1) {
  const g = new THREE.Group();
  let s = seed;
  const rnd = () => (s = (s * 9301 + 49297) % 233280) / 233280;
  for (let i = 0; i < n; i++) {
    const ig = new THREE.IcosahedronGeometry(size * (0.45 + 0.1 * rnd()), 1);
    const p = ig.attributes.position;
    for (let k = 0; k < p.count; k++) p.setXYZ(k, p.getX(k) * (0.9 + 0.25 * rnd()), p.getY(k) * (0.9 + 0.25 * rnd()), p.getZ(k) * (0.45 + 0.2 * rnd()));
    ig.computeVertexNormals();
    const m = mesh(ig, COL.wad);
    m.position.set(center.x + (rnd() - 0.5) * size * 0.3, center.y + (rnd() - 0.5) * size * 0.3, center.z + i * size * 0.42);
    m.rotation.set(rnd(), rnd(), rnd());
    g.add(m);
  }
  return g;
}
// A rolled parachute: a cylinder with the lines wrapped round it.
function chuteRolled(z0, len, r, { color = COL.chuteA, wrap = true } = {}) {
  const g = new THREE.Group();
  g.add(lathe([[0, z0], [r * 0.85, z0], [r, z0 + r * 0.3], [r, z0 + len - r * 0.3], [r * 0.85, z0 + len], [0, z0 + len]], color, {}, 40));
  if (wrap) {
    const pts = [];
    for (let i = 0; i <= 80; i++) {
      const a = i / 80 * Math.PI * 2 * 2.5;
      pts.push(V((r + 0.3) * Math.cos(a), (r + 0.3) * Math.sin(a), z0 + len * 0.2 + len * 0.55 * i / 80));
    }
    g.add(tube(pts, 0.3, COL.night, { outline: false }));
  }
  return g;
}

// ---------- rendering ----------
let renderer;
function setup() {
  const canvas = document.createElement('canvas');
  document.body.appendChild(canvas);
  renderer = new THREE.WebGLRenderer({ canvas, antialias: false, alpha: true, preserveDrawingBuffer: true });
  renderer.localClippingEnabled = true;
  renderer.setPixelRatio(1);
}

const quadScene = new THREE.Scene();
const quadCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
const compMat = new THREE.ShaderMaterial({
  uniforms: { tColor: { value: null }, tNd: { value: null }, tId: { value: null }, uTexel: { value: new THREE.Vector2() },
              uW: { value: 3 }, uDepthThr: { value: 1.0 }, uLine: { value: new THREE.Color(COL.night) },
              uNormThr: { value: 0.25 } },
  vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }`,
  fragmentShader: `
    uniform sampler2D tColor, tNd, tId; uniform vec2 uTexel; uniform float uW, uDepthThr, uNormThr; uniform vec3 uLine;
    varying vec2 vUv;
    float depthAt(vec2 uv){ return texture2D(tNd, uv).a * ${FAR.toFixed(1)}; }
    vec3 nAt(vec2 uv){ return texture2D(tNd, uv).rgb * 2.0 - 1.0; }
    vec3 idAt(vec2 uv){ return texture2D(tId, uv).rgb; }
    float edgeAt(vec2 uv, vec2 o) {
      float d0 = depthAt(uv), da = depthAt(uv + o), db = depthAt(uv - o);
      float e = 0.0;
      // silhouettes: second difference of depth, or a step to the background
      if (abs(da + db - 2.0 * d0) > uDepthThr) e = 1.0;
      vec3 i0 = idAt(uv), ia = idAt(uv + o);
      if (distance(i0, ia) > 0.001) e = 1.0;
      vec3 n0 = nAt(uv), na = nAt(uv + o);
      if (1.0 - dot(n0, na) > uNormThr) e = 1.0;
      return e;
    }
    void main() {
      vec4 c = texture2D(tColor, vUv);
      float e = 0.0;
      for (int k = 0; k < 8; k++) {
        float a = float(k) * 0.785398;
        vec2 o = vec2(cos(a), sin(a)) * uW * uTexel;
        e = max(e, edgeAt(vUv, o));
        e = max(e, edgeAt(vUv, o * 0.5));
      }
      // nothing drawn and no line: transparent
      vec3 col = mix(c.rgb, uLine, e);
      float alpha = max(c.a, e);
      gl_FragColor = vec4(col, alpha);
    }`,
  transparent: true,
});
quadScene.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), compMat));

function collectMeshes(root) {
  const out = [];
  root.traverse(o => { if (o.isMesh && o.userData.color) out.push(o); });
  return out;
}

// Fit an orthographic camera looking along -dir (dir points from the
// subject toward the camera) to every visible vertex, with a margin.
function frameCamera(root, dir, up, margin, aspectFix, focus) {
  root.updateMatrixWorld(true);
  const cam = new THREE.OrthographicCamera(-1, 1, 1, -1, 1, FAR);
  const dist = FAR / 2;
  cam.up.copy(up);
  cam.position.copy(dir.clone().normalize().multiplyScalar(dist));
  cam.lookAt(0, 0, 0);
  cam.updateMatrixWorld(true);
  const inv = cam.matrixWorldInverse;
  const box = new THREE.Box2(new THREE.Vector2(Infinity, Infinity), new THREE.Vector2(-Infinity, -Infinity));
  const v = new THREE.Vector3();
  for (const m of collectMeshes(root)) {
    const pos = m.geometry.attributes.position;
    const planes = m.userData.color.clippingPlanes || [];
    for (let i = 0; i < pos.count; i += 1) {
      v.fromBufferAttribute(pos, i).applyMatrix4(m.matrixWorld);
      if (planes.some(p => p.distanceToPoint(v) < -0.01)) continue;
      if (focus && !focus.containsPoint(v)) continue;
      v.applyMatrix4(inv);
      box.expandByPoint(new THREE.Vector2(v.x, v.y));
    }
  }
  let w = box.max.x - box.min.x, h = box.max.y - box.min.y;
  const cx = (box.max.x + box.min.x) / 2, cy = (box.max.y + box.min.y) / 2;
  w += 2 * margin; h += 2 * margin;
  if (aspectFix) {  // force w/h
    if (w / h < aspectFix) w = h * aspectFix; else h = w / aspectFix;
  }
  cam.left = cx - w / 2; cam.right = cx + w / 2; cam.top = cy + h / 2; cam.bottom = cy - h / 2;
  cam.updateProjectionMatrix();
  return { cam, w, h };
}

async function render(def) {
  nextId = 1;
  const root = new THREE.Group();
  const s = def.build(root) || {};
  const dir = s.dir || V(1, -1, 0.5), up = s.up || V(0, 0, 1);
  const { cam, w, h } = frameCamera(root, dir, up, s.margin ?? 6, s.aspect, s.focus);
  const W = s.W || 2400;
  const H = Math.round(W * h / w);
  addDashes(root, cam, W, H, w / W, s.line ?? 2.6, s.dash);
  const SS = Math.min(2, 8000 / Math.max(W, H));  // supersample (textures max out near 8k)
  const PW = Math.round(W * SS), PH = Math.round(H * SS);
  renderer.setSize(PW, PH, false);
  const opt = { type: THREE.FloatType, minFilter: THREE.NearestFilter, magFilter: THREE.NearestFilter };
  const tColor = new THREE.WebGLRenderTarget(PW, PH, { type: THREE.UnsignedByteType });
  const tNd = new THREE.WebGLRenderTarget(PW, PH, opt);
  const tId = new THREE.WebGLRenderTarget(PW, PH, opt);
  const scene = new THREE.Scene();
  scene.add(root);
  const meshes = collectMeshes(root);
  const pass = (key, target, clear, alpha) => {
    for (const m of meshes) { m.material = m.userData[key]; m.visible = key === 'color' || !m.userData.dash; }
    renderer.setRenderTarget(target);
    renderer.setClearColor(clear, alpha);
    renderer.clear();
    renderer.render(scene, cam);
  };
  pass('color', tColor, 0xffffff, 0);
  pass('nd', tNd, 0x8080ff, 1);
  pass('id', tId, 0x000000, 1);
  const worldPerPx = w / PW;
  compMat.uniforms.tColor.value = tColor.texture;
  compMat.uniforms.tNd.value = tNd.texture;
  compMat.uniforms.tId.value = tId.texture;
  compMat.uniforms.uTexel.value.set(1 / PW, 1 / PH);
  // Line width: s.line in final-image pixels (default about 0.6 pt at 300 dpi)
  compMat.uniforms.uW.value = (s.line ?? 2.6) * SS / 2;
  compMat.uniforms.uDepthThr.value = Math.max(0.6, worldPerPx * (s.depthK ?? 6));
  compMat.uniforms.uNormThr.value = s.normThr ?? 0.25;
  renderer.setRenderTarget(null);
  renderer.setClearColor(0xffffff, 0);
  renderer.clear();
  renderer.render(quadScene, quadCam);
  // Downsample to the final size.
  const out = document.createElement('canvas');
  out.width = W; out.height = H;
  const ctx = out.getContext('2d');
  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = 'high';
  ctx.drawImage(renderer.domElement, 0, 0, W, H);
  // Labelled points -> fractions of the image.
  const points = {};
  for (const [k, p] of Object.entries(s.points || {})) {
    const q = (p.isObject3D ? p.getWorldPosition(new THREE.Vector3()) : p.clone()).project(cam);
    points[k] = [+((q.x + 1) / 2).toFixed(4), +((1 - q.y) / 2).toFixed(4)];
  }
  for (const t of [tColor, tNd, tId]) t.dispose();
  return { png: out.toDataURL('image/png'), w: W, h: H, points };
}

// Dashed lines: every object with userData.dashPolys (fillet edges of the
// printed parts, dashed() helpers) gets thin tubes along its lines, cut into
// dashes measured on the screen (so they look the same in every view), lifted
// just off the surface and depth-tested, so hidden ones stay hidden. They are
// drawn in the colour pass only: the outline pass doesn't see them.
function addDashes(root, cam, W, H, worldPerPx, line, opts = {}) {
  root.updateMatrixWorld(true);
  const owners = [];
  root.traverse(o => { if (o.userData.dashPolys?.length && !o.userData.dash) owners.push(o); });
  const toCam = V(0, 0, 1).applyQuaternion(cam.quaternion);
  const dashPx = (opts.on ?? 3.4) * line, gapPx = (opts.off ?? 2.2) * line;
  for (const o of owners) {
    const wpx = (o.userData.dashWidth ?? opts.width ?? 0.62) * line;
    const r = wpx * worldPerPx / 2;
    const nm = new THREE.Matrix3().getNormalMatrix(o.matrixWorld);
    const geos = [];
    for (const poly of o.userData.dashPolys) {
      const P = poly.pts.map((p, i) => {
        const q = p.clone().applyMatrix4(o.matrixWorld);
        const n = poly.nrm ? poly.nrm[i].clone().applyMatrix3(nm).normalize() : toCam;
        return q.addScaledVector(n, r * 1.1);
      });
      const S = P.map(p => { const q = p.clone().project(cam); return new THREE.Vector2(q.x * W / 2, q.y * H / 2); });
      const cum = [0];
      for (let i = 1; i < S.length; i++) cum.push(cum[i - 1] + S[i].distanceTo(S[i - 1]));
      const total = cum[cum.length - 1];
      if (total < 2 * dashPx + gapPx) continue;  // seen end-on, or too short to read as dashed
      // Whole dashes at both ends: stretch the gap a little to fit.
      const n = Math.max(1, Math.round((total + gapPx) / (dashPx + gapPx)));
      const gap = n > 1 ? (total - n * dashPx) / (n - 1) : 0;
      const dash = n > 1 ? dashPx : total;
      const at = d => {  // world point at screen distance d along the line
        let i = 1;
        while (i < cum.length - 1 && cum[i] < d) i++;
        const t = (d - cum[i - 1]) / Math.max(1e-9, cum[i] - cum[i - 1]);
        return P[i - 1].clone().lerp(P[i], Math.min(1, Math.max(0, t)));
      };
      for (let k = 0; k < n; k++) {
        const d0 = k * (dash + Math.max(gap, gapPx * 0.5)), d1 = Math.min(total, d0 + dash);
        if (d1 - d0 < 1) continue;
        const pts = [at(d0)];
        for (let i = 1; i < cum.length - 1; i++) if (cum[i] > d0 && cum[i] < d1) pts.push(P[i].clone());
        pts.push(at(d1));
        if (pts[0].distanceTo(pts[pts.length - 1]) < 1e-6) continue;
        const curve = pts.length > 2 ? new THREE.CatmullRomCurve3(pts) : new THREE.LineCurve3(pts[0], pts[1]);
        const g = new THREE.TubeGeometry(curve, Math.max(2, pts.length * 2), r, 8, false);
        geos.push(g);
      }
    }
    if (!geos.length) continue;
    const clip = o.userData.dashClip ?? o.userData.color?.clippingPlanes ?? [];
    const m = mesh(mergeGeometries(geos), o.userData.dashColor ?? COL.night, { flat: true, clip, cut: o.userData.dashColor ?? COL.night });
    m.userData.dash = true;
    root.add(m);
  }
}

// A marker that follows its parent's transforms (for callouts).
function mark(parent, x, y, z) {
  const o = new THREE.Object3D();
  o.position.set(x, y, z);
  parent.add(o);
  return o;
}
const deg = THREE.MathUtils.degToRad;
const viewDir = (az, el) => V(Math.cos(deg(el)) * Math.cos(deg(az)), Math.cos(deg(el)) * Math.sin(deg(az)), Math.sin(deg(el)));

// ---------- the scenes ----------
import { defineScenes } from './scene_defs.js';
const SCENES = defineScenes({ THREE, V, COL, R, part, cyl, lathe, tube, rope, dashed, ball, knot, arrow, turnArrow, motor, igniter,
                              chuteOpen, chuteRolled, wadding, mark, viewDir, deg, mesh });

setup();
await loadRocket('m18');
await loadRocket('m24');
window.SCENES = SCENES;
window.renderScene = name => render(SCENES[name]);
window.SCENES_READY = true;
