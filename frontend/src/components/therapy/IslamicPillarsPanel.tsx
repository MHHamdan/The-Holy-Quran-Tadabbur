/**
 * IslamicPillarsPanel — Therapy page section
 *
 * Displays curated Quranic verses for the five pillars of Islam and key
 * social virtues (birr al-walidayn, neighbor rights, truthfulness, etc.).
 *
 * Arabic verse text is fetched from the backend API so the Uthmani rasm
 * never appears as a string literal in source code (CLAUDE.md constraint).
 */

import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import {
  Moon,
  Sunrise,
  HandCoins,
  Navigation,
  Users,
  Home,
  Shield,
  Star,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Loader2,
  BookOpen,
} from 'lucide-react';
import clsx from 'clsx';
import { useLanguageStore } from '../../stores/languageStore';
import { quranApi } from '../../lib/api';

// ---------------------------------------------------------------------------
// Data types
// ---------------------------------------------------------------------------

interface PillarVerse {
  surah: number;
  ayah: number;
  ref: string;
  surah_name_en: string;
  surah_name_ar: string;
  translation_en: string;
  translation_ar: string;
  explanation_en: string;
  explanation_ar: string;
}

interface Pillar {
  key: string;
  icon: React.ElementType;
  colorClass: string;
  bgClass: string;
  borderClass: string;
  headerBg: string;
  label_en: string;
  label_ar: string;
  intro_en: string;
  intro_ar: string;
  verses: PillarVerse[];
}

// ---------------------------------------------------------------------------
// Canonical verse data — translations & explanations only (no Uthmani rasm)
// Arabic text is fetched from the API when each pillar is opened.
// ---------------------------------------------------------------------------

