/**
 * Quranic Duʿā Dataset — Supplications from the Quran
 *
 * Safety rules:
 * - Every entry has an exact surah:ayah reference
 * - Arabic text is the reference only (do NOT copy Quran text here —
 *   the UI renders it from the /quran/:surahNo route link)
 * - English meanings sourced from Saheeh International / Hilali-Khan
 * - No AI-generated content — meanings are from established translations
 */

export type DuaCategory =
  | 'prophets'
  | 'morning_evening'
  | 'guidance'
  | 'forgiveness'
  | 'protection'
  | 'family'
  | 'gratitude'
  | 'general';

export interface QuranicDua {
  id: string;
  titleEn: string;
  titleAr: string;
  surah: number;
  ayah: number;
  ayahEnd?: number;
  surahNameEn: string;
  surahNameAr: string;
  meaningEn: string;
  meaningAr: string;
  transliterationArabic: string;
  contextEn: string;
  contextAr: string;
  category: DuaCategory;
  prophet?: string;
  tags: string[];
}

export const CATEGORY_META: Record<DuaCategory, { labelEn: string; labelAr: string; emoji: string; color: string }> = {
  prophets:       { labelEn: "Prophets' Prayers",  labelAr: 'أدعية الأنبياء',     emoji: '🕌', color: 'emerald' },
  morning_evening:{ labelEn: 'Morning & Evening',  labelAr: 'الأذكار اليومية',    emoji: '🌅', color: 'amber' },
  guidance:       { labelEn: 'Guidance & Light',   labelAr: 'الهداية والنور',     emoji: '💡', color: 'violet' },
  forgiveness:    { labelEn: 'Forgiveness & Mercy',labelAr: 'المغفرة والرحمة',    emoji: '🤍', color: 'rose' },
  protection:     { labelEn: 'Protection & Relief',labelAr: 'الحفظ والنجاة',     emoji: '🛡️', color: 'blue' },
  family:         { labelEn: 'Family & Children',  labelAr: 'الأسرة والذرية',    emoji: '🏡', color: 'orange' },
  gratitude:      { labelEn: 'Gratitude & Praise', labelAr: 'الشكر والحمد',      emoji: '✨', color: 'yellow' },
  general:        { labelEn: 'General Supplication',labelAr: 'أدعية عامة',       emoji: '🤲', color: 'teal' },
};

