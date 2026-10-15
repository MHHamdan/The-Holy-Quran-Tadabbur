/**
 * App information architecture: five top-level tabs and the hub contents.
 *
 *   Read      → /continue (the last reading position; a second tap opens /quran)
 *   Explore   → /explore  (ExploreHubPage)
 *   Tadabbur  → /ask      (reflection tools are listed in the More sheet)
 *   Memorise  → /memorise (MemoriseHubPage)
 *   More      → More sheet on phones and desktop, /more as a full page
 *
 * Every user-facing route is listed exactly once below, so it is reachable in
 * at most two taps (tab → hub item). Developer and admin pages (/status,
 * /admin/*, /themes/admin) are deliberately absent.
 */
import type { LucideIcon } from 'lucide-react';
import {
  AlarmClock,
  BarChart2,
  Baby,
  Book,
  BookCopy,
  BookOpen,
  BookOpenCheck,
  Bookmark,
  CalendarCheck,
  CalendarDays,
  Calculator,
  Clock,
  Columns3,
  Compass,
  FileText,
  FlipHorizontal2,
  Flame,
  GitCompare,
  Globe,
  GraduationCap,
  HandHeart,
  Heart,
  Info,
  LayoutGrid,
  Layers,
  Library,
  Map,
  MapPin,
  Megaphone,
  MessageCircle,
  Mic,
  Network,
  PenLine,
  Plane,
  RefreshCw,
  Repeat,
  Scale,
  Scroll,
  Search,
  ShieldCheck,
  Sigma,
  Smile,
  Sparkles,
  Star,
  Trophy,
  Users,
  Video,
  Wind,
  Wrench,
} from 'lucide-react';

export interface Bilingual {
  ar: string;
  en: string;
}

export interface NavLink {
  path: string;
  icon: LucideIcon;
  title: Bilingual;
  desc?: Bilingual;
}

export interface NavSection {
  id: string;
  /** translations.ts key for the section heading */
  titleKey: string;
  items: NavLink[];
}

export type TabId = 'read' | 'explore' | 'tadabbur' | 'memorise' | 'more';

export interface NavTab {
  id: TabId;
  /** translations.ts key */
  labelKey: string;
  icon: LucideIcon;
  /** Destination of the tab. `null` means the tab opens the More sheet. */
  to: string | null;
  /** Path prefixes that belong to this tab (used for aria-current). */
  match: string[];
}

// ---------------------------------------------------------------------------
// Hub contents
// ---------------------------------------------------------------------------

export const READ_ITEMS: NavLink[] = [
  {
    path: '/mushaf',
    icon: BookOpenCheck,
    title: { ar: 'المصحف', en: 'Mushaf' },
    desc: { ar: 'اقرأ صفحات المصحف صفحةً صفحة', en: 'Read the Mushaf page by page' },
  },
  {
    path: '/quran',
    icon: BookCopy,
    title: { ar: 'فهرس السور والأجزاء', en: 'Surah and juz index' },
    desc: { ar: 'انتقل إلى أي سورة أو جزء', en: 'Jump to any surah or juz' },
  },
];

