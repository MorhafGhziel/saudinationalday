import { copy, posterLine, type Place, type Value } from "./data";

/**
 * The poster is its own composition, drawn at full size on a canvas: the place's portrait render,
 * a scrim, and type set for print-like hierarchy. Nothing from the interface is captured.
 * Names are drawn with fillText, so whatever the visitor types is only ever plain text.
 */
export const POSTER = { w: 1080, h: 1920 };

const load = (src: string) => new Promise<HTMLImageElement>((ok, no) => { const i = new Image(); i.onload = () => ok(i); i.onerror = () => no(new Error("image " + src)); i.src = src; });

function fitText(ctx: CanvasRenderingContext2D, text: string, font: (px: number) => string, max: number, start: number, min: number) {
  let px = start;
  for (; px > min; px -= 4) { ctx.font = font(px); if (ctx.measureText(text).width <= max) break; }
  ctx.font = font(px);
  return px;
}

export async function drawPoster(canvas: HTMLCanvasElement, place: Place, value: Value, rawName: string) {
  const { w, h } = POSTER;
  canvas.width = w; canvas.height = h;
  const ctx = canvas.getContext("2d")!;
  const name = rawName.replace(/\s+/g, " ").trim().slice(0, 40);
  await Promise.all([document.fonts.load('700 120px "Aref Ruqaa"', "حكايتي"), document.fonts.load('500 40px "Tajawal"', "اليوم"), document.fonts.load('700 40px "Tajawal"', "اليوم")]);
  const img = await load(`/worlds/${place.id}/port-still0.webp`);

  // picture: cover, anchored a little high so the horizon sits in the upper half and the type gets quiet ground
  const s = Math.max(w / img.width, h / img.height); const dw = img.width * s, dh = img.height * s;
  ctx.drawImage(img, (w - dw) / 2, (h - dh) * 0.35, dw, dh);
  const top = ctx.createLinearGradient(0, 0, 0, 520); top.addColorStop(0, "rgba(12,9,6,0.62)"); top.addColorStop(1, "rgba(12,9,6,0)");
  ctx.fillStyle = top; ctx.fillRect(0, 0, w, 520);
  const bot = ctx.createLinearGradient(0, h - 1080, 0, h); bot.addColorStop(0, "rgba(12,9,6,0)"); bot.addColorStop(0.55, "rgba(12,9,6,0.72)"); bot.addColorStop(1, "rgba(12,9,6,0.92)");
  ctx.fillStyle = bot; ctx.fillRect(0, h - 1080, w, 1080);

  ctx.direction = "rtl"; ctx.textAlign = "center"; ctx.textBaseline = "alphabetic";
  const cx = w / 2, ivory = "#f4ead8", amber = "#e0b072";

  // occasion, top
  ctx.fillStyle = ivory; ctx.font = '500 38px "Tajawal"'; ctx.fillText(copy.occasion, cx, 150);
  ctx.strokeStyle = amber; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(cx - 44, 186); ctx.lineTo(cx + 44, 186); ctx.stroke();

  // name (optional): Latin names keep their own direction inside the RTL line
  let y = h - 640;
  if (name) {
    ctx.fillStyle = ivory;
    fitText(ctx, name, (px) => `500 ${px}px "Tajawal"`, w - 200, 64, 34);
    ctx.fillText(name, cx, y);
    y += 40;
    ctx.strokeStyle = "rgba(244,234,216,0.35)"; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.moveTo(cx - 120, y); ctx.lineTo(cx + 120, y); ctx.stroke();
  }
  // place
  ctx.fillStyle = ivory; fitText(ctx, place.name, (px) => `700 ${px}px "Aref Ruqaa"`, w - 150, 196, 110); ctx.fillText(place.name, cx, h - 400);
  // value line
  ctx.fillStyle = amber; fitText(ctx, posterLine(value), (px) => `400 ${px}px "Aref Ruqaa"`, w - 220, 104, 60); ctx.fillText(posterLine(value), cx, h - 262);
  // project name and credit, small
  ctx.fillStyle = "rgba(244,234,216,0.82)"; ctx.font = '500 34px "Tajawal"'; ctx.fillText(copy.title, cx, h - 150);
  ctx.fillStyle = "rgba(244,234,216,0.55)"; ctx.font = '400 26px "Tajawal"'; ctx.fillText(copy.credit, cx, h - 96);
  // photographs carry their credit wherever the poster travels, as CC BY asks
  ctx.fillStyle = "rgba(244,234,216,0.42)"; ctx.font = '400 19px "Tajawal"'; ctx.fillText(place.credit.short, cx, h - 52);
}

export const toBlob = (c: HTMLCanvasElement) => new Promise<Blob>((ok, no) => c.toBlob((b) => (b ? ok(b) : no(new Error("export failed"))), "image/png"));

export function download(blob: Blob, filename: string) {
  const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = filename;
  document.body.append(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 4000);
}

/** Native share sheet when the device can share files; otherwise the caller falls back to download. */
export async function share(blob: Blob, filename: string, text: string): Promise<"shared" | "cancelled" | "unsupported"> {
  const file = new File([blob], filename, { type: "image/png" });
  if (!navigator.canShare?.({ files: [file] })) return "unsupported";
  try { await navigator.share({ files: [file], text }); return "shared"; } catch (e) { return (e as Error).name === "AbortError" ? "cancelled" : "unsupported"; }
}
