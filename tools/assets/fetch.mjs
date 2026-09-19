// Downloads the CC0 source assets from Poly Haven (https://polyhaven.com, licence CC0 1.0, no account needed)
// into assets-src/polyhaven/. The binaries are git-ignored; this script and ASSETS.md are the record.
//
//   node tools/assets/fetch.mjs
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "..", "assets-src", "polyhaven");
const API = "https://api.polyhaven.com";

const MODELS = { namaqualand_cliff_01: "4k", namaqualand_cliff_02: "2k", namaqualand_boulders_01: "2k", namaqualand_boulder_02: "2k", namaqualand_boulder_04: "2k", namaqualand_rocks_01: "2k", rock_face_01: "2k", rock_face_02: "2k", mountainside: "2k" };
const TEXTURES = { red_sandstone_wall: "2k", sandstone_cracks: "2k", worn_rock_natural_01: "2k", red_sand: "2k", sand_01: "2k", sand_03: "2k", rock_wall_08: "2k", clay_plaster: "2k", patterned_clay_plaster: "2k", dry_ground_rocks: "2k", rocky_terrain_02: "2k" };
const HDRIS = { qwantani_late_afternoon_puresky: "4k", kloppenheim_06_puresky: "4k", kloofendal_48d_partly_cloudy_puresky: "4k", kloofendal_28d_misty_puresky: "4k" };

// the CDN sometimes times out on connect: retry a few times before giving up
async function retry(url, tries = 6) {
  for (let i = 0; ; i++) {
    try { const r = await fetch(url); if (!r.ok) throw new Error(`${r.status} ${url}`); return r; }
    catch (e) { if (i >= tries) throw e; await new Promise((ok) => setTimeout(ok, 1500 * (i + 1))); }
  }
}
async function get(url, file) {
  if (fs.existsSync(file) && fs.statSync(file).size > 0) return false;
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const r = await retry(url);
  const tmp = file + ".part";
  fs.writeFileSync(tmp, Buffer.from(await r.arrayBuffer()));
  fs.renameSync(tmp, file);
  return true;
}
const files = async (id) => (await retry(`${API}/files/${id}`)).json();
const log = [];

for (const [id, res] of Object.entries(MODELS)) {
  const f = await files(id);
  const g = f.gltf?.[res]?.gltf ?? f.gltf?.["2k"]?.gltf;
  const dir = path.join(ROOT, "models", id);
  await get(g.url, path.join(dir, path.basename(g.url)));
  for (const [rel, inc] of Object.entries(g.include ?? {})) await get(inc.url, path.join(dir, rel));
  log.push(`model   ${id} (${res})`);
  console.log("model", id);
}
for (const [id, res] of Object.entries(TEXTURES)) {
  const f = await files(id);
  const dir = path.join(ROOT, "textures", id);
  for (const map of ["Diffuse", "nor_gl", "Rough", "Displacement", "AO"]) {
    const m = f[map]?.[res]?.jpg ?? f[map]?.[res]?.png;
    if (m) await get(m.url, path.join(dir, path.basename(m.url)));
  }
  log.push(`texture ${id} (${res})`);
  console.log("texture", id);
}
for (const [id, res] of Object.entries(HDRIS)) {
  const f = await files(id);
  const h = f.hdri?.[res]?.hdr ?? f.hdri?.[res]?.exr;
  await get(h.url, path.join(ROOT, "hdris", path.basename(h.url)));
  log.push(`hdri    ${id} (${res})`);
  console.log("hdri", id);
}
fs.writeFileSync(path.join(ROOT, "_fetched.txt"), log.join("\n") + "\n");
