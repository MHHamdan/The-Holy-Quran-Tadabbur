/**
 * Emotional Guidance — "What does the Quran say when I feel…"
 *
 * A static, therapeutic discovery tool mapping emotional states to
 * relevant Quranic surahs, themes, and duʿā references.
 *
 * Safety: no AI-generated content. All mappings are based on well-known
 * classical scholarly classifications of Quranic themes.
 * No tafsir interpretation — only references to verified content.
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Heart, ChevronRight, ArrowLeft } from 'lucide-react';
import clsx from 'clsx';
import { useLanguageStore } from '../stores/languageStore';
import { SURAH_NAMES } from '../data/surahNames';

interface EmotionalState {
  id: string;
  labelEn: string;
  labelAr: string;
  emoji: string;
  color: string;
  quranResponseEn: string;
  quranResponseAr: string;
  surahs: { surah: number; reasonEn: string; reasonAr: string }[];
  duaRoute: string;
  duaLabelEn: string;
  duaLabelAr: string;
  themeRoute: string;
  themeLabelEn: string;
  themeLabelAr: string;
  affirmatioVerseRef: string;
  affirmationEn: string;
  affirmationAr: string;
}

const EMOTIONAL_STATES: readonly EmotionalState[] = [
  {
    id: 'anxious',
    labelEn: 'Anxious & Worried',
    labelAr: 'قلق ومتوتر',
    emoji: '😰',
    color: 'blue',
    quranResponseEn: 'The Quran addresses anxiety with certainty about divine knowledge and control over all affairs.',
    quranResponseAr: 'يعالج القرآن القلق بتأكيد المعرفة الإلهية والسيطرة على كل الأمور.',
    surahs: [
      { surah: 13, reasonEn: 'Ar-Ra\'d: "Verily, in the remembrance of Allah do hearts find rest" (13:28)', reasonAr: 'الرعد: "أَلَا بِذِكْرِ اللَّهِ تَطْمَئِنُّ الْقُلُوبُ" (13:28)' },
      { surah: 94, reasonEn: 'Ash-Sharh: "With hardship comes ease" (94:5-6)', reasonAr: 'الشرح: "فَإِنَّ مَعَ الْعُسْرِ يُسْرًا" (94:5-6)' },
      { surah: 65, reasonEn: 'At-Talaq: "Allah will bring ease after hardship" (65:7)', reasonAr: 'الطلاق: "سَيَجْعَلُ اللَّهُ بَعْدَ عُسْرٍ يُسْرًا" (65:7)' },
      { surah: 2, reasonEn: 'Al-Baqarah: "Allah does not burden a soul beyond its capacity" (2:286)', reasonAr: 'البقرة: "لَا يُكَلِّفُ اللَّهُ نَفْسًا إِلَّا وُسْعَهَا" (2:286)' },
    ],
    duaRoute: '/duas',
    duaLabelEn: 'Prayer Against Unbearable Burden (2:286)',
    duaLabelAr: 'الدعاء برفع الحمل الثقيل (2:286)',
    themeRoute: '/themes',
    themeLabelEn: 'Browse: Tawakkul (Trust in Allah)',
    themeLabelAr: 'استكشف: موضوع التوكل على الله',
    affirmatioVerseRef: '13:28',
    affirmationEn: 'Indeed, in the remembrance of Allah do hearts find rest.',
    affirmationAr: 'أَلَا بِذِكْرِ اللَّهِ تَطْمَئِنُّ الْقُلُوبُ',
  },
  {
    id: 'sad',
    labelEn: 'Sad & Grieving',
    labelAr: 'حزين وفي حداد',
    emoji: '😢',
    color: 'violet',
    quranResponseEn: 'The Quran offers comfort through the stories of prophets who faced loss and sorrow, and through the promise of eternal joy.',
    quranResponseAr: 'يُقدم القرآن العزاء من خلال قصص الأنبياء الذين واجهوا الخسارة والحزن، ومن خلال وعد الفرح الأبدي.',
    surahs: [
      { surah: 93, reasonEn: 'Ad-Duha: Revelation of divine care in the Prophet\'s ﷺ period of grief (93:1-11)', reasonAr: 'الضحى: وحي الرعاية الإلهية في فترة حزن النبي ﷺ (93:1-11)' },
      { surah: 12, reasonEn: 'Yusuf: Beautiful patience in the face of profound loss', reasonAr: 'يوسف: الصبر الجميل أمام الخسارة العميقة' },
      { surah: 39, reasonEn: 'Az-Zumar: "Do not despair of Allah\'s mercy" (39:53)', reasonAr: 'الزمر: "لَا تَقْنَطُوا مِن رَّحْمَةِ اللَّهِ" (39:53)' },
      { surah: 21, reasonEn: "Al-Anbiya: Ayyub's patience in loss and illness", reasonAr: 'الأنبياء: صبر أيوب في الخسارة والمرض' },
    ],
    duaRoute: '/duas',
    duaLabelEn: "Ayyub's Prayer in Affliction (21:83)",
    duaLabelAr: 'دعاء أيوب في البلاء (21:83)',
    themeRoute: '/themes',
    themeLabelEn: 'Browse: Sabr (Patience)',
    themeLabelAr: 'استكشف: موضوع الصبر',
    affirmatioVerseRef: '93:5',
    affirmationEn: 'And your Lord is going to give you, and you will be satisfied.',
    affirmationAr: 'وَلَسَوْفَ يُعْطِيكَ رَبُّكَ فَتَرْضَىٰ',
  },
  {
    id: 'hopeless',
    labelEn: 'Hopeless & Despairing',
    labelAr: 'فاقد الأمل ويائس',
    emoji: '😔',
    color: 'emerald',
    quranResponseEn: 'The Quran explicitly forbids despair — hope is a theological obligation.',
    quranResponseAr: 'يُحرّم القرآن صراحةً القنوط — الأمل فريضة دينية.',
    surahs: [
      { surah: 39, reasonEn: "Az-Zumar: 'Do not despair of Allah's mercy; He forgives all sins' (39:53)", reasonAr: "الزمر: 'لَا تَقْنَطُوا مِن رَّحْمَةِ اللَّهِ ۚ إِنَّ اللَّهَ يَغْفِرُ الذُّنُوبَ جَمِيعًا' (39:53)" },
      { surah: 94, reasonEn: 'Ash-Sharh: After every hardship comes ease — twice (94:5-6)', reasonAr: 'الشرح: "فَإِنَّ مَعَ الْعُسْرِ يُسْرًا" مرتين (94:5-6)' },
      { surah: 12, reasonEn: 'Yusuf: The revelation that hope persists through decades of trial', reasonAr: 'يوسف: البيان بأن الأمل يدوم رغم عقود من الابتلاء' },
      { surah: 65, reasonEn: 'At-Talaq: "Whoever trusts in Allah — He is sufficient for him" (65:3)', reasonAr: 'الطلاق: "وَمَن يَتَوَكَّلْ عَلَى اللَّهِ فَهُوَ حَسْبُهُ" (65:3)' },
    ],
    duaRoute: '/duas',
    duaLabelEn: "Yunus's Prayer in Darkness (21:87)",
    duaLabelAr: 'دعاء يونس في الظلمات (21:87)',
    themeRoute: '/themes',
    themeLabelEn: 'Browse: Hope (Raja)',
    themeLabelAr: 'استكشف: موضوع الرجاء',
    affirmatioVerseRef: '39:53',
    affirmationEn: "Do not despair of the mercy of Allah. Indeed, Allah forgives all sins.",
    affirmationAr: 'لَا تَقْنَطُوا مِن رَّحْمَةِ اللَّهِ ۚ إِنَّ اللَّهَ يَغْفِرُ الذُّنُوبَ جَمِيعًا',
  },
  {
    id: 'guilty',
    labelEn: 'Guilty & Regretful',
    labelAr: 'مذنب وآسف',
    emoji: '😞',
    color: 'rose',
    quranResponseEn: 'The Quran\'s mercy is wider than any sin. Tawbah (repentance) is the central theme of divine mercy.',
    quranResponseAr: 'رحمة القرآن أوسع من أي ذنب. التوبة هي المحور المركزي للرحمة الإلهية.',
    surahs: [
      { surah: 9, reasonEn: 'At-Tawbah: The entire chapter is about turning back to Allah', reasonAr: 'التوبة: السورة كلها عن الرجوع إلى الله' },
      { surah: 4, reasonEn: 'An-Nisa: "Whoever does wrong and seeks forgiveness will find Allah Forgiving" (4:110)', reasonAr: 'النساء: "وَمَن يَعْمَلْ سُوءًا أَوْ يَظْلِمْ نَفْسَهُ ثُمَّ يَسْتَغْفِرِ اللَّهَ يَجِدِ اللَّهَ غَفُورًا رَّحِيمًا" (4:110)' },
      { surah: 7, reasonEn: "Al-A'raf: Adam & Eve's first repentance — the model for all human remorse", reasonAr: "الأعراف: توبة آدم وحواء — النموذج الأول للندم الإنساني" },
      { surah: 42, reasonEn: 'Ash-Shura: "He accepts repentance from His servants" (42:25)', reasonAr: 'الشورى: "وَهُوَ الَّذِي يَقْبَلُ التَّوْبَةَ عَنْ عِبَادِهِ" (42:25)' },
    ],
    duaRoute: '/duas',
    duaLabelEn: "Adam & Eve's Repentance (7:23)",
    duaLabelAr: 'دعاء آدم وحواء (7:23)',
    themeRoute: '/themes',
    themeLabelEn: 'Browse: Tawbah (Repentance)',
    themeLabelAr: 'استكشف: موضوع التوبة',
    affirmatioVerseRef: '39:53',
    affirmationEn: "Say, 'O My servants who have transgressed against themselves — do not despair of Allah's mercy.'",
    affirmationAr: 'قُلْ يَا عِبَادِيَ الَّذِينَ أَسْرَفُوا عَلَىٰ أَنفُسِهِمْ لَا تَقْنَطُوا مِن رَّحْمَةِ اللَّهِ',
  },
  {
    id: 'grateful',
    labelEn: 'Grateful & Joyful',
    labelAr: 'شاكر وفرح',
    emoji: '😊',
    color: 'amber',
    quranResponseEn: 'Gratitude is multiplied by the Quran — the more you thank, the more you receive.',
    quranResponseAr: 'الشكر يُضاعَف في القرآن — كلما شكرت زادك الله.',
    surahs: [
      { surah: 55, reasonEn: 'Ar-Rahman: A chapter of pure gratitude — "Which of your Lord\'s favors do you deny?"', reasonAr: 'الرحمن: سورة الامتنان الخالص — "فَبِأَيِّ آلَاءِ رَبِّكُمَا تُكَذِّبَانِ"' },
      { surah: 14, reasonEn: "Ibrahim: 'If you are grateful, I will surely increase you' (14:7)", reasonAr: "إبراهيم: 'لَئِن شَكَرْتُمْ لَأَزِيدَنَّكُمْ' (14:7)" },
      { surah: 1, reasonEn: 'Al-Fatihah: The opening of gratitude — al-Ḥamd lillāh', reasonAr: 'الفاتحة: بداية الحمد — الحمد لله' },
      { surah: 93, reasonEn: "Ad-Duha: 'As for the favor of your Lord, proclaim it' (93:11)", reasonAr: "الضحى: 'وَأَمَّا بِنِعْمَةِ رَبِّكَ فَحَدِّثْ' (93:11)" },
    ],
    duaRoute: '/duas',
    duaLabelEn: 'Prayer to Be Grateful (Sulayman, 27:19)',
    duaLabelAr: 'الدعاء لأداء الشكر (سليمان، 27:19)',
    themeRoute: '/themes',
    themeLabelEn: 'Browse: Gratitude & Praise',
    themeLabelAr: 'استكشف: موضوع الشكر والحمد',
    affirmatioVerseRef: '14:7',
    affirmationEn: 'If you are grateful, I will surely increase you in favor.',
    affirmationAr: 'لَئِن شَكَرْتُمْ لَأَزِيدَنَّكُمْ',
  },
  {
    id: 'angry',
    labelEn: 'Angry & Frustrated',
    labelAr: 'غاضب ومحبط',
    emoji: '😤',
    color: 'orange',
    quranResponseEn: 'The Quran celebrates those who control their anger as a mark of righteousness.',
    quranResponseAr: 'يحتفي القرآن بالذين يكظمون غيظهم علامةً على البر.',
    surahs: [
      { surah: 3, reasonEn: "Ali 'Imran: 'Those who suppress their anger and pardon people — Allah loves the doers of good' (3:134)", reasonAr: "آل عمران: 'وَالْكَاظِمِينَ الْغَيْظَ وَالْعَافِينَ عَنِ النَّاسِ ۗ وَاللَّهُ يُحِبُّ الْمُحْسِنِينَ' (3:134)" },
      { surah: 42, reasonEn: "Ash-Shura: 'And those who avoid major sins and immoralities, and when they are angry, they forgive' (42:37)", reasonAr: "الشورى: 'وَالَّذِينَ يَجْتَنِبُونَ كَبَائِرَ الْإِثْمِ... وَإِذَا مَا غَضِبُوا هُمْ يَغْفِرُونَ' (42:37)" },
      { surah: 7, reasonEn: "Al-A'raf: Musa's anger and how he channelled it (7:150-154)", reasonAr: "الأعراف: غضب موسى وكيف وجّهه (7:150-154)" },
      { surah: 16, reasonEn: 'An-Nahl: Patience is better than revenge (16:126)', reasonAr: 'النحل: والصبر خير لمن صبر (16:126)' },
    ],
    duaRoute: '/duas',
    duaLabelEn: 'Seeking Refuge from Shaytan (23:97)',
    duaLabelAr: 'الاستعاذة من الشيطان (23:97)',
    themeRoute: '/themes',
    themeLabelEn: 'Browse: Hilm (Forbearance)',
    themeLabelAr: 'استكشف: موضوع الحلم',
    affirmatioVerseRef: '3:134',
    affirmationEn: 'Those who suppress their anger and pardon people — Allah loves the doers of good.',
    affirmationAr: 'وَالْكَاظِمِينَ الْغَيْظَ وَالْعَافِينَ عَنِ النَّاسِ ۗ وَاللَّهُ يُحِبُّ الْمُحْسِنِينَ',
  },
  {
    id: 'lonely',
    labelEn: 'Lonely & Disconnected',
    labelAr: 'وحيد ومنفصل',
    emoji: '😶',
    color: 'teal',
    quranResponseEn: 'The Quran affirms that Allah is always closer than your jugular vein — you are never truly alone.',
    quranResponseAr: 'القرآن يؤكد أن الله أقرب إليك من حبل الوريد — لا أحد وحيد حقاً.',
    surahs: [
      { surah: 50, reasonEn: 'Qaf: "We are closer to him than his jugular vein" (50:16)', reasonAr: 'ق: "وَنَحْنُ أَقْرَبُ إِلَيْهِ مِنْ حَبْلِ الْوَرِيدِ" (50:16)' },
      { surah: 58, reasonEn: 'Al-Mujadila: "He is with them wherever they are" (58:7)', reasonAr: 'المجادلة: "هُوَ مَعَهُمْ أَيْنَ مَا كَانُوا" (58:7)' },
      { surah: 57, reasonEn: 'Al-Hadid: "He is with you wherever you are" (57:4)', reasonAr: 'الحديد: "وَهُوَ مَعَكُمْ أَيْنَ مَا كُنتُمْ" (57:4)' },
      { surah: 18, reasonEn: 'Al-Kahf: Young believers who found each other and found Allah', reasonAr: 'الكهف: فتية مؤمنون وجدوا بعضهم ووجدوا الله' },
    ],
    duaRoute: '/duas',
    duaLabelEn: 'Prayer for Mercy & Guidance (Companions of Cave, 18:10)',
    duaLabelAr: 'دعاء الرحمة والهداية (أصحاب الكهف، 18:10)',
    themeRoute: '/therapy',
    themeLabelEn: 'Spiritual Guidance Center',
    themeLabelAr: 'مركز التوجيه الروحي',
    affirmatioVerseRef: '50:16',
    affirmationEn: 'We are closer to him than his jugular vein.',
    affirmationAr: 'وَنَحْنُ أَقْرَبُ إِلَيْهِ مِنْ حَبْلِ الْوَرِيدِ',
  },
  {
    id: 'overwhelmed',
    labelEn: 'Overwhelmed & Burned Out',
    labelAr: 'مثقل الكاهل ومحترق',
    emoji: '😩',
    color: 'purple',
    quranResponseEn: 'The Quran teaches the limits of human responsibility — Allah only burdens within capacity.',
    quranResponseAr: 'يُعلّم القرآن حدود المسؤولية البشرية — الله لا يُكلّف إلا بالوسع.',
    surahs: [
      { surah: 2, reasonEn: 'Al-Baqarah: "Allah does not burden a soul beyond its capacity" (2:286)', reasonAr: 'البقرة: "لَا يُكَلِّفُ اللَّهُ نَفْسًا إِلَّا وُسْعَهَا" (2:286)' },
      { surah: 94, reasonEn: 'Ash-Sharh: "With hardship comes ease" (94:5) — ease is inherent in every hardship', reasonAr: 'الشرح: "فَإِنَّ مَعَ الْعُسْرِ يُسْرًا" — اليسر ملازم للعسر' },
      { surah: 20, reasonEn: 'Ta-Ha: "We have not sent down the Quran to cause you distress" (20:2)', reasonAr: 'طه: "مَا أَنزَلْنَا عَلَيْكَ الْقُرْآنَ لِتَشْقَىٰ" (20:2)' },
      { surah: 65, reasonEn: 'At-Talaq: "After hardship, Allah will bring ease" (65:7)', reasonAr: 'الطلاق: "سَيَجْعَلُ اللَّهُ بَعْدَ عُسْرٍ يُسْرًا" (65:7)' },
    ],
    duaRoute: '/duas',
    duaLabelEn: "Prayer Against Unbearable Burden (Baqarah's Closing)",
    duaLabelAr: 'الدعاء برفع الحمل الثقيل (خاتمة البقرة)',
    themeRoute: '/therapy',
    themeLabelEn: 'Spiritual Guidance Center',
    themeLabelAr: 'مركز التوجيه الروحي',
    affirmatioVerseRef: '94:5',
    affirmationEn: 'For indeed, with hardship will be ease.',
    affirmationAr: 'فَإِنَّ مَعَ الْعُسْرِ يُسْرًا',
  },
  {
    id: 'seeking',
    labelEn: 'Spiritually Seeking',
    labelAr: 'باحث روحياً',
    emoji: '🔍',
    color: 'indigo',
    quranResponseEn: 'The Quran was sent precisely for seekers — every verse is a door.',
    quranResponseAr: 'نزل القرآن تحديداً للباحثين — كل آية باب.',
    surahs: [
      { surah: 1, reasonEn: 'Al-Fatihah: The prayer for guidance — the foundation of every seeker', reasonAr: 'الفاتحة: دعاء الهداية — أساس كل باحث' },
      { surah: 2, reasonEn: 'Al-Baqarah: "This is the Book about which there is no doubt, a guidance for the God-conscious" (2:2)', reasonAr: 'البقرة: "ذَٰلِكَ الْكِتَابُ لَا رَيْبَ ۛ فِيهِ ۛ هُدًى لِّلْمُتَّقِينَ" (2:2)' },
      { surah: 10, reasonEn: 'Yunus: "O mankind, there has come to you instruction from your Lord" (10:57)', reasonAr: 'يونس: "يَا أَيُّهَا النَّاسُ قَدْ جَاءَتْكُم مَّوْعِظَةٌ مِّن رَّبِّكُمْ" (10:57)' },
      { surah: 18, reasonEn: "Al-Kahf: The story of Khidr — the seeker's journey to hidden wisdom", reasonAr: 'الكهف: قصة الخضر — رحلة الباحث نحو الحكمة الخفية' },
    ],
    duaRoute: '/duas',
    duaLabelEn: 'Prayer for Guidance (Al-Fatihah, 1:6)',
    duaLabelAr: 'الدعاء للهداية (الفاتحة، 1:6)',
    themeRoute: '/ask',
    themeLabelEn: 'Ask the Tafsir Assistant',
    themeLabelAr: 'اسأل مساعد التفسير',
    affirmatioVerseRef: '2:2',
    affirmationEn: 'This is the Book about which there is no doubt, a guidance for the conscious of Allah.',
    affirmationAr: 'ذَٰلِكَ الْكِتَابُ لَا رَيْبَ ۛ فِيهِ ۛ هُدًى لِّلْمُتَّقِينَ',
  },
];

const COLOR_BG: Record<string, string> = {
  blue:    'bg-blue-100 text-blue-700 border-blue-200 hover:bg-blue-200',
  violet:  'bg-violet-100 text-violet-700 border-violet-200 hover:bg-violet-200',
  emerald: 'bg-emerald-100 text-emerald-700 border-emerald-200 hover:bg-emerald-200',
  rose:    'bg-rose-100 text-rose-700 border-rose-200 hover:bg-rose-200',
  amber:   'bg-amber-100 text-amber-700 border-amber-200 hover:bg-amber-200',
  orange:  'bg-orange-100 text-orange-700 border-orange-200 hover:bg-orange-200',
  teal:    'bg-teal-100 text-teal-700 border-teal-200 hover:bg-teal-200',
  purple:  'bg-purple-100 text-purple-700 border-purple-200 hover:bg-purple-200',
  indigo:  'bg-indigo-100 text-indigo-700 border-indigo-200 hover:bg-indigo-200',
};

const COLOR_AFFIRMATION: Record<string, string> = {
  blue:    'bg-blue-50 border-blue-200 text-blue-900',
  violet:  'bg-violet-50 border-violet-200 text-violet-900',
  emerald: 'bg-emerald-50 border-emerald-200 text-emerald-900',
  rose:    'bg-rose-50 border-rose-200 text-rose-900',
  amber:   'bg-amber-50 border-amber-200 text-amber-900',
  orange:  'bg-orange-50 border-orange-200 text-orange-900',
  teal:    'bg-teal-50 border-teal-200 text-teal-900',
  purple:  'bg-purple-50 border-purple-200 text-purple-900',
  indigo:  'bg-indigo-50 border-indigo-200 text-indigo-900',
};

export function EmotionalGuidancePage() {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';
  const [selected, setSelected] = useState<EmotionalState | null>(null);

  if (selected) {
    const colors = COLOR_BG[selected.color] ?? COLOR_BG.teal;
    const affirmColors = COLOR_AFFIRMATION[selected.color] ?? COLOR_AFFIRMATION.teal;

    return (
      <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8" dir={isRtl ? 'rtl' : 'ltr'}>
        {/* Back button */}
        <button
          onClick={() => setSelected(null)}
          className={clsx('flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 mb-6 transition-colors', isRtl && 'flex-row-reverse')}
        >
          <ArrowLeft className={clsx('w-4 h-4', isRtl && 'rotate-180')} />
          {isRtl ? 'العودة' : 'Back'}
        </button>

        {/* Header */}
        <div className="text-center mb-6">
          <span className="text-5xl mb-3 block">{selected.emoji}</span>
          <h2 className={clsx('text-2xl font-bold text-gray-900 mb-2', isRtl && 'font-arabic')}>
            {isRtl ? selected.labelAr : selected.labelEn}
          </h2>
          <p className={clsx('text-sm text-gray-600 max-w-md mx-auto', isRtl && 'font-arabic')}>
            {isRtl ? selected.quranResponseAr : selected.quranResponseEn}
          </p>
        </div>

        {/* Affirmation verse */}
        <div className={clsx('rounded-2xl border p-5 mb-6 text-center', affirmColors)}>
          <p className="font-arabic text-xl leading-loose mb-2" dir="rtl">
            {selected.affirmationAr}
          </p>
          <p className="text-sm italic text-gray-600">{selected.affirmationEn}</p>
          <p className="text-xs text-gray-400 mt-1">{selected.affirmatioVerseRef}</p>
        </div>

        {/* Relevant Surahs */}
        <div className="mb-5">
          <h3 className={clsx('text-sm font-semibold text-gray-700 mb-3', isRtl && 'font-arabic')}>
            {isRtl ? 'السور ذات الصلة' : 'Relevant Surahs'}
          </h3>
          <div className="space-y-2">
            {selected.surahs.map(({ surah, reasonEn, reasonAr }) => {
              const name = SURAH_NAMES[surah - 1];
              return (
                <Link
                  key={surah}
                  to={`/quran/${surah}`}
                  className={clsx(
                    'flex items-start gap-3 p-3 rounded-xl border transition-colors',
                    colors,
                    isRtl && 'flex-row-reverse'
                  )}
                >
                  <span className="font-bold text-sm flex-shrink-0 mt-0.5">{surah}.</span>
                  <div className="flex-1 min-w-0">
                    <p className={clsx('font-semibold text-sm', isRtl && 'font-arabic text-right')}>
                      {isRtl ? name.ar : name.en}
                    </p>
                    <p className={clsx('text-xs mt-0.5 opacity-80', isRtl && 'font-arabic text-right')}>
                      {isRtl ? reasonAr : reasonEn}
                    </p>
                  </div>
                  <ChevronRight className={clsx('w-4 h-4 flex-shrink-0 mt-1', isRtl && 'rotate-180')} />
                </Link>
              );
            })}
          </div>
        </div>

        {/* Duʿā recommendation */}
        <Link
          to={selected.duaRoute}
          className={clsx('flex items-center gap-3 p-4 rounded-xl border bg-white hover:shadow-sm transition-shadow mb-3', isRtl && 'flex-row-reverse')}
        >
          <span className="text-2xl flex-shrink-0">🤲</span>
          <div className={clsx('flex-1', isRtl && 'text-right')}>
            <p className={clsx('text-xs font-semibold text-gray-500 uppercase', isRtl && 'font-arabic')}>
              {isRtl ? 'الدعاء المُوصى به' : 'Recommended Duʿā'}
            </p>
            <p className={clsx('text-sm text-gray-700', isRtl && 'font-arabic')}>
              {isRtl ? selected.duaLabelAr : selected.duaLabelEn}
            </p>
          </div>
          <ChevronRight className={clsx('w-4 h-4 text-gray-400', isRtl && 'rotate-180')} />
        </Link>

        {/* Theme / resource link */}
        <Link
          to={selected.themeRoute}
          className={clsx('flex items-center gap-3 p-4 rounded-xl border bg-white hover:shadow-sm transition-shadow', isRtl && 'flex-row-reverse')}
        >
          <span className="text-2xl flex-shrink-0">🔍</span>
          <div className={clsx('flex-1', isRtl && 'text-right')}>
            <p className={clsx('text-xs font-semibold text-gray-500 uppercase', isRtl && 'font-arabic')}>
              {isRtl ? 'استكشف أكثر' : 'Explore More'}
            </p>
            <p className={clsx('text-sm text-gray-700', isRtl && 'font-arabic')}>
              {isRtl ? selected.themeLabelAr : selected.themeLabelEn}
            </p>
          </div>
          <ChevronRight className={clsx('w-4 h-4 text-gray-400', isRtl && 'rotate-180')} />
        </Link>

        {/* Attribution */}
        <p className={clsx('text-[10px] text-gray-300 text-center mt-6', isRtl && 'font-arabic')}>
          {isRtl
            ? 'المعاني من ترجمة صحيح إنترناشيونال • لا محتوى مُولَّد بالذكاء الاصطناعي'
            : 'Meanings: Saheeh International · No AI-generated content'}
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8" dir={isRtl ? 'rtl' : 'ltr'}>
      {/* Header */}
      <div className="text-center mb-8">
        <Heart className="w-10 h-10 text-rose-500 mx-auto mb-3" />
        <h1 className={clsx('text-2xl font-bold text-gray-900 mb-2', isRtl && 'font-arabic')}>
          {isRtl ? 'القرآن يتكلم مع حالتك' : 'What the Quran says when you feel…'}
        </h1>
        <p className={clsx('text-sm text-gray-500 max-w-md mx-auto', isRtl && 'font-arabic')}>
          {isRtl
            ? 'اختر ما تشعر به الآن واكتشف ما يقوله القرآن لحالتك'
            : 'Choose how you feel and discover what the Quran says to you'}
        </p>
      </div>

      {/* Emotion grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {EMOTIONAL_STATES.map(state => {
          const colors = COLOR_BG[state.color] ?? COLOR_BG.teal;
          return (
            <button
              key={state.id}
              onClick={() => setSelected(state)}
              className={clsx(
                'flex flex-col items-center gap-2 p-4 rounded-2xl border text-center transition-all hover:shadow-md',
                colors
              )}
            >
              <span className="text-3xl">{state.emoji}</span>
              <span className={clsx('text-sm font-medium leading-tight', isRtl && 'font-arabic')}>
                {isRtl ? state.labelAr : state.labelEn}
              </span>
            </button>
          );
        })}
      </div>

      <p className={clsx('text-[10px] text-gray-300 text-center mt-8', isRtl && 'font-arabic')}>
        {isRtl
          ? 'جميع المراجع من القرآن الكريم • لا اجتهادات من المنصة في الفتاوى'
          : 'All references from the Quran · Platform does not issue rulings'}
      </p>
    </div>
  );
}
