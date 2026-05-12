import { useState, useEffect } from 'react';
import { BookOpen, Shield, Sparkles, ChevronDown, ChevronUp, Loader2, ExternalLink, Info, CheckCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useLanguageStore } from '../../stores/languageStore';
import { therapyApi } from '../../lib/api';
import type { GuidanceCard } from '../../types/therapy';
import { QuranAudioPlayer } from '../quran/QuranAudioPlayer';
import clsx from 'clsx';

// Ruqyah Shariah informational data (no Quranic text hardcoded — fetched from API)
const RUQYAH_CHAPTERS: Array<{
  key: string;
  surah: number;
  ayah?: string;
  name_en: string;
  name_ar: string;
  hadith_en: string;
  hadith_ar: string;
  source: string;
}> = [
  {
    key: 'fatiha',
    surah: 1,
    name_en: 'Surah Al-Fatiha',
    name_ar: 'سورة الفاتحة',
    hadith_en:
      'A companion recited Al-Fatiha over a scorpion-sting victim and the man was healed. The Prophet ﷺ said: "How did you know that Al-Fatiha is a ruqyah?" and approved the act. (Bukhari & Muslim)',
    hadith_ar:
      'قرأ صحابي سورة الفاتحة على لديغ فبرأ، فقال النبي ﷺ: "وما يدريك أنها رقية؟" وأقرّ الفعل. (البخاري ومسلم)',
    source: 'Bukhari & Muslim',
  },
  {
    key: 'ayat-kursi',
    surah: 2,
    ayah: '2:255',
    name_en: 'Ayat Al-Kursi',
    name_ar: 'آية الكرسي',
    hadith_en:
      'The Prophet ﷺ said: "Whoever recites Ayat Al-Kursi after every obligatory prayer, nothing prevents him from entering Paradise except death." And: "When you go to bed, recite it — then a guardian from Allah will protect you all night, and Satan will not come near you until morning." (Bukhari)',
    hadith_ar:
      'قال النبي ﷺ: "من قرأ آية الكرسي دبر كل صلاة مكتوبة لم يمنعه من دخول الجنة إلا أن يموت." وقال: "إذا أويت إلى فراشك فاقرأها فلن يزال عليك من الله حافظ ولا يقربك شيطان حتى تصبح." (البخاري)',
    source: 'Bukhari',
  },
  {
    key: 'baqarah-last',
    surah: 2,
    ayah: '2:285–286',
    name_en: 'Last 2 Verses of Al-Baqarah',
    name_ar: 'آخر آيتين من البقرة',
    hadith_en:
      'The Prophet ﷺ said: "Whoever recites the last two verses of Surah Al-Baqarah at night, they will suffice him." Scholars explain this means they provide complete protection from harm and the whispering of Satan. (Bukhari & Muslim)',
    hadith_ar:
      'قال النبي ﷺ: "من قرأ بالآيتين من آخر سورة البقرة في ليلة كفتاه." يرى العلماء أن "كفتاه" تعني الحماية الكاملة من الأذى ووساوس الشيطان. (البخاري ومسلم)',
    source: 'Bukhari & Muslim',
  },
  {
    key: 'ikhlas',
    surah: 112,
    name_en: 'Surah Al-Ikhlas',
    name_ar: 'سورة الإخلاص',
    hadith_en:
      'The Prophet ﷺ said this surah is equal to one-third of the Quran (Bukhari). He ﷺ recited it — along with Al-Falaq and An-Nas — into his cupped hands and blew over his body each morning and evening as a daily protection practice (Bukhari).',
    hadith_ar:
      'قال النبي ﷺ إن هذه السورة تعدل ثلث القرآن (البخاري). وكان يقرأها — مع المعوذتين — في كفيه ثم ينفخ ويمسح جسده صباحاً ومساءً للحماية اليومية (البخاري).',
    source: 'Bukhari',
  },
  {
    key: 'falaq',
    surah: 113,
    name_en: 'Surah Al-Falaq',
    name_ar: 'سورة الفلق',
    hadith_en:
      'The Prophet ﷺ said: "Seek protection with them (Al-Falaq and An-Nas), for there is nothing better to seek protection with." (Abu Dawud, graded sahih by al-Albani) He recited them three times each morning and evening.',
    hadith_ar:
      'قال النبي ﷺ: "تعوّذوا بهما — المعوذتين — فإنه لا يُتعوَّذ بمثلهما." (أبو داود، صحّحه الألباني) وكان يقرأهما ثلاث مرات صباحاً ومساءً.',
    source: 'Abu Dawud (sahih)',
  },
  {
    key: 'nas',
    surah: 114,
    name_en: 'Surah An-Nas',
    name_ar: 'سورة الناس',
    hadith_en:
      'Together with Al-Falaq, this surah forms the "Al-Mu\'awwidhatayn" (the two protectors). The Prophet ﷺ specifically instructed their recitation when afflicted by the evil eye, black magic, or waswas (whispering of Satan). (Bukhari & Muslim)',
    hadith_ar:
      'تُشكّل هذه السورة مع الفلق "المعوذتين". أوصى النبي ﷺ صراحةً بقراءتهما عند الإصابة بالعين أو السحر أو الوسواس. (البخاري ومسلم)',
    source: 'Bukhari & Muslim',
  },
];