const PILLARS: Pillar[] = [
  // ── 1. Prayer ─────────────────────────────────────────────────────────────
  {
    key: 'salah',
    icon: Sunrise,
    colorClass: 'text-amber-600',
    bgClass: 'bg-amber-50',
    borderClass: 'border-amber-300',
    headerBg: 'bg-amber-50',
    label_en: 'Prayer (Salah)',
    label_ar: 'الصلاة',
    intro_en: 'Salah is the second pillar of Islam — a direct, structured conversation with Allah five times every day. It is both an obligation and a mercy.',
    intro_ar: 'الصلاة هي الركن الثاني من أركان الإسلام — محادثة مباشرة ومنظمة مع الله خمس مرات كل يوم، فريضة ورحمة في آنٍ واحد.',
    verses: [
      {
        surah: 2, ayah: 45,
        ref: '2:45', surah_name_en: 'Al-Baqarah', surah_name_ar: 'البقرة',
        translation_en: '"And seek help through patience and prayer; and indeed, it is difficult except for the humbly submissive [to Allah]."',
        translation_ar: '"وَاسْتَعِينُواْ بِالصَّبْرِ وَالصَّلاَةِ وَإِنَّهَا لَكَبِيرَةٌ إِلاَّ عَلَى الْخَاشِعِينَ"',
        explanation_en: 'Allah pairs prayer with patience as the twin remedies for hardship. Prayer is the sanctuary you return to when the world overwhelms you.',
        explanation_ar: 'قرن الله الصلاة بالصبر كعلاجَيْن للشدة. الصلاة هي الملاذ الذي تعود إليه حين يثقل عليك العالم.',
      },
      {
        surah: 2, ayah: 238,
        ref: '2:238', surah_name_en: 'Al-Baqarah', surah_name_ar: 'البقرة',
        translation_en: '"Maintain with care the [obligatory] prayers and [in particular] the middle prayer and stand before Allah, devoutly obedient."',
        translation_ar: '"حَافِظُواْ عَلَى الصَّلَوَاتِ وَالصَّلاَةِ الْوُسْطَى وَقُومُواْ لِلّهِ قَانِتِينَ"',
        explanation_en: 'Allah specifically commands guarding the prayers — not just performing them, but protecting them as something precious. The middle prayer (Asr) is emphasised for its vulnerability during the busy afternoon.',
        explanation_ar: 'أمر الله بالمحافظة على الصلوات — لا أداءها فحسب، بل صونها كشيء ثمين. تُؤكَّد صلاة الوسطى (العصر) لوقوعها في ذروة انشغال النهار.',
      },
      {
        surah: 29, ayah: 45,
        ref: '29:45', surah_name_en: 'Al-Ankabut', surah_name_ar: 'العنكبوت',
        translation_en: '"...establish prayer. Indeed, prayer prohibits immorality and wrongdoing, and the remembrance of Allah is greater. And Allah knows what you do."',
        translation_ar: '"أَقِمِ الصَّلَاةَ ۖ إِنَّ الصَّلَاةَ تَنْهَى عَنِ الْفَحْشَاءِ وَالْمُنكَرِ وَلَذِكْرُ اللَّهِ أَكْبَرُ"',
        explanation_en: 'A properly performed prayer, lived and internalised, shields you from immorality. Scholars say: if your prayer is not pulling you away from sin, examine the quality of your prayer.',
        explanation_ar: 'الصلاة المُقامة حقاً — المُعاشة والمُستوعبة — تحجز عن الفحشاء. قال العلماء: إن لم تنهَك صلاتُك عن الذنوب فراجع جودة صلاتك.',
      },
      {
        surah: 20, ayah: 14,
        ref: '20:14', surah_name_en: 'Ta-Ha', surah_name_ar: 'طه',
        translation_en: '"Indeed, I am Allah. There is no deity except Me, so worship Me and establish prayer for My remembrance."',
        translation_ar: '"إِنَّنِي أَنَا اللَّهُ لَا إِلَهَ إِلَّا أَنَا فَاعْبُدْنِي وَأَقِمِ الصَّلَاةَ لِذِكْرِي"',
        explanation_en: 'Allah\'s direct command to Moses — and through Moses, to all of humanity. Prayer is the living embodiment of lā ilāha illallāh: it is remembrance made physical.',
        explanation_ar: 'الأمر الإلهي المباشر لموسى — ومن خلاله لكل البشر. الصلاة هي التجسيد الحي للا إله إلا الله: ذكر جُعل جسداً وحركة.',
      },
      {
        surah: 4, ayah: 103,
        ref: '4:103', surah_name_en: 'An-Nisa', surah_name_ar: 'النساء',
        translation_en: '"...Indeed, prayer has been decreed upon the believers a decree of specified times."',
        translation_ar: '"إِنَّ الصَّلَاةَ كَانَتْ عَلَى الْمُؤْمِنِينَ كِتَابًا مَّوْقُوتًا"',
        explanation_en: 'Prayer is bound to specific times — dawn, midday, afternoon, sunset, night. These five anchors divide the day into segments of conscious connection, preventing the heart from drifting into heedlessness.',
        explanation_ar: 'الصلاة مرتبطة بأوقات محددة — الفجر والظهر والعصر والمغرب والعشاء. هذه المراسي الخمس تُقسّم اليوم إلى مقاطع من التواصل الواعي، تمنع القلب من الغفلة.',
      },
    ],
  },

  // ── 2. Fasting ────────────────────────────────────────────────────────────
  {
    key: 'sawm',
    icon: Moon,
    colorClass: 'text-indigo-600',
    bgClass: 'bg-indigo-50',
    borderClass: 'border-indigo-300',
    headerBg: 'bg-indigo-50',
    label_en: 'Fasting (Sawm)',
    label_ar: 'الصيام',
    intro_en: 'Fasting in Ramadan is the fourth pillar — a month-long school of discipline, gratitude, and nearness to Allah through voluntary restraint.',
    intro_ar: 'صيام رمضان هو الركن الرابع — مدرسة شهرية للانضباط والامتنان والقرب من الله عبر ضبط النفس.',
    verses: [
      {
        surah: 2, ayah: 183,
        ref: '2:183', surah_name_en: 'Al-Baqarah', surah_name_ar: 'البقرة',
        translation_en: '"O you who have believed, decreed upon you is fasting as it was decreed upon those before you that you may become righteous."',
        translation_ar: '"يَا أَيُّهَا الَّذِينَ آمَنُواْ كُتِبَ عَلَيْكُمُ الصِّيَامُ كَمَا كُتِبَ عَلَى الَّذِينَ مِن قَبْلِكُمْ لَعَلَّكُمْ تَتَّقُونَ"',
        explanation_en: 'Allah links fasting directly to taqwa (God-consciousness). The purpose is not hunger — it is the spiritual transformation that hunger creates: humility, empathy, and a reset of priorities.',
        explanation_ar: 'ربط الله الصيام مباشرة بالتقوى. الغاية ليست الجوع — بل التحول الروحي الذي يولّده: التواضع والتعاطف وإعادة ترتيب الأولويات.',
      },
      {
        surah: 2, ayah: 185,
        ref: '2:185', surah_name_en: 'Al-Baqarah', surah_name_ar: 'البقرة',
        translation_en: '"The month of Ramadhan [is that] in which was revealed the Quran, a guidance for the people and clear proofs of guidance and criterion."',
        translation_ar: '"شَهْرُ رَمَضَانَ الَّذِيَ أُنزِلَ فِيهِ الْقُرْآنُ هُدًى لِّلنَّاسِ وَبَيِّنَاتٍ مِّنَ الْهُدَى وَالْفُرْقَانِ"',
        explanation_en: 'Ramadan is the month the Quran descended. Every fast is an act of remembrance of the greatest gift — divine guidance. The Quran and fasting are permanently linked in this verse.',
        explanation_ar: 'رمضان هو الشهر الذي نزل فيه القرآن. كل إمساك هو استحضار لأعظم نعمة — الهداية الإلهية. القرآن والصيام مرتبطان دائماً في هذه الآية.',
      },
      {
        surah: 2, ayah: 187,
        ref: '2:187', surah_name_en: 'Al-Baqarah', surah_name_ar: 'البقرة',
        translation_en: '"...Allah knows that you used to deceive yourselves, so He accepted your repentance and forgave you. So now, have relations with them and seek what Allah has decreed for you..."',
        translation_ar: '"عَلِمَ اللّهُ أَنَّكُمْ كُنتُمْ تَخْتَانُونَ أَنفُسَكُمْ فَتَابَ عَلَيْكُمْ وَعَفَا عَنكُمْ"',
        explanation_en: 'Allah demonstrates His mercy in the very legislation of fasting — He knew human weakness and responded with gentleness, giving lawful permission and complete forgiveness.',
        explanation_ar: 'أظهر الله رحمته في تشريع الصيام ذاته — عرف ضعف الإنسان فأجابه بالرفق، مانحاً الحلال والمغفرة الكاملة.',
      },
      {
        surah: 97, ayah: 1,
        ref: '97:1–3', surah_name_en: 'Al-Qadr', surah_name_ar: 'القدر',
        translation_en: '"Indeed, We sent the Quran down during the Night of Decree. And what can make you know what is the Night of Decree? The Night of Decree is better than a thousand months."',
        translation_ar: '"إِنَّا أَنزَلْنَاهُ فِي لَيْلَةِ الْقَدْرِ ۝ وَمَا أَدْرَاكَ مَا لَيْلَةُ الْقَدْرِ ۝ لَيْلَةُ الْقَدْرِ خَيْرٌ مِّنْ أَلْفِ شَهْرٍ"',
        explanation_en: 'Hidden inside the last ten nights of Ramadan is a single night worth 83+ years. Fasting the month is the price of admission to the possibility of Laylat al-Qadr.',
        explanation_ar: 'مخبأة في العشر الأواخر من رمضان ليلة تساوي أكثر من 83 عاماً. صيام الشهر هو ثمن الوصول إلى احتمال ليلة القدر.',
      },
    ],
  },

  // ── 3. Zakat ──────────────────────────────────────────────────────────────
  {
    key: 'zakat',
    icon: HandCoins,
    colorClass: 'text-emerald-600',
    bgClass: 'bg-emerald-50',
    borderClass: 'border-emerald-300',
    headerBg: 'bg-emerald-50',
    label_en: 'Zakat (Obligatory Charity)',
    label_ar: 'الزكاة',
    intro_en: 'Zakat is the third pillar — 2.5% of savings above the nisab, distributed to eight categories of recipients. It purifies wealth and the soul simultaneously.',
    intro_ar: 'الزكاة هي الركن الثالث — ٢.٥٪ من المدخرات فوق النصاب، تُوزَّع على ثمانية أصناف. تُطهّر المال والنفس معاً.',
    verses: [
      {
        surah: 2, ayah: 43,
        ref: '2:43', surah_name_en: 'Al-Baqarah', surah_name_ar: 'البقرة',
        translation_en: '"And establish prayer and give zakah and bow with those who bow [in worship]."',
        translation_ar: '"وَأَقِيمُواْ الصَّلاَةَ وَآتُواْ الزَّكَاةَ وَارْكَعُواْ مَعَ الرَّاكِعِينَ"',
        explanation_en: 'Throughout the Quran, prayer and zakat appear together — spiritual connection to Allah and material connection to community are inseparable in Islam.',
        explanation_ar: 'يتكرر قرن الصلاة والزكاة في القرآن — الصلة الروحية بالله والصلة المادية بالمجتمع لا تنفصلان في الإسلام.',
      },
      {
        surah: 9, ayah: 103,
        ref: '9:103', surah_name_en: 'At-Tawbah', surah_name_ar: 'التوبة',
        translation_en: '"Take from their wealth a charity by which you purify them and cause them increase, and invoke [Allah\'s blessings] upon them. Indeed, your invocations are reassurance for them."',
        translation_ar: '"خُذْ مِنْ أَمْوَالِهِمْ صَدَقَةً تُطَهِّرُهُمْ وَتُزَكِّيهِم بِهَا وَصَلِّ عَلَيْهِمْ ۖ إِنَّ صَلَاتَكَ سَكَنٌ لَّهُمْ"',
        explanation_en: 'Zakat does not diminish wealth — the Arabic root zakā means both to increase and to purify. When you give, Allah purifies the remainder and multiplies your sustenance.',
        explanation_ar: 'الزكاة لا تنقص المال — جذر "زكا" في العربية يعني التزكية والنمو معاً. حين تُعطي، يُطهّر الله الباقي ويُبارك في رزقك.',
      },
      {
        surah: 2, ayah: 261,
        ref: '2:261', surah_name_en: 'Al-Baqarah', surah_name_ar: 'البقرة',
        translation_en: '"The example of those who spend their wealth in the way of Allah is like a seed [of grain] that sprouts seven spikes; in every spike is a hundred grains. And Allah multiplies [His reward] for whom He wills."',
        translation_ar: '"مَّثَلُ الَّذِينَ يُنفِقُونَ أَمْوَالَهُمْ فِي سَبِيلِ اللّهِ كَمَثَلِ حَبَّةٍ أَنبَتَتْ سَبْعَ سَنَابِلَ فِي كُلِّ سُنبُلَةٍ مِّئَةُ حَبَّةٍ"',
        explanation_en: 'One seed → seven spikes → 700 grains. Allah uses the geometry of agriculture to show how generosity compounds. The minimum return is 700-fold; for some, Allah multiplies further still.',
        explanation_ar: 'حبة واحدة → سبع سنابل → ٧٠٠ حبة. استخدم الله هندسة الزراعة ليُري كيف تتضاعف السخاوة. الحد الأدنى سبعمائة ضعف؛ ولبعضهم يُضاعف الله أكثر.',
      },
      {
        surah: 2, ayah: 177,
        ref: '2:177', surah_name_en: 'Al-Baqarah', surah_name_ar: 'البقرة',
        translation_en: '"...and [true] righteousness is [in] one who gives wealth, in spite of love for it, to relatives, orphans, the needy, the traveler, those who ask [for help], and for freeing slaves."',
        translation_ar: '"وَآتَى الْمَالَ عَلَى حُبِّهِ ذَوِي الْقُرْبَى وَالْيَتَامَى وَالْمَسَاكِينَ وَابْنَ السَّبِيلِ وَالسَّائِلِينَ وَفِي الرِّقَابِ"',
        explanation_en: 'True birr (righteousness) is to give even when you love what you\'re giving. The Quran names six categories of recipients — zakat channels wealth to those society has forgotten.',
        explanation_ar: 'البر الحق أن تُعطي وأنت تحب ما تُعطيه. سمّى القرآن ستة أصناف من المستحقين — تُوصل الزكاة المال إلى من نسيهم المجتمع.',
      },
    ],
  },

  // ── 4. Hajj ───────────────────────────────────────────────────────────────
  {
    key: 'hajj',
    icon: Navigation,
    colorClass: 'text-teal-600',
    bgClass: 'bg-teal-50',
    borderClass: 'border-teal-300',
    headerBg: 'bg-teal-50',
    label_en: 'Hajj (Pilgrimage)',
    label_ar: 'الحج',
    intro_en: 'Hajj is the fifth pillar — a once-in-a-lifetime journey to Makkah that strips away all social rank, leaving every pilgrim equal before Allah in white ihram.',
    intro_ar: 'الحج هو الركن الخامس — رحلة العمر إلى مكة تُجرّد من كل مكانة اجتماعية، وتترك كل حاج متساوياً أمام الله في بياض الإحرام.',
    verses: [
      {
        surah: 3, ayah: 97,
        ref: '3:97', surah_name_en: 'Al-Imran', surah_name_ar: 'آل عمران',
        translation_en: '"...And [due] to Allah from the people is a pilgrimage to the House — for whoever is able to find thereto a way. But whoever disbelieves — then indeed, Allah is free from need of the worlds."',
        translation_ar: '"وَلِلّهِ عَلَى النَّاسِ حِجُّ الْبَيْتِ مَنِ اسْتَطَاعَ إِلَيْهِ سَبِيلاً وَمَن كَفَرَ فَإِنَّ اللَّه غَنِيٌّ عَنِ الْعَالَمِينَ"',
        explanation_en: 'Hajj is a duty owed to Allah — not a favour to Him. It is obligatory once in a lifetime for whoever has the means. The condition "able" is from Allah\'s mercy, not leniency.',
        explanation_ar: 'الحج فريضة لله — ليست معروفاً تُسدى له. واجبة مرة في العمر لمن استطاع. شرط "الاستطاعة" من رحمة الله لا من التساهل.',
      },
      {
        surah: 22, ayah: 27,
        ref: '22:27', surah_name_en: 'Al-Hajj', surah_name_ar: 'الحج',
        translation_en: '"And proclaim to the people the Hajj [pilgrimage]; they will come to you on foot and on every lean camel; they will come from every distant pass."',
        translation_ar: '"وَأَذِّن فِي النَّاسِ بِالْحَجِّ يَأْتُوكَ رِجَالًا وَعَلَى كُلِّ ضَامِرٍ يَأْتِينَ مِن كُلِّ فَجٍّ عَمِيقٍ"',
        explanation_en: 'Allah commanded Ibrahim to announce Hajj — and billions answered that call across 4,000 years. Every pilgrim is a fulfilment of that one divine command. You are part of an unbroken human river.',
        explanation_ar: 'أمر الله إبراهيم بأذان الحج — فأجابه المليارات عبر أربعة آلاف عام. كل حاج استجابة لأمر إلهي واحد. أنتَ جزء من نهر بشري لا ينقطع.',
      },
      {
        surah: 2, ayah: 197,
        ref: '2:197', surah_name_en: 'Al-Baqarah', surah_name_ar: 'البقرة',
        translation_en: '"Hajj is [during] well-known months, so whoever has made Hajj obligatory upon himself therein — there is [to be for him] no sexual relations, no disobedience, and no disputing during Hajj."',
        translation_ar: '"الْحَجُّ أَشْهُرٌ مَّعْلُومَاتٌ فَمَن فَرَضَ فِيهِنَّ الْحَجَّ فَلَا رَفَثَ وَلَا فُسُوقَ وَلَا جِدَالَ فِي الْحَجِّ"',
        explanation_en: 'The three prohibitions — intimacy, disobedience, and arguing — frame Hajj as a total reset. You arrive in the world\'s biggest congregation and leave it in the deepest peace.',
        explanation_ar: 'المحظورات الثلاثة — الرفث والفسوق والجدال — تُؤطّر الحج كإعادة ضبط كاملة. تصل في أكبر تجمع بشري وتغادره في أعمق سلام.',
      },
      {
        surah: 22, ayah: 29,
        ref: '22:29', surah_name_en: 'Al-Hajj', surah_name_ar: 'الحج',
        translation_en: '"Then let them end their untidiness and fulfil their vows and perform Tawaf around the ancient House."',
        translation_ar: '"ثُمَّ لْيَقْضُوا تَفَثَهُمْ وَلْيُوفُوا نُذُورَهُمْ وَلْيَطَّوَّفُوا بِالْبَيْتِ الْعَتِيقِ"',
        explanation_en: 'The Ka\'bah is called the "Ancient House" — the oldest place of worship on earth. Tawaf is circling the axis of the spiritual world, the direction all Muslims face in prayer.',
        explanation_ar: 'يُسمّى الكعبة "البيت العتيق" — أقدم بيت عبادة على وجه الأرض. الطواف هو الدوران حول محور العالم الروحي، الاتجاه الذي يستقبله كل مسلم في صلاته.',
      },
    ],
  },

  // ── 5. Honoring Parents ───────────────────────────────────────────────────
  {
    key: 'birr_walidayn',
    icon: Users,
    colorClass: 'text-rose-600',
    bgClass: 'bg-rose-50',
    borderClass: 'border-rose-300',
    headerBg: 'bg-rose-50',
    label_en: 'Honoring Parents (Birr al-Walidayn)',
    label_ar: 'بر الوالدين',
    intro_en: 'In the Quran, obedience to parents is mentioned immediately after worshipping Allah — a deliberate pairing that elevates parental rights to the second-highest rank in Islam.',
    intro_ar: 'في القرآن، يأتي طاعة الوالدين مباشرة بعد عبادة الله — اقتران مقصود يرفع حق الوالدين إلى المرتبة الثانية في الإسلام.',
    verses: [
      {
        surah: 17, ayah: 23,
        ref: '17:23', surah_name_en: 'Al-Isra', surah_name_ar: 'الإسراء',
        translation_en: '"Your Lord has decreed that you worship none but Him, and that you be kind to parents. Whether one or both of them reach old age [while] with you, say not to them [so much as] \'uff\' and do not repel them but speak to them a noble word."',
        translation_ar: '"وَقَضَى رَبُّكَ أَلاَّ تَعْبُدُواْ إِلاَّ إِيَّاهُ وَبِالْوَالِدَيْنِ إِحْسَاناً إِمَّا يَبْلُغَنَّ عِندَكَ الْكِبَرَ أَحَدُهُمَا أَوْ كِلاَهُمَا فَلاَ تَقُل لَّهُمَا أُفٍّ"',
        explanation_en: 'Allah prohibits even the smallest expression of irritation — the Arabic "uff" (a sigh of annoyance) is the minimum. If even that is forbidden, everything harsher is forbidden with greater force.',
        explanation_ar: 'نهى الله حتى عن أصغر تعبير عن الضيق — "أف" في العربية هي الحد الأدنى. فإذا كان هذا محرماً، فكل ما هو أشد حرمةً بطريق الأولى.',
      },
      {
        surah: 17, ayah: 24,
        ref: '17:24', surah_name_en: 'Al-Isra', surah_name_ar: 'الإسراء',
        translation_en: '"And lower to them the wing of humility out of mercy and say: \'My Lord, have mercy upon them as they brought me up [when I was] small.\'"',
        translation_ar: '"وَاخْفِضْ لَهُمَا جَنَاحَ الذُّلِّ مِنَ الرَّحْمَةِ وَقُل رَّبِّ ارْحَمْهُمَا كَمَا رَبَّيَانِي صَغِيراً"',
        explanation_en: 'The du\'a for parents is embedded directly in the Quran. Allah did not just command kindness — He gave you the exact words to pray for them. Make this du\'a after every prayer.',
        explanation_ar: 'الدعاء للوالدين موجود مباشرة في القرآن. لم يأمر الله بالبر فحسب — بل أعطاك الكلمات الحرفية للدعاء لهما. اجعل هذا الدعاء بعد كل صلاة.',
      },
      {
        surah: 31, ayah: 14,
        ref: '31:14', surah_name_en: 'Luqman', surah_name_ar: 'لقمان',
        translation_en: '"And We have enjoined upon man [care] for his parents. His mother carried him, [increasing her] in weakness upon weakness, and his weaning is in two years. Be grateful to Me and to your parents; to Me is the [final] destination."',
        translation_ar: '"وَوَصَّيْنَا الْإِنسَانَ بِوَالِدَيْهِ حَمَلَتْهُ أُمُّهُ وَهْنًا عَلَى وَهْنٍ وَفِصَالُهُ فِي عَامَيْنِ أَنِ اشْكُرْ لِي وَلِوَالِدَيْكَ إِلَيَّ الْمَصِيرُ"',
        explanation_en: '"Weakness upon weakness" — the Quran acknowledges the cost of motherhood in raw, physical terms. Gratitude to parents is listed alongside gratitude to Allah. They are paired duties.',
        explanation_ar: '"وهناً على وهن" — يعترف القرآن بثمن الأمومة بعبارات صريحة جسدية. شكر الوالدين مذكور إلى جانب شكر الله. هما واجبان متقارنان.',
      },
      {
        surah: 46, ayah: 15,
        ref: '46:15', surah_name_en: 'Al-Ahqaf', surah_name_ar: 'الأحقاف',
        translation_en: '"And We have enjoined upon man, to his parents, good treatment. His mother carried him with hardship and gave birth to him with hardship, and his gestation and weaning [period] is thirty months."',
        translation_ar: '"وَوَصَّيْنَا الْإِنسَانَ بِوَالِدَيْهِ إِحْسَانًا حَمَلَتْهُ أُمُّهُ كُرْهًا وَوَضَعَتْهُ كُرْهًا وَحَمْلُهُ وَفِصَالُهُ ثَلَاثُونَ شَهْرًا"',
        explanation_en: 'Ihsān — the highest excellence of good — is the standard Allah sets for parental treatment. Not just "kindness," but the very best you are capable of.',
        explanation_ar: 'الإحسان — أعلى درجات الفعل الحسن — هو المعيار الذي وضعه الله للتعامل مع الوالدين. ليس مجرد "اللطف"، بل أفضل ما تستطيعه.',
      },
      {
        surah: 4, ayah: 36,
        ref: '4:36', surah_name_en: 'An-Nisa', surah_name_ar: 'النساء',
        translation_en: '"Worship Allah and associate nothing with Him, and to parents do good, and to relatives, orphans, the needy, the near neighbor, the far neighbor, the companion at your side, the traveler, and those whom your right hands possess."',
        translation_ar: '"وَاعْبُدُواْ اللّهَ وَلاَ تُشْرِكُواْ بِهِ شَيْئاً وَبِالْوَالِدَيْنِ إِحْسَاناً وَبِذِي الْقُرْبَى وَالْيَتَامَى وَالْمَسَاكِينِ وَالْجَارِ ذِي الْقُرْبَى وَالْجَارِ الْجُنُبِ"',
        explanation_en: 'This single verse is a complete social map: from Allah → parents → family → orphans → the poor → near neighbor → far neighbor → travel companion → subordinates. A hierarchy of care radiating outward from the centre.',
        explanation_ar: 'هذه الآية وحدها خريطة اجتماعية كاملة: من الله → الوالدين → الأسرة → الأيتام → المساكين → الجار القريب → الجار البعيد → صاحب السفر → المملوكين. تسلسل رعاية يشعّ للخارج من المركز.',
      },
    ],
  },

  // ── 6. Neighborhood Rights ────────────────────────────────────────────────
  {
    key: 'neighbor',
    icon: Home,
    colorClass: 'text-sky-600',
    bgClass: 'bg-sky-50',
    borderClass: 'border-sky-300',
    headerBg: 'bg-sky-50',
    label_en: 'Neighbor Rights (Ḥaqq al-Jār)',
    label_ar: 'حق الجار',
    intro_en: 'The Quran and authentic Sunnah place neighbor rights on a uniquely high level — the Prophet ﷺ said Jibreel kept recommending neighbors until he thought they would inherit from each other.',
    intro_ar: 'رفع القرآن والسنة الصحيحة حق الجار إلى مستوى بالغ الأهمية — قال النبي ﷺ: "ما زال جبريل يوصيني بالجار حتى ظننت أنه سيُورّثه".',
    verses: [
      {
        surah: 4, ayah: 36,
        ref: '4:36 (neighbor portion)', surah_name_en: 'An-Nisa', surah_name_ar: 'النساء',
        translation_en: '"...and [be good to] the near neighbor and the far neighbor and the companion at your side and the traveler and those whom your right hands possess."',
        translation_ar: '"وَالْجَارِ ذِي الْقُرْبَى وَالْجَارِ الْجُنُبِ وَالصَّاحِبِ بِالجَنبِ وَابْنِ السَّبِيلِ"',
        explanation_en: 'Two types of neighbors: the close neighbor (kin or nearby) and the far neighbor (non-kin, more distant). Both carry rights. Distance and relationship do not diminish the obligation of ihsān.',
        explanation_ar: 'نوعان من الجيران: الجار ذو القربى (القريب أو المجاور) والجار الجنب (غير ذي القربى أو الأبعد). لكليهما حقوق. المسافة والعلاقة لا تُقلّلان من واجب الإحسان.',
      },
      {
        surah: 2, ayah: 83,
        ref: '2:83', surah_name_en: 'Al-Baqarah', surah_name_ar: 'البقرة',
        translation_en: '"...and speak to people good [words] and establish prayer and give zakah." Then you turned away, except a few of you, and you were refusing.',
        translation_ar: '"وَقُولُواْ لِلنَّاسِ حُسْناً وَأَقِيمُواْ الصَّلاَةَ وَآتُواْ الزَّكَاةَ"',
        explanation_en: '"Speak good to people" — this is not limited to eloquence but to intention. A kind word to your neighbor is a deed registered with Allah. Most harm to neighbors begins with harmful speech.',
        explanation_ar: '"قولوا للناس حسناً" — لا يقتصر هذا على البلاغة بل على النية. الكلمة الطيبة لجارك عمل مُسجَّل عند الله. معظم الأذى الواقع على الجيران يبدأ بالكلام المسيء.',
      },
      {
        surah: 49, ayah: 12,
        ref: '49:12', surah_name_en: 'Al-Hujurat', surah_name_ar: 'الحجرات',
        translation_en: '"O you who have believed, avoid much [negative] assumption. Indeed, some assumption is sin. And do not spy or backbite each other. Would one of you like to eat the flesh of his brother when dead? You would detest it."',
        translation_ar: '"يَا أَيُّهَا الَّذِينَ آمَنُوا اجْتَنِبُوا كَثِيرًا مِّنَ الظَّنِّ إِنَّ بَعْضَ الظَّنِّ إِثْمٌ وَلَا تَجَسَّسُوا وَلَا يَغْتَب بَّعْضُكُم بَعْضًا"',
        explanation_en: 'Three neighbor-destroyers: bad suspicion, spying, and backbiting. Allah uses the visceral image of eating a corpse to communicate how repulsive backbiting is — you consume someone who cannot defend themselves.',
        explanation_ar: 'ثلاثة مُدمِّرة للجوار: سوء الظن، والتجسس، والغيبة. استخدم الله صورة الأكل من الجيفة ليُعبّر عن بشاعة الغيبة — تأكل من لا يستطيع الدفاع عن نفسه.',
      },
      {
        surah: 49, ayah: 11,
        ref: '49:11', surah_name_en: 'Al-Hujurat', surah_name_ar: 'الحجرات',
        translation_en: '"O you who have believed, let not a people ridicule [another] people; perhaps they may be better than them... And do not insult one another and do not call each other by [offensive] nicknames."',
        translation_ar: '"يَا أَيُّهَا الَّذِينَ آمَنُوا لَا يَسْخَرْ قَوْمٌ مِّن قَوْمٍ عَسَى أَن يَكُونُوا خَيْرًا مِّنْهُمْ وَلَا تَلْمِزُوا أَنفُسَكُمْ وَلَا تَنَابَزُوا بِالْأَلْقَابِ"',
        explanation_en: 'Mockery, slander, and demeaning nicknames poison the community. Note "perhaps they are better than you" — the one you mock may have a rank with Allah that you do not have.',
        explanation_ar: 'السخرية والتلمز والتنابز بالألقاب تُسمّم المجتمع. لاحظ "عسى أن يكونوا خيراً منهم" — من تسخر منه قد تكون له مرتبة عند الله لا تملكها.',
      },
    ],
  },

  // ── 7. Truthfulness & Trust ───────────────────────────────────────────────
  {
    key: 'sidq',
    icon: Shield,
    colorClass: 'text-violet-600',
    bgClass: 'bg-violet-50',
    borderClass: 'border-violet-300',
    headerBg: 'bg-violet-50',
    label_en: 'Truthfulness & Trust (Ṣidq & Amānah)',
    label_ar: 'الصدق والأمانة',
    intro_en: 'The Prophet ﷺ was known as Al-Sadiq Al-Amin (the Truthful, the Trustworthy) before revelation. Truthfulness is the foundation of character; without it, all other virtues are undermined.',
    intro_ar: 'عُرف النبي ﷺ بالصادق الأمين قبل البعثة. الصدق أساس الشخصية؛ بدونه تنهار كل الفضائل الأخرى.',
    verses: [
      {
        surah: 9, ayah: 119,
        ref: '9:119', surah_name_en: 'At-Tawbah', surah_name_ar: 'التوبة',
        translation_en: '"O you who have believed, fear Allah and be with the truthful."',
        translation_ar: '"يَا أَيُّهَا الَّذِينَ آمَنُواْ اتَّقُواْ اللّهَ وَكُونُواْ مَعَ الصَّادِقِينَ"',
        explanation_en: 'A short, powerful command: be WITH the truthful — meaning seek their company, imitate them, align yourself with them. Taqwa and ṣidq are here intertwined: you cannot fully have one without the other.',
        explanation_ar: 'أمر قصير وقوي: كونوا مع الصادقين — أي ابتغوا صحبتهم وتأسّوا بهم وانحازوا إليهم. التقوى والصدق مضفوران هنا: لا يكتمل أحدهما دون الآخر.',
      },
      {
        surah: 33, ayah: 70,
        ref: '33:70', surah_name_en: 'Al-Ahzab', surah_name_ar: 'الأحزاب',
        translation_en: '"O you who have believed, fear Allah and speak words of appropriate justice. He will [then] amend for you your deeds and forgive you your sins."',
        translation_ar: '"يَا أَيُّهَا الَّذِينَ آمَنُوا اتَّقُوا اللَّهَ وَقُولُوا قَوْلًا سَدِيدًا ۝ يُصْلِحْ لَكُمْ أَعْمَالَكُمْ وَيَغْفِرْ لَكُمْ ذُنُوبَكُمْ"',
        explanation_en: 'Qawlan sadidan — firm, upright, correct speech — is directly linked to amal ṣaliḥ (good deeds). Allah says: speak rightly, and I will correct your deeds. Speech is the foundation of action.',
        explanation_ar: 'قولاً سديداً — كلام راسخ مستقيم صحيح — مرتبط مباشرة بالعمل الصالح. يقول الله: انطقوا صواباً، وسأُصلح أعمالكم. الكلام أساس الفعل.',
      },
      {
        surah: 4, ayah: 58,
        ref: '4:58', surah_name_en: 'An-Nisa', surah_name_ar: 'النساء',
        translation_en: '"Indeed, Allah commands you to render trusts to whom they are due and when you judge between people to judge with justice."',
        translation_ar: '"إِنَّ اللّهَ يَأْمُرُكُمْ أَن تُؤدُّواْ الأَمَانَاتِ إِلَى أَهْلِهَا وَإِذَا حَكَمْتُم بَيْنَ النَّاسِ أَن تَحْكُمُواْ بِالْعَدْلِ"',
        explanation_en: 'Amanah (trust) covers everything entrusted to you — property, secrets, responsibilities, public office. Rendering trusts means returning them faithfully, even to those you disagree with.',
        explanation_ar: 'الأمانة تشمل كل ما أُؤتمنت عليه — مالاً وأسراراً ومسؤوليات ومناصب. أداء الأمانات يعني إعادتها بإخلاص، حتى لمن تختلف معه.',
      },
      {
        surah: 3, ayah: 17,
        ref: '3:17', surah_name_en: 'Al-Imran', surah_name_ar: 'آل عمران',
        translation_en: '"The patient, the true, the obedient, those who spend [in the way of Allah], and those who seek forgiveness before dawn."',
        translation_ar: '"الصَّابِرِينَ وَالصَّادِقِينَ وَالْقَانِتِينَ وَالْمُنفِقِينَ وَالْمُسْتَغْفِرِينَ بِالأَسْحَارِ"',
        explanation_en: 'Al-Sadiqun (the truthful) are listed among five categories of the people of Paradise. Truthfulness is not a secondary virtue — it is a pillar of the righteous character alongside patience, worship, generosity, and seeking forgiveness.',
        explanation_ar: 'الصادقون مذكورون بين خمسة أصناف من أهل الجنة. الصدق ليس فضيلة ثانوية — بل ركيزة في شخصية الصالحين إلى جانب الصبر والقنوت والإنفاق والاستغفار.',
      },
    ],
  },

  // ── 8. Good Character ─────────────────────────────────────────────────────
  {
    key: 'khuluq',
    icon: Star,
    colorClass: 'text-orange-600',
    bgClass: 'bg-orange-50',
    borderClass: 'border-orange-300',
    headerBg: 'bg-orange-50',
    label_en: 'Good Character (Ḥusn al-Khuluq)',
    label_ar: 'حسن الخلق',
    intro_en: 'The Prophet ﷺ said: "The heaviest thing on the scale on the Day of Resurrection will be good character." Islam is not only ritual — it is the cultivation of a beautiful inner life expressed outward.',
    intro_ar: 'قال النبي ﷺ: "أثقل ما يُوضع في الميزان يوم القيامة حسن الخلق". الإسلام ليس عبادة فحسب — بل تنمية حياة داخلية جميلة تنعكس على الخارج.',
    verses: [
      {
        surah: 68, ayah: 4,
        ref: '68:4', surah_name_en: 'Al-Qalam', surah_name_ar: 'القلم',
        translation_en: '"And indeed, you are of a great moral character."',
        translation_ar: '"وَإِنَّكَ لَعَلى خُلُقٍ عَظِيمٍ"',
        explanation_en: 'The single greatest character reference in history — Allah praising the Prophet ﷺ. "Great moral character" is the standard. This verse is the north star for every Muslim seeking to become a better human being.',
        explanation_ar: 'أعظم شهادة خلق في التاريخ — الله يُزكّي النبي ﷺ. "خلق عظيم" هو المعيار. هذه الآية هي النجم القطبي لكل مسلم يسعى لأن يكون إنساناً أفضل.',
      },
      {
        surah: 16, ayah: 90,
        ref: '16:90', surah_name_en: 'An-Nahl', surah_name_ar: 'النحل',
        translation_en: '"Indeed, Allah orders justice and good conduct and giving to relatives and forbids immorality and bad conduct and oppression. He admonishes you that perhaps you will be reminded."',
        translation_ar: '"إِنَّ اللّهَ يَأْمُرُ بِالْعَدْلِ وَالإِحْسَانِ وَإِيتَاء ذِي الْقُرْبَى وَيَنْهَى عَنِ الْفَحْشَاء وَالْمُنكَرِ وَالْبَغْيِ يَعِظُكُمْ لَعَلَّكُمْ تَذَكَّرُونَ"',
        explanation_en: 'This verse is recited in every Friday khutbah. Three commands (justice, ihsān, giving to kin) and three prohibitions (immorality, wrongdoing, transgression) — the entire ethical code in one sentence.',
        explanation_ar: 'تُتلى هذه الآية في كل خطبة جمعة. ثلاثة أوامر (العدل والإحسان وإيتاء ذي القربى) وثلاثة نواهٍ (الفحشاء والمنكر والبغي) — المنظومة الأخلاقية كاملة في جملة واحدة.',
      },
      {
        surah: 41, ayah: 34,
        ref: '41:34', surah_name_en: 'Fussilat', surah_name_ar: 'فصلت',
        translation_en: '"And not equal are the good deed and the bad. Repel [evil] by that [deed] which is better; and thereupon the one whom between you and him is enmity [will become] as though he was a devoted friend."',
        translation_ar: '"وَلَا تَسْتَوِي الْحَسَنَةُ وَلَا السَّيِّئَةُ ادْفَعْ بِالَّتِي هِيَ أَحْسَنُ فَإِذَا الَّذِي بَيْنَكَ وَبَيْنَهُ عَدَاوَةٌ كَأَنَّهُ وَلِيٌّ حَمِيمٌ"',
        explanation_en: 'The Quran\'s most powerful tool for social transformation: respond to bad with the best possible good. Your enemy can become your closest ally — not through argument, but through beautiful character.',
        explanation_ar: 'أقوى أداة قرآنية للتحول الاجتماعي: ردّ السيئ بأحسن منه. عدوك قد يصبح أقرب أوليائك — ليس عن طريق الحجة بل عن طريق حسن الخلق.',
      },
      {
        surah: 3, ayah: 134,
        ref: '3:134', surah_name_en: 'Al-Imran', surah_name_ar: 'آل عمران',
        translation_en: '"Who spend [in the cause of Allah] during ease and hardship and who restrain anger and who pardon the people — and Allah loves the doers of good."',
        translation_ar: '"الَّذِينَ يُنفِقُونَ فِي السَّرَّاء وَالضَّرَّاء وَالْكَاظِمِينَ الْغَيْظَ وَالْعَافِينَ عَنِ النَّاسِ وَاللّهُ يُحِبُّ الْمُحْسِنِينَ"',
        explanation_en: 'Three character marks of the people of Paradise: generosity in all conditions, mastery over anger, and the ability to forgive. Note the ladder — restraining anger is good; forgiving is better; being an all-around muhsin is the summit.',
        explanation_ar: 'ثلاث سمات لأهل الجنة: الكرم في كل الأحوال، والسيطرة على الغضب، والقدرة على العفو. لاحظ التسلسل — كظم الغيظ حسن؛ والعفو أحسن؛ والإحسان هو القمة.',
      },
    ],
  },
];

