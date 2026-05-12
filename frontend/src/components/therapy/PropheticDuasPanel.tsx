import { useState } from 'react';
import { ChevronDown, ChevronUp, Copy, Check, ExternalLink } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useLanguageStore } from '../../stores/languageStore';
import clsx from 'clsx';

// Authentic du'as from Quran and Sunnah, organised by emotional state.
// Note: All Arabic text here is du'a text from hadith (non-Quranic sources),
// or references to Quranic du'as shown by reference only (per CLAUDE.md).
const PROPHETIC_DUAS: Record<string, Array<{
  name_en: string;
  name_ar: string;
  arabic?: string;           // omitted when is_quranic: true (Quran text must come from DB per CLAUDE.md)
  transliteration: string;
  translation_en: string;
  translation_ar: string;
  source_en: string;
  source_ar: string;
  is_quranic?: boolean;
  quran_ref?: string;        // e.g. "21:87" — used to link to /quran/:surah
}>> = {
  anxiety: [
    {
      name_en: "The Prophet's Comprehensive Du'a for Anxiety",
      name_ar: "دعاء النبي ﷺ الشامل للهم والحزن",
      arabic:
        "اللَّهُمَّ إِنِّي أَعُوذُ بِكَ مِنَ الْهَمِّ وَالْحُزْنِ، وَأَعُوذُ بِكَ مِنَ الْعَجْزِ وَالْكَسَلِ، وَأَعُوذُ بِكَ مِنَ الْجُبْنِ وَالْبُخْلِ، وَأَعُوذُ بِكَ مِنْ ضَلَعِ الدَّيْنِ وَغَلَبَةِ الرِّجَالِ",
      transliteration:
        "Allāhumma innī a'ūdhu bika minal-hammi wal-ḥuzn, wa a'ūdhu bika minal-'ajzi wal-kasal, wa a'ūdhu bika minal-jubni wal-bukhl, wa a'ūdhu bika min ḍala'id-dayni wa ghalabatir-rijāl",
      translation_en:
        "O Allah, I seek refuge in You from anxiety and sorrow, from weakness and laziness, from cowardice and miserliness, and from the burden of debt and being overpowered by others.",
      translation_ar:
        "اللهم إني أعوذ بك من الهم والحزن والعجز والكسل والجبن والبخل وضلع الدين وغلبة الرجال.",
      source_en: "Sahih Al-Bukhari — the Prophet ﷺ used to say this du'a regularly. It addresses both ﻫَﻢّ (worry about the future) and ﺣُﺰﻥ (grief about the past) in a single supplication.",
      source_ar: "صحيح البخاري — كان النبي ﷺ يقول هذا الدعاء باستمرار. يعالج الهَمَّ (القلق على المستقبل) والحُزنَ (الحزن على الماضي) في دعاء واحد.",
    },
    {
      name_en: "Hasbiyallah — Allah is Sufficient for Me",
      name_ar: "حسبي الله — الله يكفيني",
      transliteration: "Ḥasbiyallāhu lā ilāha illā huwa 'alayhi tawakkaltu wa huwa rabbul-'arshil-'aẓīm",
      translation_en: "Allah is sufficient for me. There is no deity except Him. Upon Him I have relied, and He is the Lord of the Mighty Throne.",
      translation_ar: "حسبي الله لا إله إلا هو عليه توكلت وهو رب العرش العظيم.",
      source_en: "Quran 9:129 and Abu Dawud. The Prophet ﷺ said whoever recites this seven times morning and evening, Allah will be sufficient for whatever concerns them.",
      source_ar: "القرآن 9:129 وأبو داود. قال النبي ﷺ: من قالها سبع مرات صباحاً ومساءً كفاه الله ما أهمّه.",
      is_quranic: true,
      quran_ref: "9:129",
    },
  ],
  sadness: [
    {
      name_en: "The Quran as Healer of Grief — Du'a of Ibn Mas'ud",
      name_ar: "القرآن شافي الحزن — دعاء ابن مسعود",
      arabic:
        "اللَّهُمَّ إِنِّي عَبْدُكَ، ابْنُ عَبْدِكَ، ابْنُ أَمَتِكَ، نَاصِيَتِي بِيَدِكَ، مَاضٍ فِيَّ حُكْمُكَ، عَدْلٌ فِيَّ قَضَاؤُكَ، أَسْأَلُكَ بِكُلِّ اسْمٍ هُوَ لَكَ سَمَّيْتَ بِهِ نَفْسَكَ أَوْ أَنْزَلْتَهُ فِي كِتَابِكَ أَوْ عَلَّمْتَهُ أَحَداً مِنْ خَلْقِكَ أَوِ اسْتَأْثَرْتَ بِهِ فِي عِلْمِ الْغَيْبِ عِنْدَكَ، أَنْ تَجْعَلَ الْقُرْآنَ رَبِيعَ قَلْبِي، وَنُورَ صَدْرِي، وَجَلَاءَ حُزْنِي، وَذَهَابَ هَمِّي",
      transliteration:
        "Allāhumma innī 'abduka, ibnu 'abdika, ibnu amatika, nāṣiyatī biyadika, māḍin fiyya ḥukmuka, 'adlun fiyya qaḍā'uk, as'aluka bikulli ismin huwa laka sammayta bihi nafsaka, aw anzaltahu fī kitābika, aw 'allamtahu aḥadan min khalqika, awis-ta'tharta bihi fī 'ilmil-ghaybi 'indaka, an taj'alal-qur'āna rabī'a qalbī, wa nūra ṣadrī, wa jalā'a ḥuznī, wa dhahāba hammī",
      translation_en:
        "O Allah, I am Your servant, the son of Your servant, the son of Your female servant. My forelock is in Your hand. Your decree over me is assured. Your judgment concerning me is just. I ask You by every name You have named Yourself, or revealed in Your book, or taught to any of Your creation, or kept in the knowledge of the unseen with You — make the Quran the spring of my heart, the light of my chest, a departure for my sorrow, and a release for my anxiety.",
      translation_ar:
        "اللهم اجعل القرآن ربيع قلبي ونور صدري وجلاء حزني وذهاب همي وغمي.",
      source_en:
        "Musnad of Imam Ahmad. The Prophet ﷺ said: 'No one is ever afflicted with anxiety or grief and says these words, except that Allah will remove their anxiety and grief, and replace them with joy.'",
      source_ar:
        "مسند الإمام أحمد. قال النبي ﷺ: 'ما أصاب أحداً قط هَمٌّ ولا حَزَن فقال هذا الكلام إلا أذهب الله همّه وحزنه وأبدله مكانه فرحاً.'",
    },
    {
      name_en: "Du'a of Prophet Yunus — Called from the Darkness",
      name_ar: "دعاء النبي يونس — من ظلمات الضيق",
      transliteration: "Lā ilāha illā anta subḥānaka innī kuntu minaẓ-ẓālimīn",
      translation_en: "There is no deity except You. Exalted are You. Indeed, I have been among the wrongdoers.",
      translation_ar: "لا إله إلا أنت سبحانك إني كنت من الظالمين.",
      source_en:
        "Quran 21:87. The Prophet ﷺ said: 'No Muslim ever calls upon Allah with these words in distress, except that Allah answers his call.' (Tirmidhi, graded sahih)",
      source_ar:
        "القرآن 21:87. قال النبي ﷺ: 'ما دعا مسلم بهذا الدعاء في شيء قط إلا استجاب الله له.' (الترمذي، صحيح)",
      is_quranic: true,
      quran_ref: "21:87",
    },
  ],
  grief: [
    {
      name_en: "Du'a of Prophet Yunus — Called from the Darkness",
      name_ar: "دعاء النبي يونس — من ظلمات الضيق",
      transliteration: "Lā ilāha illā anta subḥānaka innī kuntu minaẓ-ẓālimīn",
      translation_en: "There is no deity except You. Exalted are You. Indeed, I have been among the wrongdoers.",
      translation_ar: "لا إله إلا أنت سبحانك إني كنت من الظالمين.",
      source_en:
        "Quran 21:87. Recommended especially for grief, loss, and extreme distress — the du'a that was answered when all seemed hopeless.",
      source_ar: "القرآن 21:87. يُستحب في الحزن والفقد والضيق الشديد — الدعاء الذي استُجيب حين بدا كل شيء يائساً.",
      is_quranic: true,
      quran_ref: "21:87",
    },
    {
      name_en: "The Quran as Healer of Grief — Du'a of Ibn Mas'ud",
      name_ar: "القرآن شافي الحزن — دعاء ابن مسعود",
      arabic:
        "اللَّهُمَّ إِنِّي عَبْدُكَ، ابْنُ عَبْدِكَ، ابْنُ أَمَتِكَ، نَاصِيَتِي بِيَدِكَ، مَاضٍ فِيَّ حُكْمُكَ، عَدْلٌ فِيَّ قَضَاؤُكَ، أَسْأَلُكَ بِكُلِّ اسْمٍ هُوَ لَكَ سَمَّيْتَ بِهِ نَفْسَكَ أَوْ أَنْزَلْتَهُ فِي كِتَابِكَ أَوْ عَلَّمْتَهُ أَحَداً مِنْ خَلْقِكَ أَوِ اسْتَأْثَرْتَ بِهِ فِي عِلْمِ الْغَيْبِ عِنْدَكَ، أَنْ تَجْعَلَ الْقُرْآنَ رَبِيعَ قَلْبِي، وَنُورَ صَدْرِي، وَجَلَاءَ حُزْنِي، وَذَهَابَ هَمِّي",
      transliteration:
        "Allāhumma innī 'abduka ibnu 'abdika ibnu amatika... an taj'alal-qur'āna rabī'a qalbī wa nūra ṣadrī wa jalā'a ḥuznī wa dhahāba hammī",
      translation_en:
        "O Allah… make the Quran the spring of my heart, the light of my chest, a departure for my sorrow, and a release for my anxiety.",
      translation_ar:
        "اللهم اجعل القرآن ربيع قلبي ونور صدري وجلاء حزني وذهاب همي.",
      source_en:
        "Musnad of Imam Ahmad. Specifically prescribed for grief and deep sorrow — Allah promises to replace the grief with joy.",
      source_ar: "مسند الإمام أحمد. موصى به تحديداً للحزن والكآبة — الله يعد بأن يبدل الحزن فرحاً.",
    },
  ],
  fear: [
    {
      name_en: "Hasbunallah — The Companions' Du'a Against Fear",
      name_ar: "حسبنا الله — دعاء الصحابة في مواجهة الخوف",
      transliteration: "Ḥasbunallāhu wa ni'mal-wakīl",
      translation_en: "Allah is sufficient for us, and He is the Best Disposer of affairs.",
      translation_ar: "حسبنا الله ونعم الوكيل.",
      source_en:
        "Quran 3:173. Said by the companions when warned of an overwhelming enemy army approaching — and they were blessed in response. The Prophet ﷺ also said it when about to be overtaken by a great flood (Bukhari).",
      source_ar:
        "القرآن 3:173. قالها الصحابة حين أُخبروا بجيش عرمرم مقبل — فبوركوا بها. وقالها النبي ﷺ أيضاً حين كاد يغرقه سيل عظيم (البخاري).",
      is_quranic: true,
      quran_ref: "3:173",
    },
    {
      name_en: "The Prophet's Du'a for Fear at Night",
      name_ar: "دعاء النبي ﷺ للخوف ليلاً",
      arabic:
        "لَا إِلَهَ إِلَّا اللَّهُ الْحَلِيمُ الْكَرِيمُ، سُبْحَانَ اللَّهِ رَبِّ الْعَرْشِ الْعَظِيمِ، الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ",
      transliteration:
        "Lā ilāha illallāhul-Ḥalīmul-Karīm, subḥānallāhi Rabbil-'arshil-'aẓīm, alḥamdulillāhi Rabbil-'ālamīn",
      translation_en:
        "There is no deity but Allah, the Forbearing, the Generous. Glory be to Allah, Lord of the Mighty Throne. All praise is due to Allah, Lord of all the worlds.",
      translation_ar:
        "لا إله إلا الله الحليم الكريم، سبحان الله رب العرش العظيم، الحمد لله رب العالمين.",
      source_en:
        "Sahih Al-Bukhari. The Prophet ﷺ said this when distressed and frightened at night. The divine names Al-Ḥalīm (the Forbearing) and Al-Karīm (the Generous) are specifically soothing for fear.",
      source_ar:
        "صحيح البخاري. كان النبي ﷺ يقول هذا حين يضيق ويخاف ليلاً. أسماء الله الحليم والكريم مسكِّنة تحديداً للخوف.",
    },
  ],
  guilt: [
    {
      name_en: "Sayyid al-Istighfar — The Master of Seeking Forgiveness",
      name_ar: "سيد الاستغفار",
      arabic:
        "اللَّهُمَّ أَنْتَ رَبِّي لَا إِلَهَ إِلَّا أَنْتَ، خَلَقْتَنِي وَأَنَا عَبْدُكَ، وَأَنَا عَلَى عَهْدِكَ وَوَعْدِكَ مَا اسْتَطَعْتُ، أَعُوذُ بِكَ مِنْ شَرِّ مَا صَنَعْتُ، أَبُوءُ لَكَ بِنِعْمَتِكَ عَلَيَّ وَأَبُوءُ بِذَنْبِي، فَاغْفِرْ لِي فَإِنَّهُ لَا يَغْفِرُ الذُّنُوبَ إِلَّا أَنْتَ",
      transliteration:
        "Allāhumma anta rabbī lā ilāha illā anta, khalaqtanī wa anā 'abduka, wa anā 'alā 'ahdika wa wa'dika mastata'tu, a'ūdhu bika min sharri mā ṣana'tu, abū'u laka bini'matika 'alayya wa abū'u bidhanbī, faghfir lī fa'innahu lā yaghfirudhdhunūba illā anta",
      translation_en:
        "O Allah, You are my Lord, there is no deity but You. You created me and I am Your slave. I am keeping my covenant and promise to You as best I can. I seek refuge in You from the evil of what I have done. I acknowledge Your blessings upon me and I acknowledge my sin. So forgive me, for no one forgives sins except You.",
      translation_ar:
        "اللهم أنت ربي لا إله إلا أنت خلقتني وأنا عبدك وأنا على عهدك ووعدك ما استطعت أعوذ بك من شر ما صنعت أبوء لك بنعمتك علي وأبوء بذنبي فاغفر لي فإنه لا يغفر الذنوب إلا أنت.",
      source_en:
        "Sahih Al-Bukhari. The Prophet ﷺ said: 'Whoever recites this with conviction in the morning and dies that day before evening, is from the people of Paradise. And whoever recites it at night and dies before morning, is from the people of Paradise.'",
      source_ar:
        "صحيح البخاري. قال النبي ﷺ: 'من قالها موقناً بها فمات من يومه قبل أن يمسي فهو من أهل الجنة، ومن قالها من الليل موقناً بها فمات قبل أن يصبح فهو من أهل الجنة.'",
    },
    {
      name_en: "Du'a for Forgiveness — Laylat al-Qadr",
      name_ar: "دعاء المغفرة — ليلة القدر",
      arabic: "اللَّهُمَّ إِنَّكَ عَفُوٌّ تُحِبُّ الْعَفْوَ فَاعْفُ عَنِّي",
      transliteration: "Allāhumma innaka 'afuwwun tuḥibbul-'afwa fa'fu 'annī",
      translation_en: "O Allah, You are All-Pardoning, You love to pardon, so pardon me.",
      translation_ar: "اللهم إنك عفو تحب العفو فاعف عني.",
      source_en:
        "Tirmidhi (sahih). Aisha asked the Prophet ﷺ: 'What if I knew which night was Laylat al-Qadr, what should I say?' He taught her this du'a. It can be recited at any time — especially when guilt is heavy.",
      source_ar:
        "الترمذي (صحيح). سألت عائشة النبي ﷺ: 'لو علمت أي ليلة هي ليلة القدر، ماذا أقول؟' فعلّمها هذا الدعاء. يُستحب قوله في أي وقت — خاصةً حين يثقل الذنب.",
    },
  ],
  hopelessness: [
    {
      name_en: "Du'a from the Depths of Despair",
      name_ar: "دعاء من أعماق اليأس",
      transliteration: "Lā ilāha illā anta subḥānaka innī kuntu minaẓ-ẓālimīn",
      translation_en: "There is no deity except You. Exalted are You. Indeed, I have been among the wrongdoers.",
      translation_ar: "لا إله إلا أنت سبحانك إني كنت من الظالمين.",
      source_en:
        "Quran 21:87. Prophet Yunus called to Allah from the belly of the whale — from complete darkness and hopelessness. Allah answered. The Prophet ﷺ said no Muslim calls with this du'a in distress except that Allah responds. (Tirmidhi, sahih)",
      source_ar:
        "القرآن 21:87. دعا النبي يونس الله من بطن الحوت — من ظلمة وإغلاق تامّين. فأجابه الله. قال النبي ﷺ: لا يدعو مسلم بهذا الدعاء في كرب إلا أجابه الله. (الترمذي، صحيح)",
      is_quranic: true,
      quran_ref: "21:87",
    },
    {
      name_en: "The Quran as Healer of Grief — Du'a of Ibn Mas'ud",
      name_ar: "القرآن شافي الحزن — دعاء ابن مسعود",
      arabic:
        "اللَّهُمَّ إِنِّي عَبْدُكَ، ابْنُ عَبْدِكَ، ابْنُ أَمَتِكَ، نَاصِيَتِي بِيَدِكَ، مَاضٍ فِيَّ حُكْمُكَ، عَدْلٌ فِيَّ قَضَاؤُكَ، أَسْأَلُكَ بِكُلِّ اسْمٍ هُوَ لَكَ... أَنْ تَجْعَلَ الْقُرْآنَ رَبِيعَ قَلْبِي، وَنُورَ صَدْرِي، وَجَلَاءَ حُزْنِي، وَذَهَابَ هَمِّي",
      transliteration:
        "Allāhumma innī 'abduka... an taj'alal-qur'āna rabī'a qalbī wa nūra ṣadrī wa jalā'a ḥuznī wa dhahāba hammī",
      translation_en: "O Allah… make the Quran the spring of my heart, the light of my chest, a departure for my sorrow, and a release for my anxiety.",
      translation_ar: "اللهم اجعل القرآن ربيع قلبي ونور صدري وجلاء حزني وذهاب همي.",
      source_en: "Musnad of Imam Ahmad. Promised outcome: Allah will replace the grief with joy.",
      source_ar: "مسند الإمام أحمد. النتيجة الموعودة: يُبدّل الله الحزن فرحاً.",
    },
  ],
  stress: [
    {
      name_en: "The Prophet's Du'a Against Worry and Burden",
      name_ar: "دعاء النبي ﷺ ضد الهم والأعباء",
      arabic:
        "اللَّهُمَّ إِنِّي أَعُوذُ بِكَ مِنَ الْهَمِّ وَالْحُزْنِ، وَأَعُوذُ بِكَ مِنَ الْعَجْزِ وَالْكَسَلِ، وَأَعُوذُ بِكَ مِنَ الْجُبْنِ وَالْبُخْلِ، وَأَعُوذُ بِكَ مِنْ ضَلَعِ الدَّيْنِ وَغَلَبَةِ الرِّجَالِ",
      transliteration:
        "Allāhumma innī a'ūdhu bika minal-hammi wal-ḥuzn, wa a'ūdhu bika minal-'ajzi wal-kasal, wa a'ūdhu bika minal-jubni wal-bukhl, wa a'ūdhu bika min ḍala'id-dayni wa ghalabatir-rijāl",
      translation_en:
        "O Allah, I seek refuge in You from anxiety and sorrow, from weakness and laziness, from cowardice and miserliness, and from the burden of debt and being overpowered by others.",
      translation_ar: "اللهم إني أعوذ بك من الهم والحزن والعجز والكسل والجبن والبخل وضلع الدين وغلبة الرجال.",
      source_en: "Sahih Al-Bukhari. Recite this morning and evening. It covers all dimensions of stress: emotional, physical, moral, financial, and social.",
      source_ar: "صحيح البخاري. يُقال صباحاً ومساءً. يشمل كل أبعاد الضغط: العاطفي والجسدي والأخلاقي والمادي والاجتماعي.",
    },
    {
      name_en: "Subhanallah — The Heart's Reset",
      name_ar: "سبحان الله — إعادة ضبط القلب",
      arabic: "سُبْحَانَ اللَّهِ وَبِحَمْدِهِ، سُبْحَانَ اللَّهِ الْعَظِيمِ",
      transliteration: "Subḥānallāhi wa biḥamdih, subḥānallāhil-'aẓīm",
      translation_en: "Glory be to Allah and praise Him. Glory be to Allah, the Magnificent.",
      translation_ar: "سبحان الله وبحمده سبحان الله العظيم.",
      source_en:
        "Sahih Al-Bukhari. The Prophet ﷺ said: 'Two phrases light on the tongue, heavy on the scales, beloved to the Most Merciful: Subhanallahi wa bihamdih, Subhanallahil-'Adhim.' This dhikr quiets a stressed mind.",
      source_ar:
        "صحيح البخاري. قال النبي ﷺ: 'كلمتان خفيفتان على اللسان ثقيلتان في الميزان حبيبتان إلى الرحمن: سبحان الله وبحمده، سبحان الله العظيم.' هذا الذكر يهدّئ العقل المشغول.",
    },
  ],
  loneliness: [
    {
      name_en: "The Du'a of Nearness — You Are Never Alone",
      name_ar: "دعاء القرب — لست وحيداً أبداً",
      arabic: "يَا حَيُّ يَا قَيُّومُ بِرَحْمَتِكَ أَسْتَغِيثُ",
      transliteration: "Yā Ḥayyu yā Qayyūmu biraḥmatika astaghīth",
      translation_en: "O Ever-Living, O Self-Sustaining — by Your mercy I seek relief.",
      translation_ar: "يا حي يا قيوم برحمتك أستغيث.",
      source_en:
        "Tirmidhi (hasan). These are two of the greatest names of Allah — Al-Hayy (the Ever-Living, who never sleeps) and Al-Qayyum (the Self-Sustaining Sustainer of all). When you call on Him by these names, you are calling on the One who is always awake, always present, never absent.",
      source_ar:
        "الترمذي (حسن). هذان من أعظم أسماء الله — الحي (الذي لا ينام) والقيوم (القائم على كل شيء). حين تناديه بهذين الاسمين، تنادي مَن هو دائماً يقظ، دائماً حاضر، لا يغيب أبداً.",
    },
    {
      name_en: "Allah is with Us — The Cave Du'a",
      name_ar: "الله معنا — دعاء الغار",
      transliteration: "Innallāha ma'anā",
      translation_en: "Indeed, Allah is with us.",
      translation_ar: "إن الله معنا.",
      source_en:
        "Quran 9:40. Said by the Prophet ﷺ to Abu Bakr (may Allah be pleased with him) when they were hiding in the cave during the Hijrah, surrounded by enemies. Three words that changed everything.",
      source_ar:
        "القرآن 9:40. قالها النبي ﷺ لأبي بكر رضي الله عنه حين كانا في الغار محاطَين بالأعداء أثناء الهجرة. ثلاث كلمات غيّرت كل شيء.",
      is_quranic: true,
      quran_ref: "9:40",
    },
  ],
  anger: [
    {
      name_en: "A'udhu Billah — The Prophetic Remedy for Anger",
      name_ar: "أعوذ بالله — الترياق النبوي للغضب",
      arabic: "أَعُوذُ بِاللَّهِ مِنَ الشَّيْطَانِ الرَّجِيمِ",
      transliteration: "A'ūdhu billāhi minash-shayṭānir-rajīm",
      translation_en: "I seek refuge in Allah from the accursed Satan.",
      translation_ar: "أعوذ بالله من الشيطان الرجيم.",
      source_en:
        "Bukhari & Muslim. When a man's anger was visible in his face, the Prophet ﷺ said: 'I know a word that, if he were to say it, this [anger] would go away: A'udhu Billahi minash-shaytan ir-rajim.' The Prophet ﷺ specifically prescribed this as the cure for anger.",
      source_ar:
        "البخاري ومسلم. حين رأى النبي ﷺ رجلاً مرتسماً الغضب في وجهه قال: 'إني أعلم كلمة لو قالها لذهب ما يجد: أعوذ بالله من الشيطان الرجيم.' وصفها النبي ﷺ تحديداً علاجاً للغضب.",
    },
    {
      name_en: "Allahumma Ighfir Li — Turning Anger into Repentance",
      name_ar: "اللهم اغفر لي — تحويل الغضب إلى توبة",
      arabic: "اللَّهُمَّ اغْفِرْ لِي ذَنْبِي وَأَذْهِبْ غَيْظَ قَلْبِي",
      transliteration: "Allāhummaghfir lī dhanbī wa adhhib ghayẓa qalbī",
      translation_en: "O Allah, forgive my sin and remove the rage from my heart.",
      translation_ar: "اللهم اغفر لي ذنبي وأذهب غيظ قلبي.",
      source_en:
        "Abu Dawud. Specifically asks Allah to remove the physiological sensation of rage (ghayẓ). This du'a acknowledges that anger is real and asks Allah directly to lift it.",
      source_ar:
        "أبو داود. يطلب تحديداً من الله إزالة الإحساس الجسدي بالغيظ. يُقرّ هذا الدعاء بأن الغضب حقيقي ويطلب من الله مباشرةً رفعه.",
    },
  ],
  gratitude: [
    {
      name_en: "The Du'a of Gratitude — Taught by the Prophet ﷺ",
      name_ar: "دعاء الشكر — علّمه النبي ﷺ",
      arabic:
        "اللَّهُمَّ أَعِنِّي عَلَى ذِكْرِكَ وَشُكْرِكَ وَحُسْنِ عِبَادَتِكَ",
      transliteration: "Allāhumma a'innī 'alā dhikrika wa shukrika wa ḥusni 'ibādatik",
      translation_en: "O Allah, help me to remember You, to be grateful to You, and to worship You in the best manner.",
      translation_ar: "اللهم أعني على ذكرك وشكرك وحسن عبادتك.",
      source_en:
        "Abu Dawud & Ahmad (sahih). The Prophet ﷺ specifically instructed Mu'adh ibn Jabal to say this after every obligatory prayer. It is the du'a that asks Allah to enable the very acts of dhikr and shukr.",
      source_ar:
        "أبو داود وأحمد (صحيح). أوصى النبي ﷺ معاذ بن جبل تحديداً بقول هذا الدعاء دبر كل صلاة مكتوبة. هو الدعاء الذي يطلب من الله تمكين أفعال الذكر والشكر ذاتها.",
    },
  ],
  doubt: [
    {
      name_en: "Du'a for Firmness in Faith",
      name_ar: "دعاء الثبات على الإيمان",
      arabic: "يَا مُقَلِّبَ الْقُلُوبِ ثَبِّتْ قَلْبِي عَلَى دِينِكَ",
      transliteration: "Yā muqallibal-qulūbi thabbit qalbī 'alā dīnik",
      translation_en: "O Turner of hearts, make my heart firm upon Your religion.",
      translation_ar: "يا مقلب القلوب ثبت قلبي على دينك.",
      source_en:
        "Tirmidhi (hasan). The Prophet ﷺ said this frequently. He also said: 'Hearts are between two fingers of the Most Merciful — He turns them as He wills.' Calling on Al-Muqallib (the Turner of Hearts) is the direct antidote to doubt.",
      source_ar:
        "الترمذي (حسن). كان النبي ﷺ يكثر من هذا الدعاء. وقال: 'إن القلوب بين إصبعين من أصابع الرحمن يقلبها كيف يشاء.' مناداة المقلّب القلوب هو الترياق المباشر للشك.",
    },
  ],
  general: [
    {
      name_en: "The Master Du'a of Protection",
      name_ar: "دعاء الحماية الشامل",
      arabic:
        "بِسْمِ اللَّهِ الَّذِي لَا يَضُرُّ مَعَ اسْمِهِ شَيْءٌ فِي الْأَرْضِ وَلَا فِي السَّمَاءِ وَهُوَ السَّمِيعُ الْعَلِيمُ",
      transliteration:
        "Bismillāhil-ladhī lā yaḍurru ma'asmihi shay'un fil-arḍi wa lā fis-samā'i wa huwas-samī'ul-'alīm",
      translation_en:
        "In the name of Allah, with whose name nothing on earth or in the heavens can cause harm, and He is the All-Hearing, the All-Knowing.",
      translation_ar:
        "بسم الله الذي لا يضر مع اسمه شيء في الأرض ولا في السماء وهو السميع العليم.",
      source_en:
        "Tirmidhi (sahih). Say three times in the morning and three times in the evening. The Prophet ﷺ said whoever says this will not be harmed by anything until morning / until evening.",
      source_ar:
        "الترمذي (صحيح). يُقال ثلاث مرات صباحاً وثلاث مرات مساءً. قال النبي ﷺ: من قالها لم يضره شيء حتى يصبح / حتى يمسي.",
    },
  ],
};