const PROCEDURE_STEPS_EN = [
  'Make wudu (ablution) if possible to be in a state of purity.',
  'Sit quietly, facing the qiblah if convenient, and intend the recitation for healing.',
  'Recite each surah/verse with presence and belief (iman) that healing comes from Allah alone — not from the words themselves.',
  'Optionally: cup your hands, recite into them, and gently blow over the affected area or your entire body.',
  'You may recite over water and then drink it or use it for washing.',
  'Repeat three times for each surah or verse. Consistency is key — morning and evening, especially.',
  'Combine with sincere du\'a and a firm belief that Allah is Al-Shafi (the Healer).',
];

const PROCEDURE_STEPS_AR = [
  'توضّأ إن أمكن لتكون في حالة طهارة.',
  'اجلس بهدوء مستقبلاً القبلة إن تيسّر، وانوِ التلاوة للشفاء.',
  'اقرأ كل سورة أو آية بحضور وإيمان بأن الشفاء من الله وحده — لا من الكلمات ذاتها.',
  'اختياري: احجن كفيك، اقرأ فيهما، ثم انفث برفق على الموضع المصاب أو جسدك كله.',
  'يمكنك القراءة على ماء ثم شربه أو استعماله للغسل.',
  'كرّر ثلاث مرات لكل سورة أو آية. الاستمرارية مهمة — صباحاً ومساءً خاصةً.',
  'اقرن ذلك بدعاء صادق وثقة راسخة بأن الله هو الشافي.',
];

const CONDITIONS_EN = [
  'Recitation must be from the Quran or authentic prophetic supplications (du\'a) — never unknown or invented words.',
  'Must be performed in a language whose meaning is understood (Arabic, or accompanied by understanding).',
  'Firm belief that cure comes only from Allah — the ruqyah is only a means.',
];

const CONDITIONS_AR = [
  'يجب أن تكون التلاوة من القرآن أو من الأدعية النبوية الصحيحة — لا كلمات مجهولة أو مخترعة.',
  'يجب أن تُؤدّى بلغة مفهومة المعنى (بالعربية أو مع فهم معناها).',
  'يقين تام بأن الشفاء من الله وحده — والرقية مجرد سبب.',
];

interface RuqyahChapterCardProps {
  chapter: (typeof RUQYAH_CHAPTERS)[0];
}

