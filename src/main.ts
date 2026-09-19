import { copy, places, values, type Place, type Value } from "./data";
import { download, drawPoster, share, toBlob } from "./poster";
import { Sound } from "./sound";
import { Stage, type View } from "./stage";

/**
 * The journey: threshold → walk out → choose a place → through the mist into it → a word and a name
 * → the poster. One state at a time, every control a real HTML element, nothing stored but in memory.
 */
const $ = <T extends HTMLElement>(s: string) => document.querySelector(s) as T;
const ui = $("#ui"), loading = $("#loading"), still = $("#still"), veil = $("#veil"), video = $("#walk") as HTMLVideoElement;
const params = new URLSearchParams(location.search);
const CAPTURE = params.has("capture");
if (CAPTURE) document.documentElement.classList.add("capture");

const stage = new Stage($("#stage") as HTMLCanvasElement, still, veil);
const sound = new Sound();

const aspect = () => (innerWidth / innerHeight < 0.85 ? "port" : "land");
const opening = (n: 0 | 1): View => ({ color: `/worlds/opening/${aspect()}-still${n}.webp`, data: `/worlds/opening/${aspect()}-data${n}.png` });
const world = (id: string): View => ({ color: `/worlds/${id}/${aspect()}-still0.webp`, data: `/worlds/${id}/${aspect()}-data0.png` });

/** The walk through the rock is a normal muted video: hardware-decoded, smooth on every device. */
function prepWalk() { const src = `/worlds/opening/walk-${aspect()}.mp4`; if (!video.src.endsWith(src)) { video.src = src; video.load(); } }
async function playWalk(): Promise<boolean> {
  prepWalk();
  try { video.currentTime = 0; await video.play(); } catch { return false; }        // called straight from the click, so phones allow it
  video.classList.add("on");
  setTimeout(() => void show(opening(1)), 350);                                       // the arrival view loads underneath while the video covers it
  await new Promise<void>((done) => { video.onended = () => done(); video.onerror = () => done(); setTimeout(done, 7000); });
  video.classList.remove("on"); setTimeout(() => video.pause(), 500);
  return true;
}

type State = "intro" | "select" | "place" | "poster";
let state: State = "intro", busy = false, current: View = opening(0);
let place: Place = places.find((p) => p.ready) ?? places[0], value: Value | null = null, name = "";
let skipMotion = stage.reduced;

async function show(v: View) { current = v; await stage.show(v); }
const wait = (ms: number) => new Promise((r) => setTimeout(r, ms));

function scene(html: string, cls = ""): HTMLElement {
  ui.querySelectorAll(".scene").forEach((o) => { o.classList.remove("on"); setTimeout(() => o.remove(), 900); });
  const el = document.createElement("section"); el.className = `scene ${cls}`; el.innerHTML = html; ui.append(el);
  requestAnimationFrame(() => requestAnimationFrame(() => el.classList.add("on")));
  return el;
}
const arrow = `<svg viewBox="0 0 32 20" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="M31 10H2M10 2 2 10l8 8"/></svg>`;

/* ------------------------------------------------------------------ 1. threshold */
function intro() {
  state = "intro"; $("#back").hidden = true; stage.zoomTarget = 1;
  const el = scene(`<div class="intro">
    <h1><span class="rise">${copy.title}</span></h1>
    <p class="sub rise d1">${copy.sub}</p>
    <button class="go rise d2" type="button" id="go">${copy.start} ${arrow}</button>
    <p class="hint rise d3">${copy.hint}</p></div>`);
  el.querySelector<HTMLButtonElement>("#go")!.addEventListener("click", enter);
}

/* ------------------------------------------------------------------ 2. the walk out, then the choice */
async function enter() {
  if (busy) return; busy = true;
  ui.querySelector(".scene")?.classList.remove("on");
  sound.swell(4);
  const played = !skipMotion && (await playWalk());
  if (!played) { await stage.tween("uMist", 1, 350); await show(opening(1)); await stage.tween("uMist", 0, 500); }
  busy = false; select();
}

