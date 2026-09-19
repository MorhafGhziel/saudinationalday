# حكايتنا واحدة · One Shared Story

An independent SIMA Studio piece for the 96th Saudi National Day (23 September 2026). It is **not** an official government experience and does not use the official identity or its slogan. The scenes are artistic interpretations of places, not reconstructions of real sites.

## Run it

```bash
npm install
npm run dev        # http://localhost:3900
npm run build      # type-check + production build into dist/
```

## What the visitor does

Threshold (title, one button) → a rendered walk out through the rock (video) → choose a place standing in the landscape → mist carries you into it → pick one word and an optional name → a 1080 × 1920 poster to download or share. No account, no form data leaves the browser.

**The places:** all three can be entered. **Najd, AlUla and Aseer are real photographs** (At-Turaif in Diriyah, Elephant Rock, the Sarawat mountains) from Wikimedia Commons under CC BY licences, credited on screen, in the info panel and on every poster. `tools/assets/photo_world.py` crops and grades them and estimates a depth map from each picture (sky found by colour, ground receding to the horizon or to a lane's vanishing point), so they get the same parallax, mist and poster treatment as a render. Two earlier attempts to build Najd and Aseer as 3D scenes looked like blocks and toy hills and were dropped; their scripts remain in `tools/blender/destination.py` for reference only. The opening world is still a Blender render. Adding a place = one entry in `src/data.ts`, one in `photo_world.py`.

## How it is made, and why it runs on weak devices

Nothing 3D runs in the browser. Blender is only used offline to make pictures and one short video.

- The worlds are **Blender 5.2 Cycles renders**, built by scripts in `tools/blender/` from CC0 scans and textures plus procedural rock, dunes and date palms. Each view is rendered twice from the same camera: the picture, and a small **data image** (R = √inverse depth, G = palm-frond mask).
- **The walk through the rock is an ordinary muted H.264 video** (105 frames, 30 fps, 3.5 s, about 2.4 MB, landscape and portrait versions). The camera ease is baked into the render, and every phone decodes it in hardware. It replaced a 36-frame image sequence that was choppy and re-uploaded a full image to the GPU every frame.
- The live scenes draw **one full-screen rectangle**. What it does depends on a quality tier (`src/stage.ts`):

| Tier | Who gets it | What runs | Cost |
|---|---|---|---|
| 2 full | desktops and laptops with a real GPU | parallax (3 steps), frond sway, dust hidden by depth, birds, mist, grain | up to 2.3 MP, 60 fps |
| 1 lite | every phone and tablet, 4-core or ≤ 4 GB machines | parallax (1 step), frond sway, mist | up to 1.0 MP, 30 fps, smaller pictures |
| 0 still | no WebGL, data-saver, ≤ 1 GB devices, lost GPU context | the render as a plain image, a CSS veil for travel | no GPU work at all |

- Resolution is a **pixel budget**, not a device ratio, so a 4K or 3× phone screen never renders more pixels than the tier allows.
- A **watchdog** averages real frame times and steps a device down a tier (never up) if it cannot keep pace, then reloads the picture at that tier's size. `?q=0|1|2` forces a tier for testing.
- Only the world on screen stays in GPU memory; the loop stops when the tab is hidden.
- It is **not** a free-roaming real-time 3D scene, and the zoom inside a place is a depth-parallax move, not a new camera render.

**Measured (headless Chromium on this PC, not real phones):** with a GPU, all tiers hold 16.7 ms page frames. With Chrome's software renderer (no GPU at all, a stand-in for a very weak device) the full tier needs 26–45 ms per frame, the watchdog drops it to lite within a few seconds, and lite then holds a steady 16.7 ms. First screen on a phone is about 0.35 MB of imagery, plus the 2.4 MB video fetched in the background while the title is read.

## Accessibility and fallbacks

Real HTML controls everywhere, visible focus, arrow keys in the place picker, Escape closes the info panel. `prefers-reduced-motion` (or the «تخطي الحركة» button) removes the walk, sway, dust, birds and drift and shortens transitions; the whole flow still works. If WebGL is missing or the context is lost, the page shows the same renders as still images and keeps every step. Sound is off until the visitor turns it on. No device-motion permission is ever requested.

## Recording the TikTok

`http://localhost:3900/?capture=1` plays the same run every time with a fixed example (name «نورة», AlUla, «الطموح»), with the toolbar and hints hidden. Optional: `&name=...`. Record a phone-sized portrait window (e.g. 430 × 932). Timeline: 0 s threshold → 3.5 s walk → ~8 s arrival → ~10.5 s mist into AlUla → ~15 s the word → poster. The title sits in the lower third and the poster in the centre, clear of TikTok's right-hand buttons and caption area.

## Tested

Headless Chromium with GPU (viewport emulation, **not real phones**): 1440 × 900, 1920 × 1080, 768 × 1024, 430 × 932, 390 × 844, 375 × 812. Full journey on desktop and phone with zero console errors; poster export verified as a 1080 × 1920 PNG with Arabic + Latin name and with an empty name; share falls back to download where the Web Share API cannot send files; unfinished places are locked; no horizontal overflow; reduced-motion run and no-WebGL run both complete. `tsc` and `vite build` pass.

**Not verified:** real iOS/Android devices and in-app browsers (TikTok, Instagram), frame rate on low-end phones, and the sound (it is synthesised by code and has not been judged by ear).

## This PC

Windows here has **no page file**, so memory reservations fail long before RAM is full, and GPU memory counts against the same limit. Renders only work with `CYCLES_CONCURRENT_STATES_FACTOR=0.2` and `--factory-startup` (see `tools/blender/render_opening.sh`). Turning on a system-managed page file would remove this whole class of out-of-memory errors.

See `ASSETS.md` for every source and licence.