export const EXPLORE_ITEMS: NavLink[] = [
  {
    path: '/search',
    icon: Search,
    title: { ar: 'البحث في القرآن', en: 'Quran search' },
    desc: { ar: 'ابحث عن كلمة أو موضوع في نص القرآن والتفاسير', en: 'Find a word or topic in the Quran text and tafsir' },
  },
  {
    path: '/stories',
    icon: Book,
    title: { ar: 'قصص القرآن', en: 'Quran stories' },
    desc: { ar: 'قصص القرآن ومواضعها في السور', en: 'Quranic stories and where they appear' },
  },
  {
    path: '/prophets',
    icon: Users,
    title: { ar: 'أطلس الأنبياء', en: 'Prophets atlas' },
    desc: { ar: 'الأنبياء المذكورون في القرآن مع مواضع ذكرهم', en: 'Prophets mentioned in the Quran, with their references' },
  },
  {
    path: '/themes',
    icon: Compass,
    title: { ar: 'محاور القرآن', en: 'Quranic themes' },
    desc: { ar: 'تصنيف موضوعي لآيات القرآن', en: 'Verses grouped by theme' },
  },
  {
    path: '/concepts',
    icon: Network,
    title: { ar: 'المفاهيم القرآنية', en: 'Quranic concepts' },
    desc: { ar: 'الأشخاص والأماكن والأحداث وصلاتها', en: 'People, places and events and how they connect' },
  },
  {
    path: '/surah-atlas',
    icon: Layers,
    title: { ar: 'أطلس السور', en: 'Surah atlas' },
    desc: { ar: 'نظرة على كل سورة: قصصها وأنبياؤها ومحاورها', en: 'Each surah at a glance: stories, prophets and themes' },
  },
  {
    path: '/tafsir/compare',
    icon: Columns3,
    title: { ar: 'مقارنة التفاسير', en: 'Compare tafsir' },
    desc: { ar: 'اقرأ أقوال المفسرين في الآية جنباً إلى جنب', en: 'Read several tafsir books on one verse side by side' },
  },
  {
    path: '/asma-allah',
    icon: Star,
    title: { ar: 'أسماء الله الحسنى', en: 'Names of Allah' },
    desc: { ar: 'الأسماء الحسنى ومواضعها في القرآن', en: 'The Names of Allah and where they appear in the Quran' },
  },
  {
    path: '/asbab',
    icon: Scroll,
    title: { ar: 'أسباب النزول', en: 'Occasions of revelation' },
    desc: { ar: 'روايات أسباب النزول من كتاب الواحدي', en: "Reports from al-Wahidi's Asbab al-Nuzul" },
  },
  {
    path: '/quranic-calls',
    icon: Megaphone,
    title: { ar: 'أطلس النداءات', en: 'Calls atlas' },
    desc: { ar: 'نداءات القرآن وخطاباته ومن وُجّهت إليه', en: 'The calls and addresses in the Quran and who they address' },
  },
  {
    path: '/timeline',
    icon: AlarmClock,
    title: { ar: 'ترتيب النزول', en: 'Revelation order' },
    desc: { ar: 'السور بترتيب نزولها المشهور', en: 'Surahs in the commonly cited order of revelation' },
  },
  {
    path: '/roots',
    icon: Sigma,
    title: { ar: 'الجذور اللغوية', en: 'Word roots' },
    desc: { ar: 'جذور ثلاثية وعائلاتها في القرآن', en: 'Trilateral roots and their word families' },
  },
  {
    path: '/tools/vocabulary',
    icon: BookOpen,
    title: { ar: 'مفردات القرآن', en: 'Quran vocabulary' },
    desc: { ar: 'معاني الكلمات من المعاجم المذكورة', en: 'Word meanings from the listed lexicons' },
  },
  {
    path: '/miracles',
    icon: Sparkles,
    title: { ar: 'الآيات والمعجزات', en: 'Signs and miracles' },
    desc: { ar: 'المعجزات والآيات المذكورة في القرآن', en: 'Signs and miracles mentioned in the Quran' },
  },
];

export const MEMORISE_ITEMS: NavLink[] = [
  {
    path: '/tasmee',
    icon: Mic,
    title: { ar: 'التسميع', en: 'Tasmeeʿ' },
    desc: { ar: 'يتابع التطبيق تلاوتك كلمةً كلمة تلقائياً، وقد يخطئ', en: 'Word-by-word follow-along of your recitation (automatic, may be wrong)' },
  },
  {
    path: '/flashcards',
    icon: FlipHorizontal2,
    title: { ar: 'بطاقات الحفظ', en: 'Flashcards' },
    desc: { ar: 'استرجاع الآيات آيةً آية مع حفظ تقدمك على جهازك', en: 'Recall verse by verse; progress stays on your device' },
  },
  {
    path: '/memorization',
    icon: RefreshCw,
    title: { ar: 'المتشابهات', en: 'Similar passages' },
    desc: { ar: 'مواضع متشابهة يكثر فيها الخلط عند الحفظ', en: 'Similar passages that are easy to confuse when memorising' },
  },
  {
    path: '/tools/surah-memory-atlas',
    icon: Map,
    title: { ar: 'أطلس حفظ السور', en: 'Surah memory atlas' },
    desc: { ar: 'خريطة السور لمساعدتك على ترتيب الحفظ', en: 'A map of the surahs to help you plan memorisation' },
  },
  {
    path: '/compare',
    icon: GitCompare,
    title: { ar: 'مقارنة السور', en: 'Compare surahs' },
    desc: { ar: 'قارن بين سورتين في الطول والترتيب والقصص', en: 'Compare two surahs: length, order and stories' },
  },
  {
    path: '/quiz',
    icon: Trophy,
    title: { ar: 'اختبار قرآني', en: 'Quran quiz' },
    desc: { ar: 'أسئلة جاهزة، وأسئلة يولّدها الذكاء الاصطناعي — راجع الإجابات في المصدر', en: 'Ready-made and AI-generated questions — check answers against the source' },
  },
];

