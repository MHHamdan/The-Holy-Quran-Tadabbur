import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Plane, MapPin, CheckCircle2, Circle, Info, ChevronDown, ChevronUp, AlertTriangle } from 'lucide-react';
import { useLanguageStore } from '../../stores/languageStore';
import clsx from 'clsx';

interface Ritual {
  id: string;
  name_en: string;
  name_ar: string;
  description_en: string;
  description_ar: string;
  location_en: string;
  location_ar: string;
  dua_ar?: string;
  dua_en?: string;
  tips_en?: string[];
  tips_ar?: string[];
  order: number;
}

interface TripType {
  id: 'hajj' | 'umrah';
  name_en: string;
  name_ar: string;
  description_en: string;
  description_ar: string;
}

const TRIP_TYPES: TripType[] = [
  {
    id: 'hajj',
    name_en: 'Hajj',
    name_ar: 'الحج',
    description_en: 'The annual Islamic pilgrimage to Mecca, one of the five pillars of Islam',
    description_ar: 'الحج السنوي إلى مكة المكرمة، أحد أركان الإسلام الخمسة',
  },
  {
    id: 'umrah',
    name_en: 'Umrah',
    name_ar: 'العمرة',
    description_en: 'The lesser pilgrimage that can be performed at any time of the year',
    description_ar: 'العمرة التي يمكن أداؤها في أي وقت من السنة',
  },
];

const UMRAH_RITUALS: Ritual[] = [
  {
    id: 'ihram',
    name_en: 'Ihram',
    name_ar: 'الإحرام',
    description_en: 'Enter the state of Ihram before crossing the Miqat. Wear the prescribed clothing and make the intention.',
    description_ar: 'الدخول في الإحرام قبل تجاوز الميقات. ارتداء ملابس الإحرام والنية.',
    location_en: 'Miqat (designated entry points)',
    location_ar: 'الميقات',
    dua_ar: 'لَبَّيْكَ اللَّهُمَّ عُمْرَةً',
    dua_en: 'Labbayka Allahumma Umratan (Here I am O Allah, for Umrah)',
    tips_en: ['Perform ghusl before Ihram', 'Men wear two white unstitched cloths', 'Women wear normal modest clothing'],
    tips_ar: ['الاغتسال قبل الإحرام', 'يلبس الرجال إزاراً ورداءً أبيضين', 'تلبس المرأة ملابسها الشرعية العادية'],
    order: 1,
  },
  {
    id: 'tawaf',
    name_en: 'Tawaf',
    name_ar: 'الطواف',
    description_en: 'Perform seven circuits around the Kaaba in a counter-clockwise direction, starting from the Black Stone.',
    description_ar: 'الطواف حول الكعبة سبعة أشواط عكس عقارب الساعة، بدءاً من الحجر الأسود.',
    location_en: 'Masjid al-Haram, around the Kaaba',
    location_ar: 'المسجد الحرام، حول الكعبة',
    dua_ar: 'رَبَّنَا آتِنَا فِي الدُّنْيَا حَسَنَةً وَفِي الْآخِرَةِ حَسَنَةً وَقِنَا عَذَابَ النَّارِ',
    dua_en: 'Rabbana atina fid-dunya hasanatan wa fil-akhirati hasanatan waqina adhaban-nar',
    tips_en: ['Point or kiss the Black Stone at each round', 'Pray two rakaat at Maqam Ibrahim after Tawaf', 'Drink Zamzam water'],
    tips_ar: ['الإشارة أو تقبيل الحجر الأسود في كل شوط', 'صلاة ركعتين خلف مقام إبراهيم بعد الطواف', 'شرب ماء زمزم'],
    order: 2,
  },
  {
    id: 'sai',
    name_en: "Sa'i",
    name_ar: 'السعي',
    description_en: 'Walk seven times between the hills of Safa and Marwa, commemorating Hajar searching for water.',
    description_ar: 'السعي سبعة أشواط بين الصفا والمروة، تخليداً لسعي هاجر بحثاً عن الماء.',
    location_en: 'Between Safa and Marwa hills',
    location_ar: 'بين الصفا والمروة',
    dua_ar: 'إِنَّ الصَّفَا وَالْمَرْوَةَ مِن شَعَائِرِ اللَّهِ',
    dua_en: 'Innas-Safa wal-Marwata min sha\'a\'irillah (Indeed, Safa and Marwa are among the symbols of Allah)',
    tips_en: ['Start from Safa and end at Marwa', 'Men jog lightly between the green lights', 'Make dua throughout'],
    tips_ar: ['البدء من الصفا والانتهاء بالمروة', 'يهرول الرجال بين العلامات الخضراء', 'الدعاء طوال السعي'],
    order: 3,
  },
  {
    id: 'halq',
    name_en: 'Halq or Taqsir',
    name_ar: 'الحلق أو التقصير',
    description_en: 'Shave the head (Halq) or trim the hair (Taqsir) to complete the Umrah.',
    description_ar: 'حلق الرأس أو تقصير الشعر لإتمام العمرة.',
    location_en: 'Barber shops near the Haram',
    location_ar: 'محلات الحلاقة قرب الحرم',
    tips_en: ['Halq (shaving) is preferable for men', 'Women trim a fingertip length of hair', 'This completes the Umrah'],
    tips_ar: ['الحلق أفضل للرجال', 'تقصر المرأة قدر أنملة من شعرها', 'بهذا تتم العمرة'],
    order: 4,
  },
];

