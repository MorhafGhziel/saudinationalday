import * as THREE from "three";

/**
 * The stage shows one rendered world at a time and, where the device can afford it, gives it depth.
 *
 * Every world is a Blender render plus a small data image from the same camera (R = sqrt of inverse
 * depth, G = palm-frond mask). Nothing here renders 3D geometry: the GPU only draws one full-screen
 * rectangle. How much that rectangle does depends on the tier:
 *
 *   2 full   parallax (3 steps), frond sway, depth-hidden dust, birds, mist, grain. Up to ~2.3 MP, 60 fps.
 *   1 lite   parallax (1 step), frond sway, mist. Up to ~1.0 MP, 30 fps. For phones and modest laptops.
 *   0 still  no WebGL at all: the render as a plain image, with a CSS veil for travel. For anything else.
 *
 * The tier is chosen from what the browser reports about the device, then a watchdog measures real
 * frame times and steps down (never up) if the device cannot keep pace. The walk through the rock is
 * an ordinary H.264 video, decoded in hardware on every tier.
 */
export type Aspect = "land" | "port";
export type View = { color: string; data: string | null };
export type Tier = 0 | 1 | 2;

const VERT = /* glsl */ `varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }`;

const frag = (tier: Tier) => /* glsl */ `
precision highp float;
#define STEPS ${tier === 2 ? 3 : 1}
${tier === 2 ? "#define FULL" : ""}
varying vec2 vUv;
uniform sampler2D uColor, uData;
uniform float uHasData, uTime, uMist, uZoom, uLife, uFade, uAspect;
uniform vec2 uShift, uCover, uFocus;
uniform vec3 uMistColor;

float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
vec2 cover(vec2 uv){ return (uv - 0.5) * uCover + 0.5; }

void main(){
  vec2 uv = cover((vUv - uFocus) / uZoom + uFocus);
  float d = 0.0;
  if (uHasData > 0.5) {
    vec2 p = uv;
    for (int i = 0; i < STEPS; i++) { d = texture2D(uData, p).r; p = uv - uShift * (d - 0.22); }
    uv = p;
    vec2 dg = texture2D(uData, uv).rg; d = dg.r;
    float w = sin(uTime * 0.7 + uv.y * 7.0 + uv.x * 3.0) * 0.6 + sin(uTime * 1.3 + uv.x * 11.0) * 0.4;
    uv += vec2(w * 0.0030, w * 0.0012) * dg.g * uLife;
  }
  vec3 col = texture2D(uColor, uv).rgb;
#ifdef FULL
  if (uHasData > 0.5) {
    float lum = dot(col, vec3(0.3, 0.6, 0.1));
    for (int L = 0; L < 3; L++) {                       // dust: hidden by anything nearer, brighter where the picture is lit
      float fl = float(L); float layerD = 0.62 - fl * 0.2;
      vec2 g = vUv * vec2(uAspect, 1.0) * 13.0 * (1.0 + fl * 0.8) + vec2(uTime * (0.010 + fl * 0.004), uTime * -0.006) + uShift * (layerD - 0.22) * 40.0;
      vec2 cell = floor(g); vec2 f = fract(g) - 0.5; float r = hash(cell + fl * 17.0);
      vec2 o = vec2(hash(cell + 3.1), hash(cell + 7.7)) - 0.5;
      float m = smoothstep(0.016 + r * 0.014, 0.0, length(f - o * 0.7)) * step(0.80, r);
      col += vec3(1.0, 0.86, 0.66) * m * (0.6 + 0.4 * sin(uTime * (0.6 + r) + r * 40.0)) * step(d, layerD) * (0.06 + lum * 0.38) * uLife;
    }
    float sky = 1.0 - smoothstep(0.015, 0.05, d);      // birds: tiny, far, only against open sky
    for (int b = 0; b < 4; b++) {
      float fb = float(b);
      vec2 c = vec2(fract(0.17 * fb + uTime * (0.012 + 0.004 * hash(vec2(fb, 1.0))) + hash(vec2(fb, 9.0))), 0.62 + 0.22 * hash(vec2(fb, 3.0)) + 0.015 * sin(uTime * 0.4 + fb));
      vec2 q = (vUv - c) * vec2(uAspect, 1.0) * 260.0;
      float bird = smoothstep(0.30, 0.0, abs(q.y - abs(q.x) * sin(uTime * 5.5 + fb * 2.0) * 0.55)) * smoothstep(1.0, 0.0, abs(q.x) / 1.6);
      col = mix(col, col * 0.25, bird * sky * 0.8 * uLife);
    }
  }
  col += (hash(vUv * 900.0 + uTime) - 0.5) * 0.03;
#endif
  if (uMist > 0.001) {                                   // mist fills from the horizon towards the lens
    float fog = uHasData > 0.5 ? smoothstep(1.0 - uMist * 1.6, 1.25 - uMist * 1.25, 1.0 - d + 0.1 * sin(vUv.x * 9.0 + vUv.y * 5.0 + uTime * 0.2)) : uMist;
    col = mix(col, uMistColor, clamp(fog, 0.0, 1.0));
  }
  col *= mix(0.72, 1.0, smoothstep(1.25, 0.35, length((vUv - 0.5) * vec2(1.05, 1.2))));
  gl_FragColor = vec4(col * uFade, 1.0);
}`;

