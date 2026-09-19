// Finds freely licensed, high-resolution landscape photos on Wikimedia Commons and saves small previews
// plus a JSON record (title, author, licence, source page). Nothing is used without its licence being recorded.
//
//   node tools/assets/commons.mjs            -> assets-src/commons/candidates.json + previews
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const OUT = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "..", "assets-src", "commons");
const UA = { "User-Agent": "hekayatna-national-day/1.0 (independent studio project; photo research)" };
const QUERIES = {
  najd: ["At-Turaif Diriyah", "Diriyah mud brick", "Ushaiqer heritage village", "Najd traditional architecture Saudi"],
  aseer: ["Rijal Almaa", "Al Soudah Abha mountains", "Asir mountains Saudi Arabia", "Abha landscape"],
  alula: ["Elephant Rock Al-Ula", "Hegra Saudi Arabia", "Al-Ula sandstone", "Mada'in Salih", "AlUla old town"],
};
const OK = /^(cc0|public domain|pd|cc by( |-)?\d|cc by-sa)/i;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
// polite client: one request every two seconds, and back off when the API says slow down
async function api(u) {
  for (let i = 0; i < 5; i++) {
    await sleep(3500 + i * 6000);
    const r = await fetch(u, { headers: UA }); const t = await r.text();
    try { const j = JSON.parse(t); if (!j.error) return j; console.log("  (API error:", String(j.error.code), ")"); continue; } catch { console.log("  (waiting, API said:", t.slice(0, 40), ")"); }
  }
  return {};
}
const strip = (s = "") => s.replace(/<[^>]+>/g, "").replace(/\s+/g, " ").trim();

fs.mkdirSync(OUT, { recursive: true });
const ONLY = process.argv[2];                         // e.g. "alula": search one place and keep the others as they are
const all = ONLY && fs.existsSync(path.join(OUT, "candidates.json")) ? JSON.parse(fs.readFileSync(path.join(OUT, "candidates.json"), "utf8")) : {};
for (const [place, queries] of Object.entries(QUERIES)) {
  if (ONLY && place !== ONLY) continue;
  const seen = new Map();
  for (const q of queries) {
    const u = "https://commons.wikimedia.org/w/api.php?" + new URLSearchParams({ action: "query", format: "json", generator: "search", gsrsearch: q, gsrnamespace: "6", gsrlimit: "30", prop: "imageinfo", iiprop: "url|size|extmetadata", iiurlwidth: "560" });
    const j = await api(u);
    for (const p of Object.values(j.query?.pages ?? {})) {
      const i = p.imageinfo?.[0]; if (!i) continue;
      const lic = strip(i.extmetadata?.LicenseShortName?.value);
      if (/Earth Science|NASA|ISS Expedition/i.test(strip(i.extmetadata?.Artist?.value) + strip(i.extmetadata?.ImageDescription?.value))) continue;   // photos from orbit are not what we need
      if (i.width < 2400 || i.width / i.height < 1.3 || i.width / i.height > 2.2 || !OK.test(lic) || !/\.jpe?g(\?|$)/i.test(i.url)) continue;
      seen.set(p.title, { title: p.title, w: i.width, h: i.height, licence: lic, author: strip(i.extmetadata?.Artist?.value).slice(0, 80), page: i.descriptionurl, url: i.url, thumb: i.thumburl, desc: strip(i.extmetadata?.ImageDescription?.value).slice(0, 110) });
    }
  }
  // free-est licences first, then the largest pictures
  const rank = (l) => (/cc0|public|^pd/i.test(l) ? 0 : /by-sa/i.test(l) ? 2 : 1);
  all[place] = [...seen.values()].sort((a, b) => rank(a.licence) - rank(b.licence) || b.w - a.w).slice(0, 12);
  let k = 0;
  for (const c of all[place]) { await sleep(700); c.preview = `${place}-${String(k++).padStart(2, "0")}.jpg`; fs.writeFileSync(path.join(OUT, c.preview), Buffer.from(await (await fetch(c.thumb, { headers: UA })).arrayBuffer())); }
  console.log(`\n## ${place}: ${all[place].length}`);
  for (const c of all[place]) console.log(`${c.preview} ${c.w}x${c.h} [${c.licence}] ${c.author.slice(0, 28)} | ${c.desc.slice(0, 70)}`);
}
fs.writeFileSync(path.join(OUT, "candidates.json"), JSON.stringify(all, null, 1));