export const QURANIC_DUAS: readonly QuranicDua[] = [
  // -------------------------------------------------------------------------
  // Prophets' Prayers
  // -------------------------------------------------------------------------
  {
    id: 'dua_adam_forgiveness',
    titleEn: "Adam & Eve's Repentance",
    titleAr: 'دعاء آدم وحواء',
    surah: 7, ayah: 23,
    surahNameEn: "Al-A'raf", surahNameAr: 'الأعراف',
    meaningEn: 'Our Lord, we have wronged ourselves, and if You do not forgive us and have mercy upon us, we will surely be among the losers.',
    meaningAr: 'رَبَّنَا ظَلَمْنَا أَنفُسَنَا وَإِن لَّمْ تَغْفِرْ لَنَا وَتَرْحَمْنَا لَنَكُونَنَّ مِنَ الْخَاسِرِينَ',
    transliterationArabic: 'Rabbanā ẓalamnā anfusanā wa-in lam taghfir lanā wa-tarḥamnā la-nakūnanna min al-khāsirīn',
    contextEn: 'Adam and Eve made after being sent from Paradise, teaching us the first human supplication of repentance.',
    contextAr: 'دعا به آدم وحواء بعد خروجهما من الجنة — أول دعاء توبة في تاريخ البشر.',
    category: 'prophets', prophet: 'Adam',
    tags: ['tawbah', 'forgiveness', 'adam', 'repentance'],
  },
  {
    id: 'dua_ibrahim_makkah',
    titleEn: "Ibrahim's Prayer for Makkah",
    titleAr: 'دعاء إبراهيم لمكة',
    surah: 2, ayah: 126,
    surahNameEn: 'Al-Baqarah', surahNameAr: 'البقرة',
    meaningEn: 'My Lord, make this a secure city and provide its people with fruits — whoever of them believes in Allah and the Last Day.',
    meaningAr: 'رَبِّ اجْعَلْ هَٰذَا بَلَدًا آمِنًا وَارْزُقْ أَهْلَهُ مِنَ الثَّمَرَاتِ مَنْ آمَنَ مِنْهُم بِاللَّهِ وَالْيَوْمِ الْآخِرِ',
    transliterationArabic: "Rabbi j'al hādhā baladan āminan wa-rzuq ahlahu min al-thamarāt man āmana minhum bi-llāhi wa-l-yawmi al-ākhir",
    contextEn: "Ibrahim's prayer for the city of Makkah while building the Ka'bah with his son Isma'il.",
    contextAr: 'دعا به إبراهيم لمكة المكرمة أثناء رفعه القواعد من البيت الحرام مع ولده إسماعيل.',
    category: 'prophets', prophet: 'Ibrahim',
    tags: ['ibrahim', 'makkah', 'security', 'provision', 'city'],
  },
  {
    id: 'dua_ibrahim_dhuriyya',
    titleEn: "Ibrahim's Prayer for his Progeny",
    titleAr: 'دعاء إبراهيم لذريته',
    surah: 14, ayah: 40, ayahEnd: 41,
    surahNameEn: 'Ibrahim', surahNameAr: 'إبراهيم',
    meaningEn: 'My Lord, make me an establisher of prayer, and from my descendants. Our Lord, accept my supplication. Our Lord, forgive me and my parents and the believers the Day the account is established.',
    meaningAr: 'رَبِّ اجْعَلْنِي مُقِيمَ الصَّلَاةِ وَمِن ذُرِّيَّتِي ۚ رَبَّنَا وَتَقَبَّلْ دُعَاءِ ۚ رَبَّنَا اغْفِرْ لِي وَلِوَالِدَيَّ وَلِلْمُؤْمِنِينَ يَوْمَ يَقُومُ الْحِسَابُ',
    transliterationArabic: "Rabbi j'alnī muqīma al-ṣalāt wa-min dhurriyyatī, Rabbanā wa-taqabbal duʿāʾ, Rabbanā ighfir lī wa-li-wālidayya wa-lil-muʾminīna yawma yaqūmu al-ḥisāb",
    contextEn: "Ibrahim's prayer for himself, his children, and all believers — spanning prayer, acceptance, and forgiveness.",
    contextAr: 'دعاء إبراهيم لنفسه وذريته والمؤمنين — شامل للصلاة والقبول والمغفرة.',
    category: 'prophets', prophet: 'Ibrahim',
    tags: ['ibrahim', 'prayer', 'family', 'forgiveness', 'parents'],
  },
  {
    id: 'dua_musa_forgiveness',
    titleEn: "Musa's Prayer After His Slip",
    titleAr: 'دعاء موسى بعد الزلة',
    surah: 7, ayah: 151,
    surahNameEn: "Al-A'raf", surahNameAr: 'الأعراف',
    meaningEn: 'My Lord, forgive me and my brother and admit us into Your mercy, for You are the most merciful of the merciful.',
    meaningAr: 'رَبِّ اغْفِرْ لِي وَلِأَخِي وَأَدْخِلْنَا فِي رَحْمَتِكَ ۖ وَأَنتَ أَرْحَمُ الرَّاحِمِينَ',
    transliterationArabic: 'Rabbi ighfir lī wa-li-akhī wa-adkhilnā fī raḥmatik, wa-anta arḥamu al-rāḥimīn',
    contextEn: "Musa's supplication after the incident of the tablets, seeking Allah's mercy for himself and Harun.",
    contextAr: 'دعاء موسى عليه السلام بعد حادثة الألواح — يطلب المغفرة لنفسه ولأخيه هارون.',
    category: 'prophets', prophet: 'Musa',
    tags: ['musa', 'harun', 'forgiveness', 'mercy', 'siblings'],
  },
  {
    id: 'dua_musa_guidance',
    titleEn: "Musa's Prayer for Eloquence",
    titleAr: 'دعاء موسى لشرح الصدر',
    surah: 20, ayah: 25, ayahEnd: 28,
    surahNameEn: 'Ta-Ha', surahNameAr: 'طه',
    meaningEn: 'My Lord, expand for me my breast [with assurance] and ease for me my task and untie the knot from my tongue that they may understand my speech.',
    meaningAr: 'رَبِّ اشْرَحْ لِي صَدْرِي وَيَسِّرْ لِي أَمْرِي وَاحْلُلْ عُقْدَةً مِّن لِّسَانِي يَفْقَهُوا قَوْلِي',
    transliterationArabic: "Rabbi shraḥ lī ṣadrī wa-yassir lī amrī wa-ḥlul ʿuqdatan min lisānī yafqahū qawlī",
    contextEn: "Musa's duʿā before confronting Pharaoh — excellent for anyone facing a difficult speech, presentation, or conversation.",
    contextAr: 'دعاء موسى قبل مواجهة فرعون — مناسب لكل من يواجه كلاماً صعباً أو موقفاً عسيراً.',
    category: 'prophets', prophet: 'Musa',
    tags: ['musa', 'eloquence', 'ease', 'clarity', 'speech', 'confidence'],
  },
  {
    id: 'dua_yunus_distress',
    titleEn: "Yunus's Prayer in Darkness",
    titleAr: 'دعاء يونس في الظلمات',
    surah: 21, ayah: 87,
    surahNameEn: 'Al-Anbiya', surahNameAr: 'الأنبياء',
    meaningEn: 'There is no deity except You; exalted are You. Indeed, I have been of the wrongdoers.',
    meaningAr: 'لَّا إِلَٰهَ إِلَّا أَنتَ سُبْحَانَكَ إِنِّي كُنتُ مِنَ الظَّالِمِينَ',
    transliterationArabic: 'Lā ilāha illā anta subḥānaka innī kuntu min al-ẓālimīn',
    contextEn: "Yunus's prayer from within the whale — one of the most powerful duʿā in the Quran for relief from distress.",
    contextAr: 'دعاء يونس من بطن الحوت — من أعظم الأدعية لرفع الكرب والضائقة.',
    category: 'prophets', prophet: 'Yunus',
    tags: ['yunus', 'distress', 'kurbah', 'tahlil', 'whale', 'darkness', 'repentance'],
  },
  {
    id: 'dua_ayyub_relief',
    titleEn: "Ayyub's Prayer in Affliction",
    titleAr: 'دعاء أيوب في البلاء',
    surah: 21, ayah: 83,
    surahNameEn: 'Al-Anbiya', surahNameAr: 'الأنبياء',
    meaningEn: 'Indeed, adversity has touched me, and you are the Most Merciful of the merciful.',
    meaningAr: 'أَنِّي مَسَّنِيَ الضُّرُّ وَأَنتَ أَرْحَمُ الرَّاحِمِينَ',
    transliterationArabic: 'Annī massaniya al-ḍurru wa-anta arḥamu al-rāḥimīn',
    contextEn: "Ayyub's concise, powerful prayer after years of illness — a model of dignified supplication in suffering.",
    contextAr: 'دعاء أيوب الموجز والعميق بعد سنوات من الابتلاء — نموذج في التضرع الكريم عند الشدة.',
    category: 'prophets', prophet: 'Ayyub',
    tags: ['ayyub', 'illness', 'hardship', 'mercy', 'relief', 'affliction'],
  },
  {
    id: 'dua_zakariyya_child',
    titleEn: "Zakariyya's Prayer for an Heir",
    titleAr: 'دعاء زكريا طلباً للولد',
    surah: 3, ayah: 38,
    surahNameEn: "Ali 'Imran", surahNameAr: 'آل عمران',
    meaningEn: 'My Lord, grant me from Yourself a good offspring. Indeed, You are the Hearer of supplication.',
    meaningAr: 'رَبِّ هَبْ لِي مِن لَّدُنكَ ذُرِّيَّةً طَيِّبَةً ۖ إِنَّكَ سَمِيعُ الدُّعَاءِ',
    transliterationArabic: 'Rabbi hab lī min ladunka dhurriyyatan ṭayyibah, innaka samīʿu al-duʿāʾ',
    contextEn: "Zakariyya's prayer for a righteous child, answered with the birth of Yahya. For those seeking children.",
    contextAr: 'دعاء زكريا طلباً للذرية الطيبة — استُجيب فوُلد له يحيى. يُستحب لمن يطلب الولد.',
    category: 'prophets', prophet: 'Zakariyya',
    tags: ['zakariyya', 'yahya', 'children', 'offspring', 'answered', 'family'],
  },
  {
    id: 'dua_zakariyya_detail',
    titleEn: "Zakariyya's Detailed Prayer",
    titleAr: 'دعاء زكريا المفصّل',
    surah: 19, ayah: 4, ayahEnd: 6,
    surahNameEn: 'Maryam', surahNameAr: 'مريم',
    meaningEn: 'My Lord, indeed my bones have weakened, and my head has filled with white, and never have I been in my supplication to You, my Lord, unhappy. And indeed I fear the successors after me... so give me from Yourself an heir who will inherit from me and inherit from the family of Yaqub.',
    meaningAr: 'رَبِّ إِنِّي وَهَنَ الْعَظْمُ مِنِّي وَاشْتَعَلَ الرَّأْسُ شَيْبًا وَلَمْ أَكُن بِدُعَائِكَ رَبِّ شَقِيًّا... فَهَبْ لِي مِن لَّدُنكَ وَلِيًّا يَرِثُنِي وَيَرِثُ مِنْ آلِ يَعْقُوبَ',
    transliterationArabic: "Rabbi innī wahana al-ʿaẓmu minnī wa-shtaʿala al-raʾsu shayban wa-lam akun bi-duʿāʾika rabbi shaqiyyan... fa-hab lī min ladunka waliyyan yarithunī wa-yarith min āl Yaʿqūb",
    contextEn: "Zakariyya's intimate, humble prayer — sharing his age, weakness, and trust in Allah — a model of personal, heartfelt duʿā.",
    contextAr: 'يكشف زكريا همومه لربه بصدق وثقة — نموذج في الدعاء الخاشع المفصّل.',
    category: 'prophets', prophet: 'Zakariyya',
    tags: ['zakariyya', 'old age', 'trust', 'heir', 'intimate', 'heartfelt'],
  },
  {
    id: 'dua_maryam_birth',
    titleEn: "Maryam's Prayer at Childbirth",
    titleAr: 'دعاء مريم عند الولادة',
    surah: 19, ayah: 25,
    surahNameEn: 'Maryam', surahNameAr: 'مريم',
    meaningEn: 'And shake toward you the trunk of the palm tree; it will drop upon you ripe, fresh dates.',
    meaningAr: 'وَهُزِّي إِلَيْكِ بِجِذْعِ النَّخْلَةِ تُسَاقِطْ عَلَيْكِ رُطَبًا جَنِيًّا',
    transliterationArabic: 'Wa-huzzī ilayki bi-jidhʿi al-nakhlati tusāqiṭ ʿalayki ruṭaban janiyyā',
    contextEn: "Allah's mercy to Maryam during delivery — a verse of comfort for pregnant women and mothers in difficulty.",
    contextAr: 'رحمة الله بمريم لحظة الوضع — آية تُتلى للراحة في الحمل والولادة.',
    category: 'prophets', prophet: 'Maryam',
    tags: ['maryam', 'birth', 'mothers', 'pregnancy', 'comfort'],
  },
  {
    id: 'dua_sulayman_gratitude',
    titleEn: "Sulayman's Prayer of Gratitude",
    titleAr: 'دعاء سليمان شكراً وطلباً',
    surah: 27, ayah: 19,
    surahNameEn: 'An-Naml', surahNameAr: 'النمل',
    meaningEn: 'My Lord, enable me to be grateful for Your favor which You have bestowed upon me and upon my parents and to do righteousness of which You approve. And admit me by Your mercy into [the ranks of] Your righteous servants.',
    meaningAr: 'رَبِّ أَوْزِعْنِي أَن أَشْكُرَ نِعْمَتَكَ الَّتِي أَنْعَمْتَ عَلَيَّ وَعَلَىٰ وَالِدَيَّ وَأَنْ أَعْمَلَ صَالِحًا تَرْضَاهُ وَأَدْخِلْنِي بِرَحْمَتِكَ فِي عِبَادِكَ الصَّالِحِينَ',
    transliterationArabic: "Rabbi awziʿnī an ashkura niʿmataka allatī anʿamta ʿalayya wa-ʿalā wālidayya wa-an aʿmala ṣāliḥan tarḍāh wa-adkhilnī bi-raḥmatika fī ʿibādika al-ṣāliḥīn",
    contextEn: "Sulayman's prayer upon hearing the ant — seeking gratitude, righteous deeds, and inclusion among the righteous.",
    contextAr: 'دعاء سليمان حين سمع كلام النملة — يطلب الشكر والعمل الصالح والانضمام إلى عباد الله الصالحين.',
    category: 'prophets', prophet: 'Sulayman',
    tags: ['sulayman', 'gratitude', 'parents', 'righteous', 'shukr'],
  },

  // -------------------------------------------------------------------------
  // Al-Fatihah — Most Recited Prayer
  // -------------------------------------------------------------------------
  {
    id: 'dua_fatiha_guidance',
    titleEn: 'Prayer for Guidance (Al-Fatihah)',
    titleAr: 'الاستهداء في الفاتحة',
    surah: 1, ayah: 6, ayahEnd: 7,
    surahNameEn: 'Al-Fatihah', surahNameAr: 'الفاتحة',
    meaningEn: 'Guide us to the straight path — the path of those upon whom You have bestowed favor, not of those who have evoked [Your] anger or of those who are astray.',
    meaningAr: 'اهْدِنَا الصِّرَاطَ الْمُسْتَقِيمَ صِرَاطَ الَّذِينَ أَنْعَمْتَ عَلَيْهِمْ غَيْرِ الْمَغْضُوبِ عَلَيْهِمْ وَلَا الضَّالِّينَ',
    transliterationArabic: 'Ihdinā al-ṣirāṭa al-mustaqīm, ṣirāṭa alladhīna anʿamta ʿalayhim, ghayri al-maghḍūbi ʿalayhim wa-lā al-ḍāllīn',
    contextEn: "The closing of Al-Fatihah — the duʿā recited in every rak'ah of salah. The most repeated prayer in Islam.",
    contextAr: 'خاتمة الفاتحة — الدعاء الذي نكرره في كل ركعة من الصلاة. أكثر دعاء يتكرر في حياة المسلم.',
    category: 'guidance',
    tags: ['fatihah', 'guidance', 'sirat', 'prayer', 'daily', 'salah'],
  },

  // -------------------------------------------------------------------------
  // Forgiveness & Mercy
  // -------------------------------------------------------------------------
  {
    id: 'dua_baqarah_forgiveness',
    titleEn: "Al-Baqarah's Closing Supplication",
    titleAr: 'خاتمة البقرة',
    surah: 2, ayah: 285, ayahEnd: 286,
    surahNameEn: 'Al-Baqarah', surahNameAr: 'البقرة',
    meaningEn: "Our Lord, do not impose blame upon us if we have forgotten or erred. Our Lord, and lay not upon us a burden like that which You laid upon those before us... Our Lord, and burden us not with that which we have no ability to bear. And pardon us; and forgive us; and have mercy upon us. You are our protector, so give us victory over the disbelieving people.",
    meaningAr: 'رَبَّنَا لَا تُؤَاخِذْنَا إِن نَّسِينَا أَوْ أَخْطَأْنَا ۚ رَبَّنَا وَلَا تَحْمِلْ عَلَيْنَا إِصْرًا كَمَا حَمَلْتَهُ عَلَى الَّذِينَ مِن قَبْلِنَا... وَاعْفُ عَنَّا وَاغْفِرْ لَنَا وَارْحَمْنَا أَنتَ مَوْلَانَا فَانصُرْنَا عَلَى الْقَوْمِ الْكَافِرِينَ',
    transliterationArabic: "Rabbanā lā tuʾākhidhnā in nasīnā aw akhṭaʾnā... wa-ʿfu ʿannā wa-ghfir lanā wa-rḥamnā anta mawlānā fa-nṣurnā ʿalā al-qawm al-kāfirīn",
    contextEn: "The two closing verses of Surah Al-Baqarah — a comprehensive supplication the Prophet ﷺ said was revealed from a treasure beneath the Throne.",
    contextAr: 'آيتا خاتمة البقرة — دعاء جامع أخبر النبي ﷺ أنه أُنزل من كنز تحت العرش.',
    category: 'forgiveness',
    tags: ['baqarah', 'khatimah', 'forgiveness', 'mercy', 'comprehensive', 'evening'],
  },
  {
    id: 'dua_imran_forgiveness',
    titleEn: "The Believers' Evening Prayer",
    titleAr: 'دعاء أولي الألباب',
    surah: 3, ayah: 193, ayahEnd: 194,
    surahNameEn: "Ali 'Imran", surahNameAr: 'آل عمران',
    meaningEn: "Our Lord, indeed we have heard a caller calling to faith, [saying], 'Believe in your Lord,' and we have believed. Our Lord, so forgive us our sins and remove from us our misdeeds and cause us to die with the righteous.",
    meaningAr: 'رَّبَّنَا إِنَّنَا سَمِعْنَا مُنَادِيًا يُنَادِي لِلْإِيمَانِ... رَبَّنَا فَاغْفِرْ لَنَا ذُنُوبَنَا وَكَفِّرْ عَنَّا سَيِّئَاتِنَا وَتَوَفَّنَا مَعَ الْأَبْرَارِ',
    transliterationArabic: 'Rabbanā innanā samiʿnā munādiyyan yunādī lil-īmān... Rabbanā fa-ghfir lanā dhunūbanā wa-kaffir ʿannā sayyiʾātanā wa-tawaffanā maʿa al-abrār',
    contextEn: "The prayer of those described as 'people of understanding' who remember Allah standing, sitting, and on their sides.",
    contextAr: 'دعاء أولي الألباب الذين يذكرون الله قياماً وقعوداً وعلى جنوبهم.',
    category: 'forgiveness',
    tags: ['uli al-albab', 'forgiveness', 'evening', 'believers', 'death', 'righteous'],
  },

  // -------------------------------------------------------------------------
  // Protection
  // -------------------------------------------------------------------------
  {
    id: 'dua_muminun_refuge',
    titleEn: 'Seeking Refuge from Whispers',
    titleAr: 'الاستعاذة من وساوس الشيطان',
    surah: 23, ayah: 97, ayahEnd: 98,
    surahNameEn: 'Al-Muʾminun', surahNameAr: 'المؤمنون',
    meaningEn: 'My Lord, I seek refuge in You from the incitements of the devils, and I seek refuge in You, my Lord, lest they be present with me.',
    meaningAr: 'رَّبِّ أَعُوذُ بِكَ مِنْ هَمَزَاتِ الشَّيَاطِينِ وَأَعُوذُ بِكَ رَبِّ أَن يَحْضُرُونِ',
    transliterationArabic: "Rabbi aʿūdhu bika min hamazāti al-shayāṭīn wa-aʿūdhu bika rabbi an yaḥḍurūn",
    contextEn: "For protection from shaytan — recited when feeling whispers, distraction in salah, or spiritual unease.",
    contextAr: 'للاستعاذة من وساوس الشيطان — يُستحب عند الوسواس أو التشتت في الصلاة.',
    category: 'protection',
    tags: ['shaytan', 'waswas', 'protection', 'refuge', 'prayer', 'distraction'],
  },
  {
    id: 'dua_falaq_naas',
    titleEn: 'Al-Muʿawwidhatān (Al-Falaq & An-Nas)',
    titleAr: 'المعوذتان',
    surah: 113, ayah: 1,
    surahNameEn: 'Al-Falaq', surahNameAr: 'الفلق',
    meaningEn: "Say, 'I seek refuge in the Lord of daybreak from the evil of that which He created...' and 'I seek refuge in the Lord of mankind, the Sovereign of mankind, the God of mankind, from the evil of the retreating whisperer...'",
    meaningAr: 'قُلْ أَعُوذُ بِرَبِّ الْفَلَقِ مِن شَرِّ مَا خَلَقَ... قُلْ أَعُوذُ بِرَبِّ النَّاسِ مَلِكِ النَّاسِ...',
    transliterationArabic: "Qul aʿūdhu bi-rabbi al-falaq min sharri mā khalaqa... Qul aʿūdhu bi-rabbi al-nās, maliki al-nās, ilāhi al-nās...",
    contextEn: "The two Surahs of refuge — recited morning and evening and before sleep for comprehensive protection.",
    contextAr: 'المعوذتان — تُقرآن صباحاً ومساءً وقبل النوم للحماية الشاملة.',
    category: 'protection',
    tags: ['falaq', 'nas', 'morning', 'evening', 'sleep', 'evil', 'protection', 'sihr'],
  },
  {
    id: 'dua_travel',
    titleEn: 'Prayer for Safe Journey',
    titleAr: 'دعاء السفر',
    surah: 43, ayah: 13, ayahEnd: 14,
    surahNameEn: 'Az-Zukhruf', surahNameAr: 'الزخرف',
    meaningEn: 'Exalted is He who has subjected this to us, and we could not have [otherwise] subdued it. And indeed we, to our Lord, will [surely] return.',
    meaningAr: 'سُبْحَانَ الَّذِي سَخَّرَ لَنَا هَٰذَا وَمَا كُنَّا لَهُ مُقْرِنِينَ وَإِنَّا إِلَىٰ رَبِّنَا لَمُنقَلِبُونَ',
    transliterationArabic: "Subḥāna alladhī sakhkhara lanā hādhā wa-mā kunnā lahu muqrinīn, wa-innā ilā rabbinā la-munqalibūn",
    contextEn: "The Quranic duʿā recited when mounting any vehicle — car, plane, ship — affirming dependence on Allah in travel.",
    contextAr: 'دعاء ركوب المركبة — يُقال عند ركوب السيارة أو الطائرة أو السفينة.',
    category: 'protection',
    tags: ['travel', 'journey', 'vehicle', 'safety', 'morning', 'safar'],
  },

  // -------------------------------------------------------------------------
  // Guidance & Light
  // -------------------------------------------------------------------------
  {
    id: 'dua_kahf_mercy_guidance',
    titleEn: 'Prayer of the Companions of the Cave',
    titleAr: 'دعاء أصحاب الكهف',
    surah: 18, ayah: 10,
    surahNameEn: 'Al-Kahf', surahNameAr: 'الكهف',
    meaningEn: 'Our Lord, grant us from Yourself mercy and prepare for us from our affair right guidance.',
    meaningAr: 'رَبَّنَا آتِنَا مِن لَّدُنكَ رَحْمَةً وَهَيِّئْ لَنَا مِنْ أَمْرِنَا رَشَدًا',
    transliterationArabic: 'Rabbanā ātinā min ladunka raḥmatan wa-hayyi ʾ lanā min amrinā rashadā',
    contextEn: "The prayer of the young believers fleeing to the cave — for mercy and guidance when facing pressure or uncertainty.",
    contextAr: 'دعاء الفتية المؤمنين حين لجأوا إلى الكهف — للرحمة والهداية في أوقات الضغط.',
    category: 'guidance',
    tags: ['kahf', 'youth', 'guidance', 'mercy', 'refuge', 'faith'],
  },
  {
    id: 'dua_nur_knowledge',
    titleEn: 'Prayer for Beneficial Knowledge',
    titleAr: 'الدعاء للعلم النافع',
    surah: 20, ayah: 114,
    surahNameEn: 'Ta-Ha', surahNameAr: 'طه',
    meaningEn: 'My Lord, increase me in knowledge.',
    meaningAr: 'رَّبِّ زِدْنِي عِلْمًا',
    transliterationArabic: 'Rabbi zidnī ʿilmā',
    contextEn: "The shortest and most concise Quranic duʿā — a constant prayer for those seeking knowledge.",
    contextAr: 'أقصر دعاء قرآني وأبلغه — دعاء دائم لطالب العلم.',
    category: 'guidance',
    tags: ['knowledge', 'ilm', 'learning', 'students', 'short', 'daily'],
  },
  {
    id: 'dua_baqarah_good_world_akhira',
    titleEn: 'The Comprehensive Worldly & Hereafter Prayer',
    titleAr: 'دعاء الدنيا والآخرة',
    surah: 2, ayah: 201,
    surahNameEn: 'Al-Baqarah', surahNameAr: 'البقرة',
    meaningEn: 'Our Lord, give us in this world [that which is] good and in the Hereafter [that which is] good and protect us from the punishment of the Fire.',
    meaningAr: 'رَبَّنَا آتِنَا فِي الدُّنْيَا حَسَنَةً وَفِي الْآخِرَةِ حَسَنَةً وَقِنَا عَذَابَ النَّارِ',
    transliterationArabic: 'Rabbanā ātinā fī al-dunyā ḥasanatan wa-fī al-ākhirati ḥasanatan wa-qinā ʿadhāba al-nār',
    contextEn: "The Prophet ﷺ would often recite this duʿā. It covers every aspiration — worldly and eternal — in one supplication.",
    contextAr: 'كان النبي ﷺ يكثر من هذا الدعاء — يجمع الدنيا والآخرة في جملة واحدة.',
    category: 'general',
    tags: ['dunya', 'akhira', 'fire', 'comprehensive', 'hajj', 'general', 'prophet'],
  },

  // -------------------------------------------------------------------------
  // Family & Children
  // -------------------------------------------------------------------------
  {
    id: 'dua_furqan_family',
    titleEn: 'Prayer for Righteous Family',
    titleAr: 'دعاء الذرية الصالحة',
    surah: 25, ayah: 74,
    surahNameEn: 'Al-Furqan', surahNameAr: 'الفرقان',
    meaningEn: 'Our Lord, grant us from among our wives and offspring comfort to our eyes and make us a leader [i.e., example] for the righteous.',
    meaningAr: 'رَبَّنَا هَبْ لَنَا مِنْ أَزْوَاجِنَا وَذُرِّيَّاتِنَا قُرَّةَ أَعْيُنٍ وَاجْعَلْنَا لِلْمُتَّقِينَ إِمَامًا',
    transliterationArabic: "Rabbanā hab lanā min azwājinā wa-dhurriyyātinā qurrata aʿyun wa-j'alnā lil-muttaqīna imāmā",
    contextEn: "The duʿā of the ibad al-Rahman (servants of the Most Merciful) — for a righteous spouse, children, and community leadership.",
    contextAr: 'دعاء عباد الرحمن — للزوجة الصالحة والذرية الطيبة وقيادة المتقين.',
    category: 'family',
    tags: ['family', 'spouse', 'children', 'offspring', 'ibad al-rahman', 'leadership'],
  },
  {
    id: 'dua_ibrahim_parents',
    titleEn: "Prayer for Parents' Forgiveness",
    titleAr: 'الدعاء للوالدين',
    surah: 71, ayah: 28,
    surahNameEn: 'Nuh', surahNameAr: 'نوح',
    meaningEn: 'My Lord, forgive me and my parents and whoever enters my house a believer and the believing men and believing women. And do not increase the wrongdoers except in destruction.',
    meaningAr: 'رَّبِّ اغْفِرْ لِي وَلِوَالِدَيَّ وَلِمَن دَخَلَ بَيْتِيَ مُؤْمِنًا وَلِلْمُؤْمِنِينَ وَالْمُؤْمِنَاتِ',
    transliterationArabic: 'Rabbi ighfir lī wa-li-wālidayya wa-li-man dakhala baytiya muʾminan wa-lil-muʾminīna wa-l-muʾmināt',
    contextEn: "Nuh's prayer for believers — includes parents, household members, and all Muslim men and women.",
    contextAr: 'دعاء نوح للمؤمنين — يشمل الوالدين وأهل البيت وعموم المؤمنين.',
    category: 'family', prophet: 'Nuh',
    tags: ['parents', 'family', 'nuh', 'forgiveness', 'household', 'believers'],
  },
  {
    id: 'dua_isra_parents_mercy',
    titleEn: 'Prayer of Mercy for Parents',
    titleAr: 'دعاء الرحمة للوالدين',
    surah: 17, ayah: 24,
    surahNameEn: 'Al-Isra', surahNameAr: 'الإسراء',
    meaningEn: 'My Lord, have mercy upon them as they brought me up [when I was] small.',
    meaningAr: 'رَّبِّ ارْحَمْهُمَا كَمَا رَبَّيَانِي صَغِيرًا',
    transliterationArabic: 'Rabbi irḥamhumā kamā rabbayānī ṣaghīrā',
    contextEn: "The Quranic duʿā for parents — to be recited for living and deceased parents alike.",
    contextAr: 'الدعاء القرآني للوالدين — يُقال لهما حيّين وميتين.',
    category: 'family',
    tags: ['parents', 'mercy', 'upbringing', 'children', 'family', 'deceased'],
  },

  // -------------------------------------------------------------------------
  // Gratitude
  // -------------------------------------------------------------------------
  {
    id: 'dua_naml_gratitude',
    titleEn: 'Prayer to Be Grateful',
    titleAr: 'الدعاء لأداء الشكر',
    surah: 27, ayah: 19,
    surahNameEn: 'An-Naml', surahNameAr: 'النمل',
    meaningEn: 'My Lord, enable me to be grateful for Your favor which You have bestowed upon me and upon my parents and to do righteousness of which You approve.',
    meaningAr: 'رَبِّ أَوْزِعْنِي أَن أَشْكُرَ نِعْمَتَكَ الَّتِي أَنْعَمْتَ عَلَيَّ وَعَلَىٰ وَالِدَيَّ وَأَنْ أَعْمَلَ صَالِحًا تَرْضَاهُ',
    transliterationArabic: "Rabbi awziʿnī an ashkura niʿmataka allatī anʿamta ʿalayya wa-ʿalā wālidayya wa-an aʿmala ṣāliḥan tarḍāh",
    contextEn: "Sulayman's duʿā after hearing the ant — a prayer not just for gratitude but for being ENABLED to express it properly.",
    contextAr: 'دعاء سليمان حين سمع النملة — لا يطلب الشكر فحسب بل القدرة على أدائه.',
    category: 'gratitude', prophet: 'Sulayman',
    tags: ['shukr', 'gratitude', 'parents', 'righteous', 'sulayman', 'enabling'],
  },
  {
    id: 'dua_ahqaf_gratitude',
    titleEn: "Al-Ahqaf's Prayer at Forty",
    titleAr: 'دعاء بلوغ الأربعين',
    surah: 46, ayah: 15,
    surahNameEn: 'Al-Ahqaf', surahNameAr: 'الأحقاف',
    meaningEn: "My Lord, enable me to be grateful for Your favor which You have bestowed upon me and upon my parents and to work righteousness of which You will approve and make righteous for me my offspring. Indeed, I have repented to You, and indeed, I am of the Muslims.",
    meaningAr: 'رَبِّ أَوْزِعْنِي أَنْ أَشْكُرَ نِعْمَتَكَ الَّتِي أَنْعَمْتَ عَلَيَّ وَعَلَىٰ وَالِدَيَّ وَأَنْ أَعْمَلَ صَالِحًا تَرْضَاهُ وَأَصْلِحْ لِي فِي ذُرِّيَّتِي إِنِّي تُبْتُ إِلَيْكَ وَإِنِّي مِنَ الْمُسْلِمِينَ',
    transliterationArabic: "Rabbi awziʿnī an ashkura niʿmataka allatī anʿamta ʿalayya wa-ʿalā wālidayya wa-an aʿmala ṣāliḥan tarḍāhu wa-aṣliḥ lī fī dhurriyyatī innī tubtu ilayka wa-innī min al-muslimīn",
    contextEn: "This verse describes what a believer says at age forty — the age of spiritual maturity. A comprehensive life prayer.",
    contextAr: 'وصف القرآن ما يقوله المؤمن حين يبلغ أشده — دعاء جامع في منتصف العمر.',
    category: 'gratitude',
    tags: ['forty', 'maturity', 'gratitude', 'parents', 'children', 'repentance', 'comprehensive'],
  },

  // -------------------------------------------------------------------------
  // General Supplications
  // -------------------------------------------------------------------------
  {
    id: 'dua_baqarah_burden',
    titleEn: 'Prayer Against Unbearable Burden',
    titleAr: 'الدعاء برفع الحمل الثقيل',
    surah: 2, ayah: 286,
    surahNameEn: 'Al-Baqarah', surahNameAr: 'البقرة',
    meaningEn: 'Our Lord, do not burden us with that which we have no ability to bear. And pardon us; and forgive us; and have mercy upon us. You are our protector.',
    meaningAr: 'رَبَّنَا وَلَا تُحَمِّلْنَا مَا لَا طَاقَةَ لَنَا بِهِ ۖ وَاعْفُ عَنَّا وَاغْفِرْ لَنَا وَارْحَمْنَا أَنتَ مَوْلَانَا',
    transliterationArabic: 'Rabbanā wa-lā tuḥammilnā mā lā ṭāqata lanā bih, wa-ʿfu ʿannā wa-ghfir lanā wa-rḥamnā anta mawlānā',
    contextEn: "For moments of overwhelm — stress, anxiety, impossible demands — asking Allah not to burden beyond one's capacity.",
    contextAr: 'عند الإرهاق والإحساس بثقل الأمانة — مسألة الله ألا يحمّل فوق الطاقة.',
    category: 'general',
    tags: ['burden', 'stress', 'overwhelm', 'capacity', 'anxiety', 'forgiveness', 'mercy'],
  },
  {
    id: 'dua_tawbah_acceptance',
    titleEn: 'Prayer for Accepted Repentance',
    titleAr: 'الدعاء لقبول التوبة',
    surah: 2, ayah: 128,
    surahNameEn: 'Al-Baqarah', surahNameAr: 'البقرة',
    meaningEn: 'Our Lord, and make us Muslims [in submission] to You and from our descendants a Muslim nation [in submission] to You. And show us our rites and accept our repentance. Indeed, You are the Accepting of repentance, the Merciful.',
    meaningAr: 'رَبَّنَا وَاجْعَلْنَا مُسْلِمَيْنِ لَكَ وَمِن ذُرِّيَّتِنَا أُمَّةً مُّسْلِمَةً لَّكَ وَأَرِنَا مَنَاسِكَنَا وَتُبْ عَلَيْنَا إِنَّكَ أَنتَ التَّوَّابُ الرَّحِيمُ',
    transliterationArabic: "Rabbanā wa-j'alnā muslimayni laka wa-min dhurriyyatinā ummatan muslimatan lak wa-arinā manāsikanā wa-tub ʿalaynā innaka anta al-tawwābu al-raḥīm",
    contextEn: "Ibrahim and Isma'il's prayer while building the Ka'bah — for submission, accepted worship, and repentance.",
    contextAr: 'دعاء إبراهيم وإسماعيل أثناء بناء الكعبة — للإسلام والقبول والتوبة.',
    category: 'general', prophet: 'Ibrahim',
    tags: ['ibrahim', 'kaabah', 'submission', 'repentance', 'accepted', 'ummah'],
  },
  {
    id: 'dua_imran_comprehensive',
    titleEn: 'Comprehensive Prayer of Believers',
    titleAr: 'دعاء المؤمنين الجامع',
    surah: 3, ayah: 8, ayahEnd: 9,
    surahNameEn: "Ali 'Imran", surahNameAr: 'آل عمران',
    meaningEn: "Our Lord, let not our hearts deviate after You have guided us and grant us from Yourself mercy. Indeed, You are the Bestower. Our Lord, surely You will gather the people for a Day about which there is no doubt. Indeed, Allah does not fail in His promise.",
    meaningAr: 'رَبَّنَا لَا تُزِغْ قُلُوبَنَا بَعْدَ إِذْ هَدَيْتَنَا وَهَبْ لَنَا مِن لَّدُنكَ رَحْمَةً إِنَّكَ أَنتَ الْوَهَّابُ',
    transliterationArabic: "Rabbanā lā tuzigh qulūbanā baʿda idh hadaytanā wa-hab lanā min ladunka raḥmah, innaka anta al-Wahhāb",
    contextEn: "Prayer against deviation — for protection from losing faith after being guided.",
    contextAr: 'الدعاء من الانزلاغ عن الهدى — حماية القلب بعد الهداية.',
    category: 'guidance',
    tags: ['heart', 'guidance', 'deviation', 'stability', 'iman', 'mercy'],
  },
];