// ---------------------------------------------------------------------------
// Single verse card — fetches Arabic text from API
// ---------------------------------------------------------------------------

function VerseCard({ verse, index }: { verse: PillarVerse; index: number }) {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';
  const [uthmani, setUthmani] = useState<string | null>(null);
  const [loadingText, setLoadingText] = useState(false);
  const fetchedRef = useRef(false);

  useEffect(() => {
    if (fetchedRef.current) return;
    fetchedRef.current = true;
    setLoadingText(true);
    quranApi
      .getVerse(verse.surah, verse.ayah)
      .then(res => setUthmani(res.data.text_uthmani))
      .catch(() => setUthmani(null))
      .finally(() => setLoadingText(false));
  }, [verse.surah, verse.ayah]);

  return (
    <div className="bg-white border border-gray-100 rounded-xl overflow-hidden shadow-sm">
      {/* Header row */}
      <div className={clsx('px-4 py-2.5 bg-gray-50 border-b border-gray-100 flex items-center justify-between', isRtl && 'flex-row-reverse')}>
        <div className={clsx('flex items-center gap-2', isRtl && 'flex-row-reverse')}>
          <span className="w-5 h-5 rounded-full bg-white border border-gray-200 flex items-center justify-center text-[10px] font-bold text-gray-500 shadow-sm flex-shrink-0">
            {index + 1}
          </span>
          <span className={clsx('text-xs font-medium text-gray-600', isRtl && 'font-arabic')}>
            {isRtl ? verse.surah_name_ar : verse.surah_name_en}
          </span>
        </div>
        <Link
          to={`/quran/${verse.surah}`}
          className="flex items-center gap-1 text-xs text-primary-600 hover:text-primary-800 font-mono"
        >
          {verse.ref}
          <ExternalLink className="w-3 h-3" />
        </Link>
      </div>

      {/* Arabic text (from API) */}
      <div className="px-4 pt-4 pb-2">
        {loadingText ? (
          <div className="h-8 flex items-center">
            <Loader2 className="w-4 h-4 text-gray-300 animate-spin" />
          </div>
        ) : uthmani ? (
          <p dir="rtl" className="font-arabic text-right text-lg leading-loose text-gray-900">
            {uthmani}
          </p>
        ) : null}
      </div>

      {/* Translation */}
      <div className="px-4 py-3 border-t border-gray-50">
        <div className={clsx('flex items-start gap-2 mb-1.5', isRtl && 'flex-row-reverse')}>
          <BookOpen className="w-3.5 h-3.5 text-gray-400 mt-0.5 flex-shrink-0" />
          <span className="text-[10px] uppercase tracking-wide text-gray-400 font-medium">
            {isRtl ? 'الترجمة' : 'Translation'}
          </span>
        </div>
        <p className={clsx('text-sm text-gray-700 italic leading-relaxed', isRtl ? 'font-arabic text-right' : 'text-left')}>
          {isRtl ? verse.translation_ar : verse.translation_en}
        </p>
      </div>

      {/* Explanation */}
      <div className="px-4 pb-4 pt-2 border-t border-gray-50">
        <p className={clsx('text-xs text-gray-500 leading-relaxed', isRtl && 'font-arabic text-right')}>
          {isRtl ? verse.explanation_ar : verse.explanation_en}
        </p>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// IslamicPillarsPanel
// ---------------------------------------------------------------------------

export function IslamicPillarsPanel() {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';
  const [openKey, setOpenKey] = useState<string | null>(null);

  const toggle = (key: string) => setOpenKey(prev => (prev === key ? null : key));

  return (
    <div className="space-y-3">
      {/* Section header */}
      <div className={clsx('flex items-center gap-2', isRtl && 'flex-row-reverse')}>
        <div className="w-1 h-5 bg-teal-500 rounded-full" />
        <h3 className={clsx('font-semibold text-gray-700 text-sm', isRtl && 'font-arabic')}>
          {isRtl ? 'الأركان والفضائل القرآنية' : 'Pillars & Virtues — Quranic Verses'}
        </h3>
      </div>
      <p className={clsx('text-xs text-gray-500 leading-relaxed', isRtl && 'font-arabic text-right')}>
        {isRtl
          ? 'مختارات من الآيات الكريمة المتعلقة بأركان الإسلام والفضائل الاجتماعية، مع شرح موجز لكل آية.'
          : 'Selected Quranic verses on the five pillars of Islam and core social virtues, each with a brief explanation.'}
      </p>

      {/* Pillar accordions */}
      {PILLARS.map(pillar => {
        const Icon = pillar.icon;
        const isOpen = openKey === pillar.key;
        return (
          <div key={pillar.key} className={clsx('rounded-xl border overflow-hidden', pillar.borderClass)}>
            {/* Pillar header button */}
            <button
              onClick={() => toggle(pillar.key)}
              className={clsx(
                'w-full flex items-center justify-between gap-3 px-4 py-3.5 transition-colors text-left',
                pillar.bgClass,
                isRtl && 'flex-row-reverse text-right',
              )}
            >
              <div className={clsx('flex items-center gap-3', isRtl && 'flex-row-reverse')}>
                <div className={clsx('w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 bg-white bg-opacity-60 border', pillar.borderClass)}>
                  <Icon className={clsx('w-4 h-4', pillar.colorClass)} />
                </div>
                <div>
                  <p className={clsx('text-sm font-semibold text-gray-800', isRtl && 'font-arabic')}>
                    {isRtl ? pillar.label_ar : pillar.label_en}
                  </p>
                  <p className={clsx('text-[10px] text-gray-500', isRtl && 'font-arabic')}>
                    {pillar.verses.length} {isRtl ? 'آيات' : 'verses'}
                  </p>
                </div>
              </div>
              <div className={clsx('flex items-center gap-2', isRtl && 'flex-row-reverse')}>
                {!isOpen && (
                  <span className={clsx('text-[10px] text-gray-400 hidden sm:block', isRtl && 'font-arabic')}>
                    {isRtl ? pillar.intro_ar.slice(0, 40) + '…' : pillar.intro_en.slice(0, 50) + '…'}
                  </span>
                )}
                {isOpen
                  ? <ChevronUp className="w-4 h-4 text-gray-500 flex-shrink-0" />
                  : <ChevronDown className="w-4 h-4 text-gray-500 flex-shrink-0" />
                }
              </div>
            </button>

            {/* Expanded content */}
            {isOpen && (
              <div className="p-4 space-y-4 bg-white border-t border-gray-100">
                {/* Intro paragraph */}
                <p className={clsx('text-sm text-gray-600 leading-relaxed', isRtl && 'font-arabic text-right')}>
                  {isRtl ? pillar.intro_ar : pillar.intro_en}
                </p>
                {/* Verse cards */}
                <div className="space-y-3">
                  {pillar.verses.map((verse, i) => (
                    <VerseCard key={`${verse.surah}:${verse.ayah}`} verse={verse} index={i} />
                  ))}
                </div>
              </div>
            )}
          </div>
        );
      })}

      {/* Footer note */}
      <div className="p-3 bg-gray-50 rounded-xl border border-gray-200">
        <p className={clsx('text-[11px] text-gray-500 leading-relaxed', isRtl && 'font-arabic text-right')}>
          {isRtl
            ? 'الآيات الكريمة مستقاة من مصحف الملك فهد. التفسيرات الموجزة توجيهية تربوية وليست تفسيراً رسمياً. للتفسير المعمّق راجع علماء موثوقين.'
            : 'Quranic text is retrieved from the King Fahd Quran (Hafs transmission). Brief explanations are pedagogical guidance, not scholarly tafsir. For depth, consult trusted scholars.'}
        </p>
      </div>
    </div>
  );
}