const BUDGET: Record<Tier, number> = { 2: 2_300_000, 1: 1_000_000, 0: 0 };

export function pickTier(): Tier {
  const q = new URLSearchParams(location.search).get("q");
  if (q === "0" || q === "1" || q === "2") return Number(q) as Tier;
  const n = navigator as Navigator & { deviceMemory?: number; connection?: { saveData?: boolean } };
  if (n.connection?.saveData || (n.deviceMemory !== undefined && n.deviceMemory <= 1)) return 0;
  const mobile = matchMedia("(pointer: coarse)").matches || Math.min(screen.width, screen.height) < 700;
  const modest = (n.deviceMemory !== undefined && n.deviceMemory <= 4) || (navigator.hardwareConcurrency ?? 8) <= 4;
  return mobile || modest ? 1 : 2;
}

export class Stage {
  tier: Tier;
  aspect: Aspect = "land";
  reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  zoomTarget = 1;
  onTier: (t: Tier) => void = () => {};
  private zoom = 1;
  private renderer: THREE.WebGLRenderer | null = null;
  private scene = new THREE.Scene();
  private cam = new THREE.Camera();
  private mesh: THREE.Mesh | null = null;
  private uniforms: Record<string, { value: unknown }>;
  private loader = new THREE.TextureLoader();
  private cache = new Map<string, THREE.Texture>();
  private imgSize = new THREE.Vector2(16, 9);
  private target = new THREE.Vector2();
  private shift = new THREE.Vector2();
  private raf = 0; private t0 = performance.now(); private last = 0;
  private acc = 0; private frames = 0; private settle = 0; private quiet = 0;

  get ok() { return this.tier > 0; }