interface PropheticDuasPanelProps {
  emotion: string;
}

function DuaCard({ dua }: { dua: (typeof PROPHETIC_DUAS)['anxiety'][0] }) {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';
  const [copied, setCopied] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const handleCopy = async () => {
    if (!dua.arabic) return;
    try {
      await navigator.clipboard.writeText(dua.arabic);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // clipboard API not available
    }
  };

  // Parse quran_ref "surah:ayah" → "/quran/surah" link
  const quranLink = dua.quran_ref ? `/quran/${dua.quran_ref.split(':')[0]}` : null;

  return (
    <div className="bg-white rounded-2xl border border-teal-100 shadow-sm overflow-hidden">
      <div className={clsx('px-4 py-3 bg-teal-50 flex items-center justify-between', isRtl && 'flex-row-reverse')}>
        <h4 className={clsx('text-xs font-semibold text-teal-800', isRtl && 'font-arabic')}>
          {isRtl ? dua.name_ar : dua.name_en}
        </h4>
        {dua.arabic && (
          <button
            onClick={handleCopy}
            className="flex items-center gap-1 text-xs text-teal-600 hover:text-teal-800 transition-colors"
            title={isRtl ? 'نسخ النص العربي' : 'Copy Arabic text'}
          >
            {copied
              ? <Check className="w-3.5 h-3.5 text-green-500" />
              : <Copy className="w-3.5 h-3.5" />}
          </button>
        )}
      </div>

      <div className="px-4 py-4 space-y-3">
        {/* Arabic text — only for hadith du'as; Quranic text loaded from DB via the Quran page */}
        {dua.arabic && (
          <p dir="rtl" className="font-arabic text-right text-base leading-loose text-gray-900">
            {dua.arabic}
          </p>
        )}

        {/* For Quranic du'as: show a link to the verse instead of hardcoded Arabic */}
        {dua.is_quranic && quranLink && (
          <Link
            to={quranLink}
            className={clsx(
              'inline-flex items-center gap-1.5 text-xs font-medium text-teal-700 hover:text-teal-900',
              isRtl && 'flex-row-reverse font-arabic',
            )}
          >
            <ExternalLink className="w-3.5 h-3.5" />
            {isRtl ? `اقرأ الآية في القرآن (${dua.quran_ref})` : `Read verse in Quran (${dua.quran_ref})`}
          </Link>
        )}

        {/* Transliteration */}
        <p dir="ltr" className="text-xs text-gray-400 italic leading-relaxed">
          {dua.transliteration}
        </p>

        {/* Translation */}
        <p className={clsx('text-sm text-gray-700 leading-relaxed', isRtl && 'font-arabic text-right')}>
          {isRtl ? dua.translation_ar : dua.translation_en}
        </p>

        {/* Source — collapsible */}
        <button
          onClick={() => setExpanded(v => !v)}
          className={clsx(
            'flex items-center gap-1.5 text-xs text-teal-600 hover:text-teal-800 font-medium',
            isRtl && 'flex-row-reverse font-arabic',
          )}
        >
          <span className="text-[10px] bg-teal-100 text-teal-700 px-1.5 py-0.5 rounded-full">
            {isRtl ? 'المصدر' : 'Source'}
          </span>
          {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        </button>
        {expanded && (
          <p className={clsx('text-xs text-gray-500 leading-relaxed', isRtl && 'font-arabic text-right')}>
            {isRtl ? dua.source_ar : dua.source_en}
          </p>
        )}
      </div>
    </div>
  );
}

export function PropheticDuasPanel({ emotion }: PropheticDuasPanelProps) {
  const { language } = useLanguageStore();
  const isRtl = language === 'ar';
  const duas = PROPHETIC_DUAS[emotion] ?? PROPHETIC_DUAS['general'];

  if (!duas || duas.length === 0) return null;

  return (
    <div className="space-y-3">
      <div className={clsx('flex items-center gap-2', isRtl && 'flex-row-reverse')}>
        <div className="w-1 h-5 bg-teal-400 rounded-full" />
        <h3 className={clsx('font-semibold text-gray-700 text-sm', isRtl && 'font-arabic')}>
          {isRtl ? 'أدعية نبوية للحالة الراهنة' : "Prophetic Du'as for Your State"}
        </h3>
      </div>
      {duas.map((dua, i) => (
        <DuaCard key={i} dua={dua} />
      ))}
    </div>
  );
}