export const MORE_SECTIONS: NavSection[] = [
  {
    id: 'reflect',
    titleKey: 'more_section_reflect',
    items: [
      {
        path: '/therapy',
        icon: Heart,
        title: { ar: 'رعاية القلب', en: 'Heart care' },
        desc: { ar: 'آيات وأدعية لما تمر به من مشاعر', en: 'Verses and duʿā for what you are going through' },
      },
      {
        path: '/guidance',
        icon: Smile,
        title: { ar: 'ما يقوله القرآن حين تشعر…', en: 'When you feel…' },
        desc: { ar: 'آيات مختارة لمشاعر القلق والحزن والأمل', en: 'Selected verses for anxiety, sadness and hope' },
      },
      {
        path: '/journal',
        icon: PenLine,
        title: { ar: 'مذكرة التأمل', en: 'Reflection journal' },
        desc: { ar: 'ملاحظاتك على الآيات، محفوظة على جهازك', en: 'Your notes on verses, kept on your device' },
      },
      {
        path: '/challenge',
        icon: Flame,
        title: { ar: 'تحدي اليوم', en: 'Daily challenge' },
      },
      {
        path: '/tools/prompt-guide',
        icon: ShieldCheck,
        title: { ar: 'كيف أسأل؟', en: 'How to ask' },
        desc: { ar: 'كيف تكتب سؤالاً واضحاً للمساعد', en: 'How to write a clear question for the assistant' },
      },
    ],
  },
  {
    id: 'reading',
    titleKey: 'more_section_reading',
    items: [
      ...READ_ITEMS,
      { path: '/bookmarks', icon: Bookmark, title: { ar: 'المحفوظات', en: 'Bookmarks' } },
      { path: '/reading-plan', icon: CalendarCheck, title: { ar: 'خطة الختمة', en: 'Khatmah plan' } },
      { path: '/stats', icon: BarChart2, title: { ar: 'إحصائيات القراءة', en: 'Reading stats' } },
    ],
  },
  {
    id: 'daily',
    titleKey: 'more_section_daily',
    items: [
      { path: '/tools/prayer-times', icon: Clock, title: { ar: 'مواقيت الصلاة', en: 'Prayer times' } },
      { path: '/tools/maps', icon: MapPin, title: { ar: 'المساجد واتجاه القبلة', en: 'Mosques and Qibla' } },
      { path: '/tools/calendar', icon: CalendarDays, title: { ar: 'التقويم الهجري', en: 'Hijri calendar' } },
      { path: '/dhikr', icon: Wind, title: { ar: 'عداد الذكر', en: 'Dhikr counter' } },
      { path: '/duas', icon: HandHeart, title: { ar: 'أدعية القرآن', en: 'Quranic duʿā' } },
      { path: '/tools/finance', icon: Calculator, title: { ar: 'حاسبة الزكاة', en: 'Zakat calculator' } },
      { path: '/tools/trips', icon: Plane, title: { ar: 'دليل الحج والعمرة', en: 'Hajj and Umrah guide' } },
      { path: '/tools', icon: Wrench, title: { ar: 'كل الأدوات', en: 'All tools' } },
    ],
  },
  {
    id: 'learn',
    titleKey: 'more_section_learn',
    items: [
      { path: '/learn', icon: GraduationCap, title: { ar: 'مسار التعلم', en: 'Learning path' } },
      { path: '/names', icon: Baby, title: { ar: 'أسماء من القرآن', en: 'Names from the Quran' } },
    ],
  },
  {
    id: 'app',
    titleKey: 'more_section_app',
    items: [
      { path: '/about', icon: Info, title: { ar: 'عن تدبّر', en: 'About Tadabbur' } },
      { path: '/sources', icon: Library, title: { ar: 'المصادر والتراخيص', en: 'Sources & licences' } },
      { path: '/privacy', icon: FileText, title: { ar: 'سياسة الخصوصية', en: 'Privacy policy' } },
      { path: '/licenses', icon: Scale, title: { ar: 'تراخيص البرمجيات والخطوط', en: 'Software and font licences' } },
    ],
  },
];