  constructor(canvas: HTMLCanvasElement, private still: HTMLElement, private veil: HTMLElement) {
    this.tier = pickTier();
    if (this.tier > 0) {
      try {
        this.renderer = new THREE.WebGLRenderer({ canvas, antialias: false, alpha: false, stencil: false, depth: false, powerPreference: this.tier === 2 ? "high-performance" : "default" });
        this.renderer.outputColorSpace = THREE.LinearSRGBColorSpace;          // renders are display-ready already
      } catch { this.tier = 0; }
    }
    this.uniforms = {
      uColor: { value: null }, uData: { value: null }, uHasData: { value: 0 }, uTime: { value: 0 }, uAspect: { value: 1 }, uMist: { value: 0 },
      uMistColor: { value: new THREE.Color(0.95, 0.8, 0.6) }, uZoom: { value: 1 }, uLife: { value: 1 }, uFade: { value: 0 },
      uShift: { value: new THREE.Vector2() }, uCover: { value: new THREE.Vector2(1, 1) }, uFocus: { value: new THREE.Vector2(0.5, 0.5) },
    };
    this.build();
    canvas.addEventListener("webglcontextlost", (e) => { e.preventDefault(); this.drop(0); });
    addEventListener("resize", () => this.resize());
    addEventListener("pointermove", (e) => { if (e.pointerType === "mouse") this.target.set(e.clientX / innerWidth - 0.5, 0.5 - e.clientY / innerHeight); }, { passive: true });
    let sx = 0, sy = 0;                                                       // touch drag; device-motion permission is never requested
    addEventListener("touchstart", (e) => { sx = e.touches[0].clientX; sy = e.touches[0].clientY; }, { passive: true });
    addEventListener("touchmove", (e) => this.target.set(THREE.MathUtils.clamp((e.touches[0].clientX - sx) / innerWidth, -0.5, 0.5), THREE.MathUtils.clamp((sy - e.touches[0].clientY) / innerHeight, -0.5, 0.5)), { passive: true });
    addEventListener("touchend", () => this.target.set(0, 0), { passive: true });
    document.addEventListener("visibilitychange", () => { cancelAnimationFrame(this.raf); if (!document.hidden && this.tier > 0) { this.last = 0; this.settle = 0; this.loop(0); } });
    this.resize();
    if (this.tier > 0) this.loop(0);
    this.mark();
  }

  private mark() { const c = document.documentElement.classList; c.toggle("no-gl", this.tier === 0); c.remove("tier-0", "tier-1", "tier-2"); c.add(`tier-${this.tier}`); }