function select() {
  state = "select"; $("#back").hidden = false; stage.zoomTarget = 1;
  places.forEach((p) => p.ready && stage.preload(world(p.id)));
  const a = aspect();
  const el = scene(`<h2 class="ask">${copy.ask}</h2>
    <div role="radiogroup" aria-label="${copy.ask}">${places.map((p) => `<button class="spot" type="button" role="radio" aria-checked="${p.id === place.id}" data-id="${p.id}" style="right:${(1 - p.anchor[a][0]) * 100}%;top:${p.anchor[a][1] * 100}%"><b>${p.name}</b><small>${p.ready ? p.region : copy.soon}</small></button>`).join("")}</div>
    <div class="dock"><p class="line" id="line">${place.line}</p><p class="idx" id="idx"></p><button class="btn" type="button" id="in">${copy.enter}</button></div>`);
  const spots = [...el.querySelectorAll<HTMLButtonElement>(".spot")];
  const pick = (id: string, focus = false) => {
    place = places.find((p) => p.id === id)!;
    spots.forEach((s) => { const on = s.dataset.id === id; s.setAttribute("aria-checked", String(on)); s.tabIndex = on ? 0 : -1; if (on && focus) s.focus(); });
    el.querySelector("#line")!.textContent = place.ready ? place.line : copy.soonLine;
    el.querySelector<HTMLButtonElement>("#in")!.disabled = !place.ready;
    el.querySelector("#idx")!.textContent = `${String(places.indexOf(place) + 1).padStart(2, "0")} / ${String(places.length).padStart(2, "0")}`;
    sound.tick();
  };
  pick(place.id);
  spots.forEach((s) => s.addEventListener("click", () => pick(s.dataset.id!)));
  el.addEventListener("keydown", (e) => {
    if (!["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(e.key)) return;
    e.preventDefault(); const i = places.indexOf(place); const step = e.key === "ArrowLeft" || e.key === "ArrowDown" ? 1 : -1;
    pick(places[(i + step + places.length) % places.length].id, true);
  });
  el.querySelector("#in")!.addEventListener("click", () => place.ready && travel(world(place.id), arrive));
}

/* ------------------------------------------------------------------ travel: the air fills with mist, the place changes inside it, the mist clears */
async function travel(to: View, then: () => void) {
  while (busy) await wait(100);            // a tap during a transition is kept, not lost: it runs as soon as the air clears
  busy = true;
  ui.querySelector(".scene")?.classList.remove("on");
  stage.setMist(place.mist); sound.swell(3);
  await stage.tween("uMist", 1, skipMotion ? 250 : 1500); await show(to); await wait(skipMotion ? 0 : 250); then(); await stage.tween("uMist", 0, skipMotion ? 250 : 1900);
  busy = false;
}

/* ------------------------------------------------------------------ 3. inside the place */
function arrive() {
  state = "place"; $("#back").hidden = false;
  const a = aspect(); stage.setFocus(place.focus[a][0], place.focus[a][1]);
  const el = scene(`<div class="arrive"><h2>${place.name}</h2><p>${place.line}</p><p class="look">مرّر أو استخدم الأسهم لتقترب من التفاصيل</p><p class="photo-credit">${place.credit.href ? `<a href="${place.credit.href}" target="_blank" rel="noreferrer">${place.credit.short}</a>` : place.credit.short}</p></div>
    <form class="form" id="f" novalidate>
      <fieldset><legend>${copy.word}</legend><div class="chips">${values.map((v) => `<label class="chip"><input type="radio" name="v" value="${v}" ${v === value ? "checked" : ""}><span>${v}</span></label>`).join("")}</div></fieldset>
      <label class="sr" for="n" style="position:absolute;clip:rect(0 0 0 0);width:1px;height:1px;overflow:hidden">${copy.name}</label>
      <input class="name" id="n" name="n" type="text" maxlength="40" autocomplete="given-name" placeholder="${copy.name}" dir="auto">
      <button class="btn" type="submit" id="make" ${value ? "" : "disabled"}>${copy.make}</button>
    </form>`);
  const input = el.querySelector<HTMLInputElement>("#n")!; input.value = name;
  el.querySelectorAll<HTMLInputElement>('input[name="v"]').forEach((r) => r.addEventListener("change", () => { value = r.value as Value; el.querySelector<HTMLButtonElement>("#make")!.disabled = false; sound.tick(); }));
  el.querySelector("#f")!.addEventListener("submit", (e) => { e.preventDefault(); name = input.value; if (value) poster(); });
}
// the short path inside a place: scroll, arrows or a vertical drag move the camera in a little
function nudge(d: number) { if (state === "place" && !skipMotion) stage.zoomTarget = Math.min(1.16, Math.max(1, stage.zoomTarget + d)); }
addEventListener("wheel", (e) => nudge(e.deltaY * -0.0006), { passive: true });
addEventListener("keydown", (e) => { if ((e.target as HTMLElement).tagName === "INPUT") return; if (e.key === "ArrowUp" || e.key === "PageUp") nudge(0.04); if (e.key === "ArrowDown" || e.key === "PageDown") nudge(-0.04); });
let ty = 0; addEventListener("touchstart", (e) => (ty = e.touches[0].clientY), { passive: true });
addEventListener("touchmove", (e) => { nudge((ty - e.touches[0].clientY) * 0.0006); ty = e.touches[0].clientY; }, { passive: true });

/* ------------------------------------------------------------------ 4. the poster */
async function poster() {
  if (!value) return;
  state = "poster"; stage.zoomTarget = 1.1;
  const el = scene(`<canvas id="art" role="img"></canvas><div><div class="actions">
      <button class="btn" type="button" id="dl">${copy.download}</button>
      <button class="btn ghost" type="button" id="sh">${copy.share}</button>
      <button class="btn ghost" type="button" id="again">${copy.again}</button></div><p class="note" id="note" role="status"></p></div>`, "reveal");
  const canvas = el.querySelector<HTMLCanvasElement>("#art")!; const note = el.querySelector("#note")!;
  canvas.setAttribute("aria-label", `لوحة: ${name ? name + "، " : ""}${place.name}، ${value}`);
  void stage.tween("uLife", 0.4, 800);
  try { await drawPoster(canvas, place, value, name); } catch { note.textContent = "تعذّر إنشاء اللوحة. حاول مرة أخرى."; return; }
  const file = `hekayatna-${place.id}.png`;
  el.querySelector("#dl")!.addEventListener("click", async () => { download(await toBlob(canvas), file); note.textContent = "تم حفظ اللوحة (1080 × 1920)."; });
  el.querySelector("#sh")!.addEventListener("click", async () => {
    const blob = await toBlob(canvas); const r = await share(blob, file, `${copy.title} · ${copy.occasion}`);
    if (r === "unsupported") { download(blob, file); note.textContent = "المشاركة المباشرة غير مدعومة في هذا المتصفح، فحفظنا اللوحة لتشاركها بنفسك."; }
  });
  el.querySelector("#again")!.addEventListener("click", () => { void stage.tween("uLife", 1, 600); travel(opening(1), select); });
}

/* ------------------------------------------------------------------ chrome */
$("#back").addEventListener("click", () => {
  if (busy) return;
  if (state === "poster") { void stage.tween("uLife", 1, 600); arrive(); }
  else if (state === "place") travel(opening(1), select);
  else if (state === "select") travel(opening(0), intro);
});
$("#sound").addEventListener("click", async (e) => { const on = await sound.toggle(); const b = e.currentTarget as HTMLElement; b.setAttribute("aria-pressed", String(on)); b.textContent = on ? "الصوت: يعمل" : "الصوت: مغلق"; });
$("#skip").addEventListener("click", (e) => { skipMotion = !skipMotion; stage.reduced = skipMotion; if (!skipMotion) void stage.tween("uLife", 1, 300); (e.currentTarget as HTMLElement).setAttribute("aria-pressed", String(skipMotion)); });
$("#skip").setAttribute("aria-pressed", String(skipMotion));
$("#about-text").textContent = copy.independent;
$("#about-credits").innerHTML = places.map((p) => `<li><b>${p.name}:</b> ${p.credit.full}</li>`).join("");
$("#info").addEventListener("click", (e) => { const p = $("#about"); p.hidden = !p.hidden; (e.currentTarget as HTMLElement).setAttribute("aria-expanded", String(!p.hidden)); });
addEventListener("keydown", (e) => { if (e.key === "Escape" && !$("#about").hidden) { $("#about").hidden = true; $("#info").setAttribute("aria-expanded", "false"); $("#info").focus(); } });
let lastAspect = aspect();
addEventListener("resize", () => { const a = aspect(); if (a === lastAspect || busy) return; lastAspect = a; const v = state === "intro" ? opening(0) : state === "select" ? opening(1) : world(place.id); void show(v); if (state === "select") select(); });

/* ------------------------------------------------------------------ start */
(async () => {
  await show(opening(0)).catch(() => {});
  loading.classList.add("off");
  void stage.tween("uFade", 1, 1600);
  intro();
  setTimeout(() => { prepWalk(); stage.preload(opening(1)); }, 1200);                 // fetched quietly while the visitor reads the title
  // if the watchdog steps the device down a tier, reload the current view at that tier's picture size
  stage.onTier = () => void stage.show(current);
  // capture mode: a fixed, repeatable run for recording (no personal data, same timing every time)
  if (CAPTURE) {
    place = places.find((p) => p.id === (params.get("place") ?? "alula")) ?? places[1]; value = "الطموح"; name = params.get("name") ?? "نورة";
    await wait(3500); await enter(); await wait(2600);
    await travel(world(place.id), arrive); await wait(3200); await poster();
  }
})();