const HAJJ_RITUALS: Ritual[] = [
  ...UMRAH_RITUALS.map(r => ({ ...r, id: `hajj_${r.id}` })),
  {
    id: 'mina_8',
    name_en: 'Day of Tarwiyah (8th Dhul Hijjah)',
    name_ar: 'يوم التروية (8 ذو الحجة)',
    description_en: 'Travel to Mina and spend the night. Perform all prayers in shortened form.',
    description_ar: 'التوجه إلى منى والمبيت فيها. أداء الصلوات قصراً.',
    location_en: 'Mina',
    location_ar: 'منى',
    tips_en: ['Shorten prayers (Dhuhr, Asr, Isha to 2 rakaat)', 'Prepare for Arafah the next day'],
    tips_ar: ['قصر الصلوات (الظهر والعصر والعشاء ركعتين)', 'الاستعداد ليوم عرفة'],
    order: 5,
  },
  {
    id: 'arafah',
    name_en: 'Day of Arafah (9th Dhul Hijjah)',
    name_ar: 'يوم عرفة (9 ذو الحجة)',
    description_en: 'Stand at Arafah from noon until sunset. This is the most important pillar of Hajj.',
    description_ar: 'الوقوف بعرفة من الظهر حتى غروب الشمس. هذا أهم ركن في الحج.',
    location_en: 'Plain of Arafah',
    location_ar: 'صعيد عرفات',
    dua_ar: 'لا إله إلا الله وحده لا شريك له، له الملك وله الحمد وهو على كل شيء قدير',
    dua_en: 'La ilaha illallahu wahdahu la sharika lah, lahul-mulku wa lahul-hamdu wa huwa ala kulli shay\'in qadir',
    tips_en: ['This is the greatest day', 'Make abundant dua', 'The Prophet said: "Hajj is Arafah"'],
    tips_ar: ['هذا أعظم يوم', 'أكثر من الدعاء', 'قال النبي ﷺ: "الحج عرفة"'],
    order: 6,
  },
  {
    id: 'muzdalifah',
    name_en: 'Night at Muzdalifah',
    name_ar: 'المبيت بمزدلفة',
    description_en: 'After sunset on Arafah, proceed to Muzdalifah. Pray Maghrib and Isha combined, and collect pebbles.',
    description_ar: 'بعد غروب يوم عرفة، التوجه إلى مزدلفة. الجمع بين المغرب والعشاء وجمع الحصى.',
    location_en: 'Muzdalifah',
    location_ar: 'مزدلفة',
    tips_en: ['Combine and shorten Maghrib and Isha', 'Collect 70 pebbles for Jamarat', 'Rest until Fajr'],
    tips_ar: ['الجمع والقصر بين المغرب والعشاء', 'جمع 70 حصاة للجمرات', 'الراحة حتى الفجر'],
    order: 7,
  },
  {
    id: 'jamarat_10',
    name_en: 'Stoning & Sacrifice (10th Dhul Hijjah)',
    name_ar: 'رمي الجمرات والذبح (10 ذو الحجة)',
    description_en: 'Stone Jamarat al-Aqabah with 7 pebbles, sacrifice an animal, shave head, and perform Tawaf al-Ifadah.',
    description_ar: 'رمي جمرة العقبة بسبع حصيات، ذبح الهدي، الحلق، وطواف الإفاضة.',
    location_en: 'Mina & Makkah',
    location_ar: 'منى ومكة',
    dua_ar: 'بسم الله، الله أكبر',
    dua_en: 'Bismillah, Allahu Akbar (In the name of Allah, Allah is Greatest)',
    tips_en: ['Stone after sunrise', 'Say Allahu Akbar with each pebble', 'Tawaf al-Ifadah can be delayed'],
    tips_ar: ['الرمي بعد شروق الشمس', 'التكبير مع كل حصاة', 'يجوز تأخير طواف الإفاضة'],
    order: 8,
  },
  {
    id: 'tashreeq',
    name_en: 'Days of Tashreeq (11-13 Dhul Hijjah)',
    name_ar: 'أيام التشريق (11-13 ذو الحجة)',
    description_en: 'Stay in Mina and stone all three Jamarat each day after Dhuhr. May leave after 12th if desired.',
    description_ar: 'المبيت بمنى ورمي الجمرات الثلاث كل يوم بعد الظهر. يجوز التعجل في اليوم الثاني عشر.',
    location_en: 'Mina',
    location_ar: 'منى',
    tips_en: ['Stone small, medium, then large Jamarat', 'Make dua after small and medium', 'No dua after large'],
    tips_ar: ['رمي الصغرى ثم الوسطى ثم الكبرى', 'الدعاء بعد الصغرى والوسطى', 'لا يقف للدعاء بعد الكبرى'],
    order: 9,
  },
  {
    id: 'farewell',
    name_en: 'Farewell Tawaf',
    name_ar: 'طواف الوداع',
    description_en: 'Perform a final Tawaf around the Kaaba before leaving Makkah.',
    description_ar: 'طواف الوداع حول الكعبة قبل مغادرة مكة.',
    location_en: 'Masjid al-Haram',
    location_ar: 'المسجد الحرام',
    tips_en: ['Should be the last act before leaving', 'Exempted for menstruating women', 'Make dua while looking at Kaaba'],
    tips_ar: ['يكون آخر عمل قبل السفر', 'يسقط عن الحائض', 'الدعاء عند النظر للكعبة'],
    order: 10,
  },
];

