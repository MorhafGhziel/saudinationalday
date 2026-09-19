/** Places, values and copy. Adding a place = one entry here + its assets in public/worlds/<id>/. */
export type PlaceId = "najd" | "alula" | "aseer" | "jeddah" | "makkah" | "madinah" | "sharqiyah";

export type Place = {
  id: PlaceId;
  name: string;          // as written on the poster
  region: string;        // small label
  line: string;          // one quiet sentence shown on arrival
  mist: [number, number, number];   // colour of the air we travel through to get there
  ready: boolean;        // false = shown as "coming soon"
  anchor?: { land: [number, number]; port: [number, number] };  // unused since the picker became a row of names
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
  {
    id: "jeddah", name: "جدة", region: "البلد التاريخية", line: "رواشين من خشب تطل على أزقة البلد، وبحر قريب يكمل الحكاية.", mist: [0.90, 0.86, 0.80], ready: true,
    focus: { land: [0.45, 0.5], port: [0.5, 0.45] },
    credit: { short: "الصورة: xiquinhosilva · CC BY 4.0", full: "رواشين في جدة التاريخية (البلد). تصوير xiquinhosilva، ويكيميديا كومنز، رخصة CC BY 4.0. عُدّلت الألوان والقص.", href: "https://commons.wikimedia.org/wiki/File:Old_Jeddah_-_55362178648.jpg" },
  },
  {
    id: "makkah", name: "مكة المكرمة", region: "جبل النور", line: "جبل النور، شامخاً فوق أم القرى.", mist: [0.88, 0.86, 0.84], ready: true,
    focus: { land: [0.5, 0.45], port: [0.5, 0.45] },
    credit: { short: "الصورة: Selami Akceylan · CC BY 3.0", full: "جبل النور في مكة المكرمة. تصوير Selami Akceylan، ويكيميديا كومنز، رخصة CC BY 3.0. عُدّلت الألوان والقص.", href: "https://commons.wikimedia.org/wiki/File:HAC_2010_MEKKE_NUR_DAGINA_BAKIS_-_panoramio_(1).jpg" },
  },
  {
    id: "madinah", name: "المدينة المنورة", region: "جبل أحد", line: "سكينة المدينة، وجبل أحد يطل عليها من بعيد.", mist: [0.90, 0.84, 0.78], ready: true,
    focus: { land: [0.5, 0.55], port: [0.45, 0.6] },
    credit: { short: "الصورة: Ahmed · CC BY 4.0", full: "جبل أحد ومسجد سيد الشهداء في المدينة المنورة. تصوير Ahmed، ويكيميديا كومنز، رخصة CC BY 4.0. عُدّلت الألوان والقص.", href: "https://commons.wikimedia.org/wiki/File:Mount_Uhud,_Medina,_20241002_091239_125.jpg" },
  },
  {
    id: "sharqiyah", name: "الشرقية", region: "كورنيش الدمام", line: "نخيل وبحر هادئ، وصباح يبدأ من الخليج.", mist: [0.86, 0.90, 0.92], ready: true,
    focus: { land: [0.55, 0.5], port: [0.5, 0.5] },
    credit: { short: "الصورة: Radosław Botev · CC BY 3.0 PL", full: "كورنيش الدمام. تصوير Radosław Botev، ويكيميديا كومنز، رخصة CC BY 3.0 PL. عُدّلت الألوان والقص.", href: "https://commons.wikimedia.org/wiki/File:Dammam_Corniche_(2).jpg" },
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
  independent: "مشروع إبداعي مستقل من استوديو سِمة، وليس تجربة رسمية. مشهد البداية تصوّر فني مصنوع ببرنامج Blender، والأماكن السبعة صور حقيقية برخص مفتوحة مع ذكر أصحابها.",
};

/** «والطموح حكايتي» */
export const posterLine = (v: Value) => `و${v} حكايتي`;