function RuqyahChapterCard({ chapter }: RuqyahChapterCardProps) {
  const { language } = useLanguageStore();
  const [hadithOpen, setHadithOpen] = useState(false);
  const isRtl = language === 'ar';

  return (
    <div className="bg-white rounded-2xl border border-emerald-100 shadow-sm overflow-hidden">
      <div className={clsx('px-5 py-3 bg-emerald-50 flex items-center justify-between', isRtl && 'flex-row-reverse')}>
        <div className={clsx('flex items-center gap-2', isRtl && 'flex-row-reverse')}>
          <BookOpen className="w-4 h-4 text-emerald-600" />
          <h3 className={clsx('font-semibold text-emerald-800 text-sm', isRtl && 'font-arabic')}>
            {isRtl ? chapter.name_ar : chapter.name_en}
          </h3>
        </div>
        <Link
          to={`/quran/${chapter.surah}`}
          className={clsx('flex items-center gap-1 text-xs text-emerald-600 hover:text-emerald-800', isRtl && 'flex-row-reverse')}
        >
          <span dir="ltr" className="font-mono text-xs">
            {chapter.ayah ?? `${chapter.surah}:1`}
          </span>
          <ExternalLink className="w-3 h-3" />
        </Link>
      </div>

      <div className="px-5 py-4">
        <QuranAudioPlayer
          mode="surah"
          suraNo={chapter.surah}
          language={language}
          compact={true}
          autoPlay={false}
        />
      </div>

      <div className="px-5 pb-4">
        <button
          onClick={() => setHadithOpen(v => !v)}
          className={clsx(
            'flex items-center gap-2 text-xs font-medium text-emerald-700 hover:text-emerald-900',
            isRtl && 'flex-row-reverse font-arabic w-full',
          )}
        >
          <Sparkles className="w-3.5 h-3.5 flex-shrink-0" />
          <span className={isRtl ? 'font-arabic' : ''}>
            {isRtl ? 'الدليل من الحديث' : 'Prophetic Authority'}
          </span>
          <span className="text-[10px] text-emerald-500 ml-0.5">({chapter.source})</span>
          {hadithOpen
            ? <ChevronUp className="w-3 h-3 ml-auto" />
            : <ChevronDown className="w-3 h-3 ml-auto" />}
        </button>
        {hadithOpen && (
          <div className="mt-3 p-3 bg-emerald-50 rounded-xl border border-emerald-100">
            <p className={clsx('text-xs text-emerald-800 leading-relaxed', isRtl ? 'font-arabic text-right' : '')}>
              {isRtl ? chapter.hadith_ar : chapter.hadith_en}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export function RuqyahGuide() {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';
  const [procedureOpen, setProcedureOpen] = useState(false);
  const [conditionsOpen, setConditionsOpen] = useState(false);
  const [themeCards, setThemeCards] = useState<GuidanceCard[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    therapyApi.getTheme('ruqyah')
      .then(data => setThemeCards(data.cards))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const steps = isRtl ? PROCEDURE_STEPS_AR : PROCEDURE_STEPS_EN;
  const conditions = isRtl ? CONDITIONS_AR : CONDITIONS_EN;

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="p-5 bg-gradient-to-br from-emerald-50 to-teal-50 rounded-2xl border border-emerald-100">
        <div className={clsx('flex items-start gap-3', isRtl && 'flex-row-reverse')}>
          <div className="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center flex-shrink-0">
            <Shield className="w-5 h-5 text-emerald-600" />
          </div>
          <div>
            <h2 className={clsx('font-bold text-emerald-900 text-base mb-1', isRtl && 'font-arabic text-right')}>
              {isRtl ? 'الرقية الشرعية — الشفاء بالقرآن الكريم' : 'Ruqyah Shariah — Healing with the Quran'}
            </h2>
            <p className={clsx('text-sm text-emerald-700 leading-relaxed', isRtl && 'font-arabic text-right')}>
              {isRtl
                ? 'الرقية الشرعية هي استخدام الآيات القرآنية والأدعية النبوية الصحيحة للشفاء. النبي ﷺ مارسها وأقرّها، وشرطها الأساسي الإيمان بأن الشفاء من الله وحده.'
                : 'Ruqyah Shariah is the use of Quranic verses and authentic prophetic supplications for healing. The Prophet ﷺ practiced and approved it. Its fundamental condition is belief that healing comes only from Allah.'}
            </p>
          </div>
        </div>
      </div>

      {/* Three Conditions */}
      <div>
        <button
          onClick={() => setConditionsOpen(v => !v)}
          className={clsx(
            'w-full flex items-center justify-between p-4 bg-amber-50 rounded-xl border border-amber-200',
            isRtl && 'flex-row-reverse',
          )}
        >
          <div className={clsx('flex items-center gap-2', isRtl && 'flex-row-reverse')}>
            <Info className="w-4 h-4 text-amber-600" />
            <span className={clsx('text-sm font-semibold text-amber-800', isRtl && 'font-arabic')}>
              {isRtl ? 'شروط الرقية الشرعية الثلاثة' : '3 Conditions of Valid Ruqyah'}
            </span>
          </div>
          {conditionsOpen ? <ChevronUp className="w-4 h-4 text-amber-600" /> : <ChevronDown className="w-4 h-4 text-amber-600" />}
        </button>
        {conditionsOpen && (
          <div className="mt-2 p-4 bg-amber-50 rounded-xl border border-amber-100 space-y-2">
            {conditions.map((condition, i) => (
              <div key={i} className={clsx('flex items-start gap-2.5', isRtl && 'flex-row-reverse')}>
                <span className="w-5 h-5 rounded-full bg-amber-200 text-amber-800 text-xs font-bold flex items-center justify-center flex-shrink-0 mt-0.5">
                  {i + 1}
                </span>
                <p className={clsx('text-sm text-amber-800 leading-relaxed', isRtl && 'font-arabic text-right')}>
                  {condition}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* The 6 Ruqyah Surahs/Verses */}
      <div>
        <h3 className={clsx('font-semibold text-gray-700 text-sm mb-3', isRtl && 'font-arabic text-right')}>
          {isRtl ? 'السور والآيات الأساسية في الرقية الشرعية' : 'Core Surahs & Verses of Ruqyah Shariah'}
        </h3>
        <div className="space-y-3">
          {RUQYAH_CHAPTERS.map(ch => (
            <RuqyahChapterCard key={ch.key} chapter={ch} />
          ))}
        </div>
      </div>

      {/* Quranic Healing Verses (from API) */}
      {(loading || themeCards.length > 0) && (
        <div>
          <h3 className={clsx('font-semibold text-gray-700 text-sm mb-3', isRtl && 'font-arabic text-right')}>
            {isRtl ? 'آيات الشفاء في القرآن الكريم' : 'Verses on Quranic Healing'}
          </h3>
          {loading ? (
            <div className="flex justify-center py-6">
              <Loader2 className="w-5 h-5 text-emerald-400 animate-spin" />
            </div>
          ) : (
            <div className="space-y-3">
              {themeCards.map(card => (
                <div key={card.reference} className="bg-white rounded-2xl border border-emerald-100 shadow-sm overflow-hidden">
                  <div className={clsx('px-5 py-3 bg-emerald-50 flex items-center justify-between', isRtl && 'flex-row-reverse')}>
                    <span className={clsx('text-xs font-medium text-emerald-700', isRtl && 'font-arabic')}>
                      {isRtl ? card.surah_name_ar : card.surah_name_en}
                    </span>
                    <Link
                      to={`/quran/${card.surah}`}
                      className="flex items-center gap-1 text-xs text-emerald-600 hover:text-emerald-800"
                    >
                      <span dir="ltr" className="font-mono">{card.reference}</span>
                      <ExternalLink className="w-3 h-3" />
                    </Link>
                  </div>
                  <div className="px-5 py-4 space-y-3">
                    <p dir="rtl" className="font-arabic text-right text-xl leading-loose text-gray-900">
                      {card.text_uthmani}
                    </p>
                    <QuranAudioPlayer
                      mode="verse"
                      suraNo={card.surah}
                      ayaNo={card.ayah_start}
                      language={language}
                      compact={true}
                      autoPlay={false}
                    />
                    <p className={clsx('text-sm text-emerald-800 leading-relaxed', isRtl && 'font-arabic text-right')}>
                      {isRtl ? card.lesson_ar : card.lesson_en}
                    </p>
                    <div className="p-3 bg-emerald-50 rounded-xl border border-emerald-100">
                      <p dir="rtl" className="font-arabic text-right text-sm text-emerald-800 leading-relaxed mb-1">
                        {card.dua_ar}
                      </p>
                      <p dir="ltr" className="text-xs text-emerald-600 italic">{card.dua_en}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Step-by-step Procedure */}
      <div>
        <button
          onClick={() => setProcedureOpen(v => !v)}
          className={clsx(
            'w-full flex items-center justify-between p-4 bg-indigo-50 rounded-xl border border-indigo-200',
            isRtl && 'flex-row-reverse',
          )}
        >
          <div className={clsx('flex items-center gap-2', isRtl && 'flex-row-reverse')}>
            <CheckCircle className="w-4 h-4 text-indigo-600" />
            <span className={clsx('text-sm font-semibold text-indigo-800', isRtl && 'font-arabic')}>
              {isRtl ? 'كيفية أداء الرقية على النفس (خطوة بخطوة)' : 'How to Perform Self-Ruqyah (Step by Step)'}
            </span>
          </div>
          {procedureOpen ? <ChevronUp className="w-4 h-4 text-indigo-600" /> : <ChevronDown className="w-4 h-4 text-indigo-600" />}
        </button>
        {procedureOpen && (
          <div className="mt-2 p-4 bg-indigo-50 rounded-xl border border-indigo-100 space-y-3">
            {steps.map((step, i) => (
              <div key={i} className={clsx('flex items-start gap-3', isRtl && 'flex-row-reverse')}>
                <span className="w-6 h-6 rounded-full bg-indigo-200 text-indigo-800 text-xs font-bold flex items-center justify-center flex-shrink-0 mt-0.5">
                  {i + 1}
                </span>
                <p className={clsx('text-sm text-indigo-800 leading-relaxed', isRtl && 'font-arabic text-right')}>
                  {step}
                </p>
              </div>
            ))}
            <div className="mt-3 p-3 bg-white rounded-xl border border-indigo-200">
              <p className={clsx('text-xs text-indigo-600 font-medium', isRtl && 'font-arabic text-right')}>
                {isRtl
                  ? 'تنبيه: الرقية الشرعية مكملة للعلاج الطبي لا بديل عنه. إذا كنت تعاني من أزمة صحية، تواصل مع متخصص طبي أو نفسي أولاً.'
                  : 'Note: Ruqyah Shariah complements — and does not replace — medical or mental health treatment. If you are in crisis, seek qualified professional help first.'}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