const PREPARATION_CHECKLIST = [
  { id: 'visa', name_en: 'Obtain visa', name_ar: 'الحصول على التأشيرة' },
  { id: 'vaccination', name_en: 'Required vaccinations', name_ar: 'التطعيمات المطلوبة' },
  { id: 'ihram_clothes', name_en: 'Ihram clothing', name_ar: 'ملابس الإحرام' },
  { id: 'medication', name_en: 'Personal medication', name_ar: 'الأدوية الشخصية' },
  { id: 'comfortable_shoes', name_en: 'Comfortable walking shoes', name_ar: 'أحذية مريحة للمشي' },
  { id: 'sunscreen', name_en: 'Sunscreen & umbrella', name_ar: 'واقي شمس ومظلة' },
  { id: 'money_belt', name_en: 'Money belt for valuables', name_ar: 'حزام للأموال والثمينات' },
  { id: 'dua_book', name_en: "Dua book / app", name_ar: 'كتاب أو تطبيق أدعية' },
  { id: 'phone_charger', name_en: 'Phone & charger', name_ar: 'هاتف وشاحن' },
  { id: 'copy_docs', name_en: 'Copies of documents', name_ar: 'نسخ من الوثائق' },
];

export function HajjUmrahGuidePage() {
  const { language } = useLanguageStore();
  const isArabic = language === 'ar';

  const [selectedTrip, setSelectedTrip] = useState<'hajj' | 'umrah'>('umrah');
  const [completedRituals, setCompletedRituals] = useState<Set<string>>(new Set());
  const [expandedRitual, setExpandedRitual] = useState<string | null>(null);
  const [checkedItems, setCheckedItems] = useState<Set<string>>(new Set());

  const rituals = selectedTrip === 'hajj' ? HAJJ_RITUALS : UMRAH_RITUALS;

  function toggleRitual(id: string) {
    setCompletedRituals((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }

  function toggleExpanded(id: string) {
    setExpandedRitual(expandedRitual === id ? null : id);
  }

  function toggleCheckedItem(id: string) {
    setCheckedItems((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }

  const progress = Math.round((completedRituals.size / rituals.length) * 100);

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8" dir={isArabic ? 'rtl' : 'ltr'}>
      {/* Header */}
      <div className="mb-6">
        <Link
          to="/tools"
          className="inline-flex items-center gap-2 text-primary-600 hover:text-primary-700 mb-4"
        >
          <ArrowLeft className={clsx('w-4 h-4', isArabic && 'rotate-180')} />
          {isArabic ? 'العودة للأدوات' : 'Back to Tools'}
        </Link>

        <div className="flex items-center gap-3 mb-2">
          <div className="p-3 bg-teal-100 rounded-lg">
            <Plane className="w-8 h-8 text-teal-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {isArabic ? 'دليل الحج والعمرة' : 'Hajj & Umrah Guide'}
            </h1>
            <p className="text-gray-600">
              {isArabic
                ? 'دليل شامل لمناسك الحج والعمرة'
                : 'Complete guide to Hajj and Umrah rituals'}
            </p>
          </div>
        </div>
      </div>

      {/* Trip Type Selector */}
      <div className="mb-8">
        <div className="flex gap-4">
          {TRIP_TYPES.map((trip) => (
            <button
              key={trip.id}
              onClick={() => {
                setSelectedTrip(trip.id);
                setCompletedRituals(new Set());
                setExpandedRitual(null);
              }}
              className={clsx(
                'flex-1 p-4 rounded-xl border-2 transition-all',
                selectedTrip === trip.id
                  ? 'border-teal-500 bg-teal-50'
                  : 'border-gray-200 hover:border-gray-300'
              )}
            >
              <h3 className="font-bold text-lg mb-1">
                {isArabic ? trip.name_ar : trip.name_en}
              </h3>
              <p className="text-sm text-gray-600">
                {isArabic ? trip.description_ar : trip.description_en}
              </p>
            </button>
          ))}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-6 p-4 bg-gray-50 rounded-xl">
        <div className="flex items-center justify-between mb-2">
          <span className="font-medium text-gray-700">
            {isArabic ? 'تقدم المناسك' : 'Ritual Progress'}
          </span>
          <span className="text-teal-600 font-bold">{progress}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div
            className="bg-teal-500 h-3 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
        <p className="text-sm text-gray-500 mt-2">
          {isArabic
            ? `${completedRituals.size} من ${rituals.length} مناسك مكتملة`
            : `${completedRituals.size} of ${rituals.length} rituals completed`}
        </p>
      </div>

      {/* Rituals List */}
      <div className="mb-8">
        <h2 className="text-xl font-bold text-gray-900 mb-4">
          {isArabic ? 'المناسك' : 'Rituals'}
        </h2>
        <div className="space-y-3">
          {rituals.map((ritual) => (
            <RitualCard
              key={ritual.id}
              ritual={ritual}
              language={language}
              isCompleted={completedRituals.has(ritual.id)}
              isExpanded={expandedRitual === ritual.id}
              onToggleComplete={() => toggleRitual(ritual.id)}
              onToggleExpand={() => toggleExpanded(ritual.id)}
            />
          ))}
        </div>
      </div>

      {/* Preparation Checklist */}
      <div className="mb-8">
        <h2 className="text-xl font-bold text-gray-900 mb-4">
          {isArabic ? 'قائمة التجهيزات' : 'Preparation Checklist'}
        </h2>
        <div className="card border border-gray-200">
          <div className="space-y-2">
            {PREPARATION_CHECKLIST.map((item) => (
              <label
                key={item.id}
                className="flex items-center gap-3 p-2 hover:bg-gray-50 rounded-lg cursor-pointer"
              >
                <input
                  type="checkbox"
                  checked={checkedItems.has(item.id)}
                  onChange={() => toggleCheckedItem(item.id)}
                  className="w-5 h-5 text-teal-600 rounded focus:ring-teal-500"
                />
                <span className={clsx(checkedItems.has(item.id) && 'line-through text-gray-400')}>
                  {isArabic ? item.name_ar : item.name_en}
                </span>
              </label>
            ))}
          </div>
        </div>
      </div>

      {/* Important Dates Notice */}
      <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div>
            <h4 className="font-semibold text-amber-800 mb-1">
              {isArabic ? 'تواريخ مهمة' : 'Important Dates'}
            </h4>
            <p className="text-sm text-amber-700">
              {isArabic
                ? 'الحج يقام في الأيام 8-13 من ذي الحجة. تحقق من التقويم الهجري للتواريخ الميلادية المقابلة.'
                : 'Hajj is performed on 8-13 Dhul Hijjah. Check the Hijri calendar for corresponding Gregorian dates.'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

// Ritual Card Component
interface RitualCardProps {
  ritual: Ritual;
  language: 'ar' | 'en';
  isCompleted: boolean;
  isExpanded: boolean;
  onToggleComplete: () => void;
  onToggleExpand: () => void;
}

function RitualCard({
  ritual,
  language,
  isCompleted,
  isExpanded,
  onToggleComplete,
  onToggleExpand,
}: RitualCardProps) {
  const isArabic = language === 'ar';

  return (
    <div
      className={clsx(
        'card border transition-colors',
        isCompleted ? 'border-teal-300 bg-teal-50' : 'border-gray-200'
      )}
    >
      {/* Header */}
      <div className="flex items-start gap-3">
        <button
          onClick={onToggleComplete}
          className="shrink-0 mt-1"
        >
          {isCompleted ? (
            <CheckCircle2 className="w-6 h-6 text-teal-600" />
          ) : (
            <Circle className="w-6 h-6 text-gray-300" />
          )}
        </button>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <h3 className={clsx(
              'font-semibold',
              isCompleted ? 'text-teal-700' : 'text-gray-900'
            )}>
              {ritual.order}. {isArabic ? ritual.name_ar : ritual.name_en}
            </h3>
            <button
              onClick={onToggleExpand}
              className="p-1 text-gray-500 hover:text-gray-700"
            >
              {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
            </button>
          </div>
          <p className="text-sm text-gray-600 mt-1">
            {isArabic ? ritual.description_ar : ritual.description_en}
          </p>
          <p className="text-xs text-gray-500 mt-1 flex items-center gap-1">
            <MapPin className="w-3 h-3" />
            {isArabic ? ritual.location_ar : ritual.location_en}
          </p>
        </div>
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="mt-4 pt-4 border-t border-gray-200 space-y-4">
          {/* Dua */}
          {ritual.dua_ar && (
            <div className="p-3 bg-white rounded-lg border border-gray-100">
              <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-1">
                <Info className="w-4 h-4" />
                {isArabic ? 'الدعاء' : 'Dua'}
              </h4>
              <p className="text-lg text-gray-900 font-arabic leading-loose" dir="rtl">
                {ritual.dua_ar}
              </p>
              {ritual.dua_en && (
                <p className="text-sm text-gray-600 mt-2" dir="ltr">
                  {ritual.dua_en}
                </p>
              )}
            </div>
          )}

          {/* Tips */}
          {(ritual.tips_en || ritual.tips_ar) && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">
                {isArabic ? 'نصائح' : 'Tips'}
              </h4>
              <ul className="space-y-1">
                {(isArabic ? ritual.tips_ar : ritual.tips_en)?.map((tip, idx) => (
                  <li key={idx} className="text-sm text-gray-600 flex items-start gap-2">
                    <span className="text-teal-500">•</span>
                    {tip}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