/** Outside link collections: shown last, with a note that we do not check them. */
export const EXTERNAL_ITEMS: NavLink[] = [
  { path: '/tools/books', icon: BookOpen, title: { ar: 'كتب إسلامية', en: 'Islamic books' } },
  { path: '/tools/videos', icon: Video, title: { ar: 'مرئيات إسلامية', en: 'Islamic videos' } },
  { path: '/tools/web', icon: Globe, title: { ar: 'مواقع إسلامية', en: 'Islamic websites' } },
];

// ---------------------------------------------------------------------------
// Tabs
// ---------------------------------------------------------------------------

const prefixes = (items: NavLink[]) => items.map((i) => i.path);

export const TABS: NavTab[] = [
  {
    id: 'read',
    labelKey: 'nav_read',
    icon: BookOpenCheck,
    to: '/continue',
    match: ['/continue', '/juz', ...prefixes(READ_ITEMS)],
  },
  {
    id: 'explore',
    labelKey: 'nav_explore',
    icon: Compass,
    to: '/explore',
    match: ['/explore', '/story-atlas', '/tafsir', '/similarity', ...prefixes(EXPLORE_ITEMS)],
  },
  {
    id: 'tadabbur',
    labelKey: 'nav_tadabbur',
    icon: MessageCircle,
    to: '/ask',
    match: ['/ask', ...prefixes(MORE_SECTIONS[0].items)],
  },
  {
    id: 'memorise',
    labelKey: 'nav_memorise',
    icon: Repeat,
    to: '/memorise',
    match: ['/memorise', ...prefixes(MEMORISE_ITEMS)],
  },
  {
    id: 'more',
    labelKey: 'nav_more',
    icon: LayoutGrid,
    to: null,
    match: [
      '/more',
      ...MORE_SECTIONS.slice(1).flatMap((s) => prefixes(s.items)),
      ...prefixes(EXTERNAL_ITEMS),
    ],
  },
];

function matches(pathname: string, prefix: string): boolean {
  return pathname === prefix || pathname.startsWith(prefix.endsWith('/') ? prefix : `${prefix}/`);
}

/** The tab a path belongs to: the tab with the longest matching prefix. */
export function activeTabFor(pathname: string): TabId | null {
  let best: { id: TabId; len: number } | null = null;
  for (const tab of TABS) {
    for (const prefix of tab.match) {
      if (matches(pathname, prefix) && (!best || prefix.length > best.len)) {
        best = { id: tab.id, len: prefix.length };
      }
    }
  }
  return best?.id ?? null;
}

/** Routes that render a full-height reading or chat surface: no floating
 *  feedback button there (it covered Quran text and the Ask composer). */
export const READER_ROUTE_PREFIXES = ['/mushaf', '/quran', '/tasmee', '/ask'];

export function isReaderRoute(pathname: string): boolean {
  return READER_ROUTE_PREFIXES.some((p) => matches(pathname, p));
}

/** Every path reachable from the shell, for the reachability test. */
export function allNavPaths(): string[] {
  return [
    ...TABS.map((t) => t.to).filter((p): p is string => !!p),
    ...EXPLORE_ITEMS.map((i) => i.path),
    ...MEMORISE_ITEMS.map((i) => i.path),
    ...MORE_SECTIONS.flatMap((s) => s.items.map((i) => i.path)),
    ...EXTERNAL_ITEMS.map((i) => i.path),
  ];
}
