/** Places, values and copy. Adding a place = one entry here + its rendered assets in public/worlds/<id>/. */
export type PlaceId = "najd" | "alula" | "aseer";

export type Place = {
  id: PlaceId;
  name: string;          // as written on the poster
  region: string;        // small label
  line: string;          // one quiet sentence shown on arrival
  mist: [number, number, number];   // colour of the air we travel through to get there
  ready: boolean;        // false = shown as "coming soon": its world is not finished to the standard of the others
  anchor: { land: [number, number]; port: [number, number] };  // where its label sits over the vista (0..1, from top-left)
};

export const places: Place[] = [
  { id: "najd", name: "الرياض", region: "نجد", line: "طين وظل نخيل، وبيوت تحفظ دفء أهلها.", mist: [0.93, 0.80, 0.62], ready: false, anchor: { land: [0.70, 0.46], port: [0.72, 0.40] } },
  { id: "alula", name: "العلا", region: "الحِجر والوادي", line: "صخر نحتته الريح آلاف السنين، وضوء يكمل النحت.", mist: [0.96, 0.78, 0.58], ready: true, anchor: { land: [0.36, 0.34], port: [0.40, 0.30] } },
  { id: "aseer", name: "عسير", region: "السراة", line: "جبال يلامسها الغيم، ومدرجات خضراء على كتف السماء.", mist: [0.82, 0.87, 0.90], ready: false, anchor: { land: [0.16, 0.50], port: [0.20, 0.47] } },
];

export const values = ["الطموح", "الكرم", "الإبداع", "الأصالة", "الشجاعة"] as const;
export type Value = (typeof values)[number];

export const copy = {
  title: "حكايتنا واحدة",
  sub: "أماكن مختلفة، وحكاية تجمعنا.",
  start: "ابدأ حكايتك",
  hint: "ادخل التجربة",
  ask: "من وين تبدأ حكايتك؟",
  enter: "ادخل المكان",
  word: "وش الكلمة اللي تمثلك؟",
  name: "اسمك (اختياري)",
  make: "اصنع لوحتي",
  occasion: "اليوم الوطني السعودي ٩٦",
  credit: "تجربة من SIMA",
  download: "تحميل التصميم",
  share: "مشاركة",
  again: "جرّب مكان ثاني",
  back: "رجوع",
  soon: "قريباً",
  soonLine: "نعمل على هذا المكان ليظهر بالمستوى نفسه. قريباً.",
  // honest labels
  independent: "مشروع إبداعي مستقل من استوديو سِمة، وليس تجربة رسمية. المشاهد تصوّر فني مستلهم من المكان، لا توثيق له.",
};

/** «والطموح حكايتي» */
export const posterLine = (v: Value) => `و${v} حكايتي`;
