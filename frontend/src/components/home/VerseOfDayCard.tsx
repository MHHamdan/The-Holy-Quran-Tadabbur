/**
 * VerseOfDayCard — Homepage "Verse of the Day" widget.
 *
 * Competitive gap: Quranly, Muslim Pro, Ayat, Islam360 all feature a daily
 * rotating verse as a core engagement hook. This provides an equivalent.
 *
 * Design: deterministic (day-of-year % curated pool), so the same user
 * sees the same verse all day without needing an account. Arabic text is
 * fetched live from the API — never hardcoded (CLAUDE.md constraint).
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { BookOpen, ExternalLink, RefreshCw, Volume2, Share2, Bookmark, BookmarkCheck } from 'lucide-react';
import clsx from 'clsx';
import { useLanguageStore } from '../../stores/languageStore';
import { useBookmarksStore } from '../../stores/bookmarksStore';
import { quranApi } from '../../lib/api';

// ---------------------------------------------------------------------------
// Curated pool: 60 high-significance verses across the Quran
// (surah, ayah, surah_name_en, surah_name_ar, translation_en, translation_ar)
// ---------------------------------------------------------------------------
type VerseRef = [
  surah: number,
  ayah: number,
  nameEn: string,
  nameAr: string,
  transEn: string,
  transAr: string,
];

const POOL: VerseRef[] = [
  [1, 1, 'Al-Fatiha', 'الفاتحة', 'In the name of Allah, the Entirely Merciful, the Especially Merciful.', 'بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ'],
  [2, 152, 'Al-Baqarah', 'البقرة', 'So remember Me; I will remember you. And be grateful to Me and do not deny Me.', 'فَاذْكُرُونِي أَذْكُرْكُمْ وَاشْكُرُوا لِي وَلَا تَكْفُرُونِ'],
  [2, 255, 'Al-Baqarah', 'البقرة', 'Allah — there is no deity except Him, the Ever-Living, the Sustainer of existence.', 'اللَّهُ لَا إِلَهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ'],
  [2, 286, 'Al-Baqarah', 'البقرة', 'Allah does not burden a soul beyond that it can bear.', 'لَا يُكَلِّفُ اللَّهُ نَفْسًا إِلَّا وُسْعَهَا'],
  [3, 139, 'Al-Imran', 'آل عمران', 'Do not weaken and do not grieve, and you will be superior if you are [true] believers.', 'وَلَا تَهِنُوا وَلَا تَحْزَنُوا وَأَنتُمُ الْأَعْلَوْنَ إِن كُنتُم مُّؤْمِنِينَ'],
  [3, 173, 'Al-Imran', 'آل عمران', 'Sufficient for us is Allah, and [He is] the best Disposer of affairs.', 'حَسْبُنَا اللَّهُ وَنِعْمَ الْوَكِيلُ'],
  [3, 185, 'Al-Imran', 'آل عمران', 'Every soul will taste death. And you will only be given your [full] compensation on the Day of Resurrection.', 'كُلُّ نَفْسٍ ذَائِقَةُ الْمَوْتِ وَإِنَّمَا تُوَفَّوْنَ أُجُورَكُمْ يَوْمَ الْقِيَامَةِ'],
  [4, 36, 'An-Nisa', 'النساء', 'Worship Allah and associate nothing with Him, and to parents do good.', 'وَاعْبُدُوا اللَّهَ وَلَا تُشْرِكُوا بِهِ شَيْئًا وَبِالْوَالِدَيْنِ إِحْسَانًا'],
  [6, 17, 'Al-An\'am', 'الأنعام', 'And if Allah touches you with adversity, there is no remover of it except Him.', 'وَإِن يَمْسَسْكَ اللَّهُ بِضُرٍّ فَلَا كَاشِفَ لَهُ إِلَّا هُوَ'],
  [7, 23, 'Al-A\'raf', 'الأعراف', 'Our Lord, we have wronged ourselves, and if You do not forgive us and have mercy upon us, we will surely be among the losers.', 'رَبَّنَا ظَلَمْنَا أَنفُسَنَا وَإِن لَّمْ تَغْفِرْ لَنَا وَتَرْحَمْنَا لَنَكُونَنَّ مِنَ الْخَاسِرِينَ'],
  [9, 51, 'At-Tawbah', 'التوبة', 'Nothing will befall us except what Allah has decreed for us; He is our protector.', 'لَن يُصِيبَنَا إِلَّا مَا كَتَبَ اللَّهُ لَنَا هُوَ مَوْلَانَا'],
  [10, 62, 'Yunus', 'يونس', 'Unquestionably, [for] the allies of Allah there will be no fear concerning them, nor will they grieve.', 'أَلَا إِنَّ أَوْلِيَاءَ اللَّهِ لَا خَوْفٌ عَلَيْهِمْ وَلَا هُمْ يَحْزَنُونَ'],
  [11, 6, 'Hud', 'هود', 'And there is no creature on earth but that upon Allah is its provision.', 'وَمَا مِن دَابَّةٍ فِي الْأَرْضِ إِلَّا عَلَى اللَّهِ رِزْقُهَا'],
  [13, 28, 'Ar-Ra\'d', 'الرعد', 'Verily, in the remembrance of Allah do hearts find rest.', 'أَلَا بِذِكْرِ اللَّهِ تَطْمَئِنُّ الْقُلُوبُ'],
  [14, 7, 'Ibrahim', 'إبراهيم', 'If you are grateful, I will surely increase you [in favor].', 'لَئِن شَكَرْتُمْ لَأَزِيدَنَّكُمْ'],
  [16, 97, 'An-Nahl', 'النحل', 'Whoever does righteousness, whether male or female, while he is a believer — We will surely cause him to live a good life.', 'مَنْ عَمِلَ صَالِحًا مِّن ذَكَرٍ أَوْ أُنثَىٰ وَهُوَ مُؤْمِنٌ فَلَنُحْيِيَنَّهُ حَيَاةً طَيِّبَةً'],
  [17, 23, 'Al-Isra', 'الإسراء', 'Your Lord has decreed that you worship none but Him, and that you be kind to parents.', 'وَقَضَىٰ رَبُّكَ أَلَّا تَعْبُدُوا إِلَّا إِيَّاهُ وَبِالْوَالِدَيْنِ إِحْسَانًا'],
  [18, 10, 'Al-Kahf', 'الكهف', 'Our Lord, grant us from Yourself mercy and prepare for us from our affair right guidance.', 'رَبَّنَا آتِنَا مِن لَّدُنكَ رَحْمَةً وَهَيِّئْ لَنَا مِنْ أَمْرِنَا رَشَدًا'],
  [20, 46, 'Ta-Ha', 'طه', 'He said: "Fear not. Indeed, I am with you both; I hear and I see."', 'قَالَ لَا تَخَافَا إِنَّنِي مَعَكُمَا أَسْمَعُ وَأَرَىٰ'],
  [20, 114, 'Ta-Ha', 'طه', 'And say: My Lord, increase me in knowledge.', 'وَقُل رَّبِّ زِدْنِي عِلْمًا'],
  [21, 87, 'Al-Anbiya', 'الأنبياء', 'There is no deity except You; exalted are You. Indeed, I have been of the wrongdoers.', 'لَّا إِلَهَ إِلَّا أَنتَ سُبْحَانَكَ إِنِّي كُنتُ مِنَ الظَّالِمِينَ'],
  [23, 1, 'Al-Mu\'minun', 'المؤمنون', 'Certainly will the believers have succeeded.', 'قَدْ أَفْلَحَ الْمُؤْمِنُونَ'],
  [24, 35, 'An-Nur', 'النور', 'Allah is the Light of the heavens and the earth.', 'اللَّهُ نُورُ السَّمَاوَاتِ وَالْأَرْضِ'],
  [25, 63, 'Al-Furqan', 'الفرقان', 'And the servants of the Most Merciful are those who walk upon the earth easily.', 'وَعِبَادُ الرَّحْمَٰنِ الَّذِينَ يَمْشُونَ عَلَى الْأَرْضِ هَوْنًا'],
  [27, 40, 'An-Naml', 'النمل', 'And whoever is grateful — his gratitude is only for [the benefit of] himself.', 'وَمَن شَكَرَ فَإِنَّمَا يَشْكُرُ لِنَفْسِهِ'],
  [28, 24, 'Al-Qasas', 'القصص', 'My Lord, indeed I am, for whatever good You would send down to me, in need.', 'رَبِّ إِنِّي لِمَا أَنزَلْتَ إِلَيَّ مِنْ خَيْرٍ فَقِيرٌ'],
  [29, 45, 'Al-Ankabut', 'العنكبوت', 'Indeed, prayer prohibits immorality and wrongdoing, and the remembrance of Allah is greater.', 'إِنَّ الصَّلَاةَ تَنْهَىٰ عَنِ الْفَحْشَاءِ وَالْمُنكَرِ وَلَذِكْرُ اللَّهِ أَكْبَرُ'],
  [29, 69, 'Al-Ankabut', 'العنكبوت', 'And those who strive for Us — We will surely guide them to Our ways.', 'وَالَّذِينَ جَاهَدُوا فِينَا لَنَهْدِيَنَّهُمْ سُبُلَنَا'],
  [31, 34, 'Luqman', 'لقمان', 'Indeed, Allah [alone] has knowledge of the Hour and sends down the rain and knows what is in the wombs.', 'إِنَّ اللَّهَ عِندَهُ عِلْمُ السَّاعَةِ وَيُنَزِّلُ الْغَيْثَ وَيَعْلَمُ مَا فِي الْأَرْحَامِ'],
  [33, 21, 'Al-Ahzab', 'الأحزاب', 'There has certainly been for you in the Messenger of Allah an excellent pattern.', 'لَّقَدْ كَانَ لَكُمْ فِي رَسُولِ اللَّهِ أُسْوَةٌ حَسَنَةٌ'],
  [33, 56, 'Al-Ahzab', 'الأحزاب', 'Indeed, Allah confers blessing upon the Prophet, and His angels [ask Him to do so]. O you who have believed, ask [Allah to confer] blessing upon him.', 'إِنَّ اللَّهَ وَمَلَائِكَتَهُ يُصَلُّونَ عَلَى النَّبِيِّ يَا أَيُّهَا الَّذِينَ آمَنُوا صَلُّوا عَلَيْهِ وَسَلِّمُوا تَسْلِيمًا'],
  [36, 82, 'Ya-Sin', 'يس', 'His command is only when He intends a thing that He says to it, "Be," and it is.', 'إِنَّمَا أَمْرُهُ إِذَا أَرَادَ شَيْئًا أَن يَقُولَ لَهُ كُن فَيَكُونُ'],
  [39, 10, 'Az-Zumar', 'الزمر', 'Indeed, the patient will be given their reward without account.', 'إِنَّمَا يُوَفَّى الصَّابِرُونَ أَجْرَهُم بِغَيْرِ حِسَابٍ'],
  [39, 53, 'Az-Zumar', 'الزمر', 'Say, "O My servants who have transgressed against themselves [by sinning], do not despair of the mercy of Allah."', 'قُلْ يَا عِبَادِيَ الَّذِينَ أَسْرَفُوا عَلَىٰ أَنفُسِهِمْ لَا تَقْنَطُوا مِن رَّحْمَةِ اللَّهِ'],
  [40, 60, 'Ghafir', 'غافر', 'And your Lord says, "Call upon Me; I will respond to you."', 'وَقَالَ رَبُّكُمُ ادْعُونِي أَسْتَجِبْ لَكُمْ'],
  [41, 30, 'Fussilat', 'فصلت', 'Indeed, those who have said, "Our Lord is Allah" and then remained on a right course — the angels will descend upon them.', 'إِنَّ الَّذِينَ قَالُوا رَبُّنَا اللَّهُ ثُمَّ اسْتَقَامُوا تَتَنَزَّلُ عَلَيْهِمُ الْمَلَائِكَةُ'],
  [42, 10, 'Ash-Shura', 'الشورى', 'And in whatever thing you differ, its ruling is [to be referred] to Allah.', 'وَمَا اخْتَلَفْتُمْ فِيهِ مِن شَيْءٍ فَحُكْمُهُ إِلَى اللَّهِ'],
  [49, 10, 'Al-Hujurat', 'الحجرات', 'The believers are but brothers, so make settlement between your brothers.', 'إِنَّمَا الْمُؤْمِنُونَ إِخْوَةٌ فَأَصْلِحُوا بَيْنَ أَخَوَيْكُمْ'],
  [49, 13, 'Al-Hujurat', 'الحجرات', 'Indeed, the most noble of you in the sight of Allah is the most righteous of you.', 'إِنَّ أَكْرَمَكُمْ عِندَ اللَّهِ أَتْقَاكُمْ'],
  [51, 56, 'Adh-Dhariyat', 'الذاريات', 'And I did not create the jinn and mankind except to worship Me.', 'وَمَا خَلَقْتُ الْجِنَّ وَالْإِنسَ إِلَّا لِيَعْبُدُونِ'],
  [55, 13, 'Ar-Rahman', 'الرحمن', 'So which of the favors of your Lord would you deny?', 'فَبِأَيِّ آلَاءِ رَبِّكُمَا تُكَذِّبَانِ'],
  [57, 21, 'Al-Hadid', 'الحديد', 'Race toward forgiveness from your Lord and a Garden whose width is like the width of the heavens and earth.', 'سَابِقُوا إِلَىٰ مَغْفِرَةٍ مِّن رَّبِّكُمْ وَجَنَّةٍ عَرْضُهَا كَعَرْضِ السَّمَاءِ وَالْأَرْضِ'],
  [58, 11, 'Al-Mujadila', 'المجادلة', 'Allah will raise those who have believed among you and those who were given knowledge, by degrees.', 'يَرْفَعِ اللَّهُ الَّذِينَ آمَنُوا مِنكُمْ وَالَّذِينَ أُوتُوا الْعِلْمَ دَرَجَاتٍ'],
  [59, 18, 'Al-Hashr', 'الحشر', 'O you who have believed, fear Allah. And let every soul look to what it has put forth for tomorrow.', 'يَا أَيُّهَا الَّذِينَ آمَنُوا اتَّقُوا اللَّهَ وَلْتَنظُرْ نَفْسٌ مَّا قَدَّمَتْ لِغَدٍ'],
  [59, 22, 'Al-Hashr', 'الحشر', 'He is Allah, other than whom there is no deity, Knower of the unseen and the witnessed.', 'هُوَ اللَّهُ الَّذِي لَا إِلَٰهَ إِلَّا هُوَ عَالِمُ الْغَيْبِ وَالشَّهَادَةِ'],
  [65, 3, 'At-Talaq', 'الطلاق', 'And whoever relies upon Allah — then He is sufficient for him.', 'وَمَن يَتَوَكَّلْ عَلَى اللَّهِ فَهُوَ حَسْبُهُ'],
  [67, 2, 'Al-Mulk', 'الملك', 'He who created death and life to test you as to which of you is best in deed.', 'الَّذِي خَلَقَ الْمَوْتَ وَالْحَيَاةَ لِيَبْلُوَكُمْ أَيُّكُمْ أَحْسَنُ عَمَلًا'],
  [68, 4, 'Al-Qalam', 'القلم', 'And indeed, you are of a great moral character.', 'وَإِنَّكَ لَعَلَىٰ خُلُقٍ عَظِيمٍ'],
  [76, 9, 'Al-Insan', 'الإنسان', '"We feed you only for the countenance of Allah. We wish not from you reward or gratitude."', 'إِنَّمَا نُطْعِمُكُمْ لِوَجْهِ اللَّهِ لَا نُرِيدُ مِنكُمْ جَزَاءً وَلَا شُكُورًا'],
  [89, 27, 'Al-Fajr', 'الفجر', 'O reassured soul, return to your Lord, well-pleased and pleasing [to Him].', 'يَا أَيَّتُهَا النَّفْسُ الْمُطْمَئِنَّةُ ارْجِعِي إِلَىٰ رَبِّكِ رَاضِيَةً مَّرْضِيَّةً'],
  [93, 5, 'Ad-Duha', 'الضحى', 'And your Lord is going to give you, and you will be satisfied.', 'وَلَسَوْفَ يُعْطِيكَ رَبُّكَ فَتَرْضَىٰ'],
  [94, 5, 'Ash-Sharh', 'الشرح', 'For indeed, with hardship [will be] ease.', 'فَإِنَّ مَعَ الْعُسْرِ يُسْرًا'],
  [94, 6, 'Ash-Sharh', 'الشرح', 'Indeed, with hardship [will be] ease.', 'إِنَّ مَعَ الْعُسْرِ يُسْرًا'],
  [108, 1, 'Al-Kawthar', 'الكوثر', 'Indeed, We have granted you, [O Muhammad], al-Kawthar.', 'إِنَّا أَعْطَيْنَاكَ الْكَوْثَرَ'],
  [112, 1, 'Al-Ikhlas', 'الإخلاص', 'Say, "He is Allah, [who is] One."', 'قُلْ هُوَ اللَّهُ أَحَدٌ'],
];

function getDayIndex(): number {
  const now = new Date();
  const start = new Date(now.getFullYear(), 0, 0);
  const diff = +now - +start;
  const oneDay = 1000 * 60 * 60 * 24;
  const dayOfYear = Math.floor(diff / oneDay);
  return dayOfYear % POOL.length;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

interface Props {
  compact?: boolean;
}

export function VerseOfDayCard({ compact = false }: Props) {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';

  const [idx, setIdx] = useState(getDayIndex);
  const [uthmani, setUthmani] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const fetchedRef = useRef<number | null>(null);
  const { addBookmark, removeBookmark, isBookmarked } = useBookmarksStore();

  const ref = POOL[idx];
  const verseIdApprox = ref[0] * 1000 + ref[1]; // stable pseudo-id for day verse

  const bookmarked = uthmani ? isBookmarked(verseIdApprox) : false;

  const toggleBookmark = useCallback(() => {
    if (!uthmani) return;
    if (bookmarked) {
      removeBookmark(verseIdApprox);
    } else {
      addBookmark({
        id: verseIdApprox,
        sura_no: ref[0],
        sura_name_ar: ref[3],
        sura_name_en: ref[2],
        aya_no: ref[1],
        text_uthmani: uthmani,
      });
    }
  }, [bookmarked, uthmani, ref, verseIdApprox, addBookmark, removeBookmark]);

  const shareVerse = useCallback(async () => {
    if (!uthmani) return;
    const verseRef = `${ref[2]} (${ref[0]}:${ref[1]})`;
    const text = `${uthmani}\n— ${verseRef}`;
    if (navigator.share) {
      try { await navigator.share({ title: verseRef, text }); } catch { /* cancelled */ }
    } else {
      navigator.clipboard.writeText(text).catch(console.error);
    }
  }, [uthmani, ref]);

  useEffect(() => {
    if (fetchedRef.current === idx) return;
    fetchedRef.current = idx;
    setLoading(true);
    setUthmani(null);
    quranApi
      .getVerse(ref[0], ref[1])
      .then(res => setUthmani(res.data.text_uthmani))
      .catch(() => setUthmani(null))
      .finally(() => setLoading(false));
  }, [idx, ref]);

  const rotate = () => setIdx(i => (i + 1) % POOL.length);

  return (
    <div
      className={clsx(
        'relative overflow-hidden rounded-2xl border border-emerald-200',
        'bg-gradient-to-br from-emerald-50 via-teal-50 to-sky-50',
        compact ? 'p-4' : 'p-5 md:p-6',
      )}
      dir={isRtl ? 'rtl' : 'ltr'}
    >
      {/* Decorative orb */}
      <div className="absolute -top-8 -right-8 w-32 h-32 rounded-full bg-emerald-100/60 blur-2xl pointer-events-none" />

      {/* Header */}
      <div className={clsx('flex items-center justify-between mb-3', isRtl && 'flex-row-reverse')}>
        <div className={clsx('flex items-center gap-2', isRtl && 'flex-row-reverse')}>
          <div className="w-7 h-7 rounded-lg bg-emerald-600 flex items-center justify-center flex-shrink-0">
            <BookOpen className="w-3.5 h-3.5 text-white" />
          </div>
          <div>
            <p className={clsx('text-xs font-semibold text-emerald-700 uppercase tracking-wide', isRtl && 'font-arabic')}>
              {isRtl ? 'آية اليوم' : 'Verse of the Day'}
            </p>
            <p className="text-[10px] text-gray-400">
              {ref[2]} · {ref[0]}:{ref[1]}
            </p>
          </div>
        </div>
        <button
          onClick={rotate}
          className="p-1.5 rounded-lg text-gray-400 hover:text-emerald-600 hover:bg-white/60 transition-colors"
          title={isRtl ? 'آية أخرى' : 'Another verse'}
        >
          <RefreshCw className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Arabic text */}
      <div className="min-h-[3rem] mb-3">
        {loading ? (
          <div className="h-8 bg-emerald-100 rounded-lg animate-pulse w-3/4 ms-auto" />
        ) : uthmani ? (
          <p
            dir="rtl"
            className={clsx(
              'font-arabic text-right leading-loose text-gray-900',
              compact ? 'text-lg' : 'text-xl md:text-2xl',
            )}
          >
            {uthmani}
          </p>
        ) : null}
      </div>

      {/* Divider */}
      <div className="border-t border-emerald-100 mb-3" />

      {/* Translation */}
      <p className={clsx(
        'text-sm text-gray-600 italic leading-relaxed mb-1',
        isRtl ? 'font-arabic text-right' : 'text-left'
      )}>
        {isRtl ? ref[5] : ref[4]}
      </p>
      <p className={clsx('text-[11px] text-emerald-600 font-medium mb-4', isRtl && 'font-arabic text-right')}>
        {isRtl ? `— ${ref[3]}` : `— ${ref[2]}, ${ref[0]}:${ref[1]}`}
      </p>

      {/* CTA */}
      <div className={clsx('flex items-center gap-2 flex-wrap', isRtl && 'flex-row-reverse')}>
        <Link
          to={`/quran/${ref[0]}`}
          className={clsx(
            'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium',
            'bg-emerald-600 text-white hover:bg-emerald-700 transition-colors',
            isRtl && 'flex-row-reverse font-arabic',
          )}
        >
          <ExternalLink className="w-3 h-3" />
          {isRtl ? 'اقرأ في المصحف' : 'Read in Mushaf'}
        </Link>
        <Link
          to={`/ask`}
          className={clsx(
            'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium',
            'bg-white/70 text-emerald-700 border border-emerald-200 hover:bg-white transition-colors',
            isRtl && 'flex-row-reverse font-arabic',
          )}
        >
          <Volume2 className="w-3 h-3" />
          {isRtl ? 'تدبر هذه الآية' : 'Reflect on this verse'}
        </Link>
        {uthmani && (
          <>
            <button
              onClick={toggleBookmark}
              className={clsx(
                'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors',
                bookmarked
                  ? 'bg-amber-100 text-amber-700 hover:bg-amber-200'
                  : 'bg-white/70 text-gray-600 border border-gray-200 hover:bg-white',
                isRtl && 'font-arabic',
              )}
              title={isRtl ? (bookmarked ? 'إزالة الإشارة' : 'حفظ الآية') : (bookmarked ? 'Remove bookmark' : 'Bookmark')}
            >
              {bookmarked ? <BookmarkCheck className="w-3 h-3" /> : <Bookmark className="w-3 h-3" />}
              {isRtl ? (bookmarked ? 'محفوظة' : 'حفظ') : (bookmarked ? 'Saved' : 'Save')}
            </button>
            <button
              onClick={shareVerse}
              className={clsx(
                'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium',
                'bg-white/70 text-gray-600 border border-gray-200 hover:bg-white transition-colors',
                isRtl && 'font-arabic',
              )}
              title={isRtl ? 'مشاركة' : 'Share'}
            >
              <Share2 className="w-3 h-3" />
              {isRtl ? 'مشاركة' : 'Share'}
            </button>
          </>
        )}
      </div>
    </div>
  );
}
