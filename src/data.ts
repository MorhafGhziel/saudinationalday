/** Places, values and copy. Adding a place = one entry here + its assets in public/worlds/<id>/. */
export type PlaceId = "najd" | "alula" | "aseer";

export type Place = {
  id: PlaceId;
  name: string;          // as written on the poster
  region: string;        // small label
  line: string;          // one quiet sentence shown on arrival
  mist: [number, number, number];   // colour of the air we travel through to get there
  ready: boolean;        // false = shown as "coming soon"
  anchor: { land: [number, number]; port: [number, number] };  // where its label sits over the vista (0..1, from top-left)
  focus: { land: [number, number]; port: [number, number] };   // the point the short "look closer" move heads for
  /** Where the picture comes from. Photographs are credited on the site and on the poster, as their licences ask. */
  credit: { short: string; full: string; href?: string };
};

export const places: Place[] = [
  {
    id: "najd", name: "الرياض", region: "نجد · الدرعية", line: "جدران من طين تحفظ الظل، وممر يقود إلى أول الحكاية.", mist: [0.93, 0.80, 0.62], ready: true,
    anchor: { land: [0.70, 0.46], port: [0.72, 0.40] }, focus: { land: [0.62, 0.5], port: [0.42, 0.5] },
    credit: { short: "الصورة: Radosław Botev · CC BY 3.0 PL", full: "حي الطريف في الدرعية. تصوير Radosław Botev، ويكيميديا كومنز، رخصة CC BY 3.0 PL. عُدّلت الألوان والقص.", href: "https://commons.wikimedia.org/wiki/File:At-Turaif_District_in_ad-Dir%27iyah_(3).jpg" },
  },
  {
    id: "alula", name: "العلا", region: "جبل الفيل", line: "صخر نحتته الريح آلاف السنين، وضوء يكمل النحت.", mist: [0.96, 0.78, 0.58], ready: true,
    anchor: { land: [0.36, 0.34], port: [0.40, 0.30] }, focus: { land: [0.36, 0.5], port: [0.5, 0.45] },
    credit: { short: "الصورة: Richard Mortel · CC BY 2.0", full: "جبل الفيل في العلا. تصوير Richard Mortel، ويكيميديا كومنز، رخصة CC BY 2.0. عُدّلت الألوان والقص.", href: "https://commons.wikimedia.org/wiki/File:Elephant_Rock_2020.jpg" },
  },
  {
    id: "aseer", name: "عسير", region: "جبال السروات", line: "جبال فوق الغيم، وقمم تتتابع حتى آخر النظر.", mist: [0.82, 0.87, 0.90], ready: true,
    anchor: { land: [0.16, 0.50], port: [0.20, 0.47] }, focus: { land: [0.5, 0.6], port: [0.5, 0.62] },
    credit: { short: "الصورة: Richard Mortel · CC BY 2.0", full: "جبال السروات في منطقة عسير. تصوير Richard Mortel، ويكيميديا كومنز، رخصة CC BY 2.0. عُدّلت الألوان والقص.", href: "https://commons.wikimedia.org/wiki/File:Sarawat_Mountains,_Asir_Region,_Saudi_Arabia_(9).jpg" },
  },
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
  independent: "مشروع إبداعي مستقل من استوديو سِمة، وليس تجربة رسمية. مشهد البداية تصوّر فني مصنوع ببرنامج Blender، والأماكن الثلاثة صور حقيقية برخص مفتوحة مع ذكر أصحابها.",
};

/** «والطموح حكايتي» */
export const posterLine = (v: Value) => `و${v} حكايتي`;
