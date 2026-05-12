import { useState } from 'react';
import { Sun, Sunset, Star, ChevronDown, ChevronUp } from 'lucide-react';
import { useLanguageStore } from '../../stores/languageStore';
import clsx from 'clsx';

interface Practice {
  arabic: string;
  transliteration: string;
  translation_en: string;
  translation_ar: string;
  count: string;
  benefit_en: string;
  benefit_ar: string;
}

const MORNING_PRACTICES: Practice[] = [
  {
    arabic: 'أَصْبَحْنَا وَأَصْبَحَ الْمُلْكُ لِلَّهِ، وَالْحَمْدُ لِلَّهِ، لَا إِلَهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ',
    transliteration: "Aṣbaḥnā wa aṣbaḥal-mulku lillāh, walḥamdulillāh, lā ilāha illallāhu waḥdahu lā sharīka lah",
    translation_en: 'We have entered the morning, and the dominion belongs to Allah. All praise is due to Allah. There is no deity but Allah, alone without partner.',
    translation_ar: 'أصبحنا وأصبح الملك لله والحمد لله لا إله إلا الله وحده لا شريك له.',
    count: '1×',
    benefit_en: 'Begins the day with divine sovereignty — a reminder that your day is held in Allah\'s hands.',
    benefit_ar: 'يبدأ اليوم بالسيادة الإلهية — تذكّر أن يومك محمول في يد الله.',
  },
  {
    arabic: 'سُبْحَانَ اللَّهِ وَبِحَمْدِهِ',
    transliteration: "Subḥānallāhi wa biḥamdih",
    translation_en: 'Glory be to Allah and praise be to Him.',
    translation_ar: 'سبحان الله وبحمده.',
    count: '100×',
    benefit_en: 'The Prophet ﷺ said: "Whoever says this 100 times in the morning, his sins are erased even if they were like the foam of the sea." (Bukhari & Muslim)',
    benefit_ar: 'قال النبي ﷺ: "من قالها مائة مرة حين يصبح حُطّت خطاياه وإن كانت مثل زبد البحر." (البخاري ومسلم)',
  },
  {
    arabic: 'اللَّهُمَّ بِكَ أَصْبَحْنَا، وَبِكَ أَمْسَيْنَا، وَبِكَ نَحْيَا، وَبِكَ نَمُوتُ، وَإِلَيْكَ النُّشُورُ',
    transliteration: "Allāhumma bika aṣbaḥnā, wa bika amsaynā, wa bika naḥyā, wa bika namūtu, wa ilaykan-nushūr",
    translation_en: 'O Allah, by You we enter the morning, by You we enter the evening, by You we live, by You we die, and to You is the resurrection.',
    translation_ar: 'اللهم بك أصبحنا وبك أمسينا وبك نحيا وبك نموت وإليك النشور.',
    count: '1×',
    benefit_en: 'Complete surrender of the day to Allah — roots your entire being in divine dependence from the first moment.',
    benefit_ar: 'تسليم كامل لليوم لله — يُجذّر كيانك كله في الاتكال الإلهي منذ اللحظة الأولى.',
  },
];

const EVENING_PRACTICES: Practice[] = [
  {
    arabic: 'أَمْسَيْنَا وَأَمْسَى الْمُلْكُ لِلَّهِ، وَالْحَمْدُ لِلَّهِ',
    transliteration: "Amsaynā wa amsal-mulku lillāh, walḥamdulillāh",
    translation_en: 'We have entered the evening, and the dominion belongs to Allah. All praise is due to Allah.',
    translation_ar: 'أمسينا وأمسى الملك لله والحمد لله.',
    count: '1×',
    benefit_en: 'Closes the day with gratitude and surrender — the evening counterpart to the morning opening.',
    benefit_ar: 'يُختم اليوم بالشكر والاستسلام — المقابل المسائي للافتتاح الصباحي.',
  },
  {
    arabic: 'أَسْتَغْفِرُ اللَّهَ وَأَتُوبُ إِلَيْهِ',
    transliteration: "Astaghfirullāha wa atūbu ilayh",
    translation_en: 'I seek forgiveness from Allah and repent to Him.',
    translation_ar: 'أستغفر الله وأتوب إليه.',
    count: '100×',
    benefit_en: 'The Prophet ﷺ used to say this 100 times per day. Evening is the time to release the day\'s accumulations and approach the night clean.',
    benefit_ar: 'كان النبي ﷺ يقولها مائة مرة يومياً. المساء هو وقت إطلاق تراكمات اليوم والاقتراب من الليل نقياً.',
  },
  {
    arabic: 'بِاسْمِكَ اللَّهُمَّ أَمُوتُ وَأَحْيَا',
    transliteration: "Bismika Allāhumma amūtu wa aḥyā",
    translation_en: 'In Your name, O Allah, I die and I live.',
    translation_ar: 'باسمك اللهم أموت وأحيا.',
    count: '1× (before sleep)',
    benefit_en: 'Said before sleeping. Treats sleep as a minor death and waking as a resurrection — framing every night as a return to Allah.',
    benefit_ar: 'يُقال قبل النوم. يعامل النوم كموتة صغرى واليقظة كبعث — يُؤطّر كل ليلة كعودة إلى الله.',
  },
];