  private build() {
    if (!this.renderer) return;
    if (this.mesh) { (this.mesh.material as THREE.Material).dispose(); this.scene.remove(this.mesh); }
    const mat = new THREE.ShaderMaterial({ vertexShader: VERT, fragmentShader: frag(this.tier), depthTest: false, depthWrite: false, uniforms: this.uniforms as never });
    this.mesh = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), mat); this.mesh.frustumCulled = false; this.scene.add(this.mesh);
  }

  /** Steps down a tier. Tier 0 hands the picture to a plain <div> and stops the GPU loop for good. */
  private drop(to: Tier) {
    if (to >= this.tier) return;
    this.tier = to; this.settle = 0; this.frames = 0; this.acc = 0;
    if (to === 0) { cancelAnimationFrame(this.raf); this.renderer?.dispose(); this.renderer = null; } else { this.build(); this.resize(); }
    this.mark(); this.onTier(to);
  }

  private resize() {
    this.aspect = innerWidth / innerHeight < 0.85 ? "port" : "land";
    if (!this.renderer) return;
    const css = innerWidth * innerHeight, want = Math.min(devicePixelRatio, 2);
    const ratio = Math.min(want, Math.sqrt(BUDGET[this.tier] / css));        // a pixel budget, not a fixed ratio: a 4K screen never pays for 4K
    this.renderer.setPixelRatio(Math.max(0.5, ratio));
    this.renderer.setSize(innerWidth, innerHeight, false);
    this.fit();
  }
  private fit() {
    const va = innerWidth / innerHeight, ia = this.imgSize.x / this.imgSize.y, m = 0.94;   // the margin keeps parallax from ever showing an edge
    this.uniforms.uAspect.value = va;
    (this.uniforms.uCover.value as THREE.Vector2).set(va > ia ? m : (va / ia) * m, va > ia ? (ia / va) * m : m);
  }

  /** Lighter pictures for lighter devices. */
  url(v: string) { return this.tier === 2 && Math.max(innerWidth, innerHeight) * Math.min(devicePixelRatio, 2) > 1700 ? v : v.replace(/\.webp$/, "-sm.webp"); }

  private tex(url: string): Promise<THREE.Texture> {
    const hit = this.cache.get(url);
    if (hit) return Promise.resolve(hit);
    return new Promise((ok, no) => this.loader.load(url, (t) => {
      t.colorSpace = THREE.NoColorSpace; t.minFilter = THREE.LinearFilter; t.generateMipmaps = false; t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping;
      this.cache.set(url, t); ok(t);
    }, undefined, no));
  }

  async show(v: View) {
    const color = this.url(v.color);
    this.still.style.backgroundImage = `url(${color})`;
    if (!this.renderer) { await new Promise<void>((ok) => { const i = new Image(); i.onload = i.onerror = () => ok(); i.src = color; }); return; }
    const [c, d] = await Promise.all([this.tex(color), v.data ? this.tex(v.data) : Promise.resolve(null)]);
    for (const [k, t] of this.cache) if (t !== c && t !== d) { t.dispose(); this.cache.delete(k); }     // old worlds leave GPU memory
    this.uniforms.uColor.value = c; this.uniforms.uData.value = d; this.uniforms.uHasData.value = d ? 1 : 0;
    const im = c.image as HTMLImageElement; this.imgSize.set(im.width, im.height); this.fit(); this.settle = 0;
  }
  preload(v: View) { const i = new Image(); i.src = this.url(v.color); if (v.data && this.renderer) { const j = new Image(); j.src = v.data; } }

  tween(name: "uMist" | "uFade" | "uLife", to: number, ms: number): Promise<void> {
    if (this.reduced) ms = Math.min(ms, 250);
    if (!this.renderer) {                                                     // tier 0: travel is a CSS veil over the still picture
      if (name !== "uMist") return Promise.resolve();
      this.veil.style.transitionDuration = `${ms}ms`; this.veil.style.opacity = String(to);
      return new Promise((r) => setTimeout(r, ms));
    }
    const u = this.uniforms[name]; const from = u.value as number; const t0 = performance.now(); this.quiet = performance.now() + ms + 400;
    return new Promise((done) => { const step = () => { const k = Math.min(1, (performance.now() - t0) / ms); u.value = from + (to - from) * k * k * (3 - 2 * k); if (k < 1) requestAnimationFrame(step); else done(); }; step(); });
  }
  setMist(rgb: [number, number, number]) { (this.uniforms.uMistColor.value as THREE.Color).setRGB(...rgb); this.veil.style.backgroundColor = `rgb(${rgb.map((c) => Math.round(c * 255)).join(",")})`; }
  setFocus(x: number, y: number) { (this.uniforms.uFocus.value as THREE.Vector2).set(x, 1 - y); }

  private loop = (now: number) => {
    this.raf = requestAnimationFrame(this.loop);
    if (!this.renderer) return;
    if (this.tier === 1 && now - this.last < 30) return;                      // lite: 30 fps is plenty for slow drift, and halves the work
    const dt = this.last ? now - this.last : 16; this.last = now;
    // watchdog: once things settle, average real frame times and step down if this device cannot keep pace
    if (++this.settle > 45 && now > this.quiet && !document.hidden && dt < 250) {
      this.acc += dt;
      if (++this.frames >= 80) { const avg = this.acc / this.frames; this.acc = 0; this.frames = 0; if (avg > (this.tier === 2 ? 25 : 55)) { this.drop((this.tier - 1) as Tier); return; } }
    }
    const t = (now - this.t0) / 1000, live = this.reduced ? 0 : 1;
    this.uniforms.uTime.value = t * live;
    const tx = (this.target.x * 0.030 + Math.sin(t * 0.13) * 0.004) * live, ty = (this.target.y * 0.018 + Math.cos(t * 0.11) * 0.003) * live;
    this.shift.x += (tx - this.shift.x) * 0.06; this.shift.y += (ty - this.shift.y) * 0.06;
    (this.uniforms.uShift.value as THREE.Vector2).copy(this.shift);
    this.zoom += (this.zoomTarget - this.zoom) * 0.07; this.uniforms.uZoom.value = this.zoom;
    if (this.reduced) this.uniforms.uLife.value = 0;
    this.renderer.render(this.scene, this.cam);
  };
}