const ANYTIME_DHIKR: Practice[] = [
  {
    arabic: 'لَا إِلَهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ، لَهُ الْمُلْكُ وَلَهُ الْحَمْدُ، وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ',
    transliteration: "Lā ilāha illallāhu waḥdahu lā sharīka lah, lahul-mulku wa lahul-ḥamd, wa huwa 'alā kulli shay'in qadīr",
    translation_en: 'There is no deity but Allah alone, with no partner. His is the dominion and His is the praise, and He is over all things powerful.',
    translation_ar: 'لا إله إلا الله وحده لا شريك له له الملك وله الحمد وهو على كل شيء قدير.',
    count: '10×',
    benefit_en: 'Said 10 times after Fajr before speaking — equivalent to freeing 4 slaves, 10 good deeds, 10 sins erased, protected from Satan until evening. (Bukhari)',
    benefit_ar: 'يُقال 10 مرات بعد الفجر قبل الكلام — يعادل عتق 4 رقاب، 10 حسنات، 10 سيئات محواة، حماية من الشيطان حتى المساء. (البخاري)',
  },
  {
    arabic: 'سُبْحَانَ اللَّهِ، وَالْحَمْدُ لِلَّهِ، وَلَا إِلَهَ إِلَّا اللَّهُ، وَاللَّهُ أَكْبَرُ',
    transliteration: "Subḥānallāh, walḥamdulillāh, wa lā ilāha illallāh, wallāhu akbar",
    translation_en: 'Glory be to Allah. Praise be to Allah. There is no deity but Allah. Allah is the Greatest.',
    translation_ar: 'سبحان الله والحمد لله ولا إله إلا الله والله أكبر.',
    count: '33× each (after prayer)',
    benefit_en: 'The Prophet ﷺ called these "the four most beloved phrases to Allah." Said 33 times each after every prayer — fills what remains to 100 with Lā ilāha illallāh.',
    benefit_ar: 'سمّاها النبي ﷺ "أحب الكلام إلى الله الأربع." تُقال 33 مرة لكل منها بعد كل صلاة — ويكمل المئة بـ"لا إله إلا الله".',
  },
  {
    arabic: 'لَا حَوْلَ وَلَا قُوَّةَ إِلَّا بِاللَّهِ',
    transliteration: "Lā ḥawla wa lā quwwata illā billāh",
    translation_en: 'There is no power and no strength except with Allah.',
    translation_ar: 'لا حول ولا قوة إلا بالله.',
    count: 'Frequently',
    benefit_en: 'Called "a treasure from the treasures of Paradise" by the Prophet ﷺ. Especially powerful when feeling overwhelmed, helpless, or burdened beyond your capacity.',
    benefit_ar: 'سمّاها النبي ﷺ "كنزاً من كنوز الجنة". قوية بشكل خاص حين تشعر بالإرهاق أو العجز أو الثقل فوق طاقتك.',
  },
];

export function DailyPracticesPanel() {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';
  const [openSection, setOpenSection] = useState<string | null>(null);

  const toggle = (key: string) => setOpenSection(prev => (prev === key ? null : key));

  const renderPractices = (practices: Practice[]) => (
    <div className="space-y-3 mt-3">
      {practices.map((p, i) => (
        <div key={i} className="bg-white rounded-xl border border-gray-100 p-4 space-y-2">
          <div className={clsx('flex items-start justify-between gap-2', isRtl && 'flex-row-reverse')}>
            <p dir="rtl" className="font-arabic text-right text-base leading-loose text-gray-900 flex-1">
              {p.arabic}
            </p>
            <span className="text-xs font-medium bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full whitespace-nowrap flex-shrink-0 mt-1">
              {p.count}
            </span>
          </div>
          <p dir="ltr" className="text-xs text-gray-400 italic">{p.transliteration}</p>
          <p className={clsx('text-sm text-gray-700', isRtl && 'font-arabic text-right')}>
            {isRtl ? p.translation_ar : p.translation_en}
          </p>
          <p className={clsx('text-xs text-gray-500 leading-relaxed border-t border-gray-100 pt-2', isRtl && 'font-arabic text-right')}>
            {isRtl ? p.benefit_ar : p.benefit_en}
          </p>
        </div>
      ))}
    </div>
  );

  const sections = [
    {
      key: 'morning',
      icon: Sun,
      color: 'text-amber-500',
      bgColor: 'bg-amber-50',
      borderColor: 'border-amber-200',
      label_en: 'Morning Adhkar (Fajr – Sunrise)',
      label_ar: 'أذكار الصباح (الفجر – الشروق)',
      practices: MORNING_PRACTICES,
    },
    {
      key: 'evening',
      icon: Sunset,
      color: 'text-orange-500',
      bgColor: 'bg-orange-50',
      borderColor: 'border-orange-200',
      label_en: 'Evening Adhkar (Asr – Maghrib)',
      label_ar: 'أذكار المساء (العصر – المغرب)',
      practices: EVENING_PRACTICES,
    },
    {
      key: 'anytime',
      icon: Star,
      color: 'text-indigo-500',
      bgColor: 'bg-indigo-50',
      borderColor: 'border-indigo-200',
      label_en: 'Core Dhikr — Any Time',
      label_ar: 'أذكار أساسية — في أي وقت',
      practices: ANYTIME_DHIKR,
    },
  ];

  return (
    <div className="space-y-3">
      <div className={clsx('flex items-center gap-2', isRtl && 'flex-row-reverse')}>
        <div className="w-1 h-5 bg-amber-400 rounded-full" />
        <h3 className={clsx('font-semibold text-gray-700 text-sm', isRtl && 'font-arabic')}>
          {isRtl ? 'الممارسات اليومية — الأذكار والأدعية' : 'Daily Practices — Adhkar & Du\'as'}
        </h3>
      </div>
      <p className={clsx('text-xs text-gray-500 leading-relaxed', isRtl && 'font-arabic text-right')}>
        {isRtl
          ? 'علّم النبي ﷺ أذكاراً منهجية للصباح والمساء وبعد الصلوات. هذه ليست مجرد شعائر — بل روتين يومي للحماية والشفاء وبناء العلاقة مع الله.'
          : 'The Prophet ﷺ taught systematic adhkar for morning, evening, and after prayers. These are not merely rituals — they are a daily regimen for protection, healing, and building your relationship with Allah.'}
      </p>
      {sections.map(section => {
        const Icon = section.icon;
        const isOpen = openSection === section.key;
        return (
          <div key={section.key}>
            <button
              onClick={() => toggle(section.key)}
              className={clsx(
                'w-full flex items-center justify-between p-4 rounded-xl border transition-colors',
                section.bgColor, section.borderColor,
                isRtl && 'flex-row-reverse',
              )}
            >
              <div className={clsx('flex items-center gap-2', isRtl && 'flex-row-reverse')}>
                <Icon className={clsx('w-4 h-4', section.color)} />
                <span className={clsx('text-sm font-semibold text-gray-800', isRtl && 'font-arabic')}>
                  {isRtl ? section.label_ar : section.label_en}
                </span>
              </div>
              {isOpen ? <ChevronUp className="w-4 h-4 text-gray-500" /> : <ChevronDown className="w-4 h-4 text-gray-500" />}
            </button>
            {isOpen && renderPractices(section.practices)}
          </div>
        );
      })}

      {/* Ibn Qayyim quote */}
      <div className="p-4 bg-gray-50 rounded-xl border border-gray-200">
        <p className={clsx('text-xs text-gray-600 italic leading-relaxed', isRtl && 'font-arabic text-right')}>
          {isRtl
            ? '"القلب بحاجة إلى الذكر كما يحتاج الجسد إلى الطعام. فكما يمرض الجسد بالجوع ويضعف، يمرض القلب بالغفلة ويموت بها." — ابن قيم الجوزية'
            : '"The heart needs dhikr as much as the body needs food. Just as the body becomes ill with hunger and weakens, the heart becomes ill with negligence and dies from it." — Ibn Qayyim al-Jawziyyah'}
        </p>
      </div>
    </div>
  );
}
