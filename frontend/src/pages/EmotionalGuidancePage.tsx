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
import { Heart, ChevronRight, ArrowLeft, BookOpen } from 'lucide-react';
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
  keyRefEn: string;
  keyRefAr: string;
  hadithEn: string;
  hadithAr: string;
  scholarlySrcEn: string;
  scholarlySrcAr: string;
}

const EMOTIONAL_STATES: readonly EmotionalState[] = [
  {
    id: 'anxious',
    labelEn: 'Anxious & Worried',
    labelAr: 'قلق ومتوتر',
    emoji: '😰',
    color: 'blue',
    quranResponseEn: 'The Quran addresses anxiety through three therapeutic lenses: divine knowledge (Allah knows every fear — 2:255 Ayat al-Kursi), divine control (nothing happens without His permission — 64:11), and the promise of relief (ease is inherent in hardship, simultaneously — 94:5-6). The prescription is explicit in 13:28: remembrance (dhikr) is the Quranic antidote for a restless heart — not a metaphor, but a theological and practical prescription with 14 centuries of Islamic spiritual psychology behind it.',
    quranResponseAr: 'يعالج القرآن القلق من ثلاثة محاور علاجية: المعرفة الإلهية (الله يعلم كل خوف — 2:255 آية الكرسي)، والسيطرة الإلهية (لا شيء يقع إلا بإذنه — 64:11)، ووعد الفرج (اليسر ملازم للعسر في آنٍ معاً — 94:5-6). والوصفة صريحة في 13:28: ذكر الله هو ترياق القرآن للقلب المضطرب — ليس مجازاً، بل منهج روحي وعلمي موثَّق في علم النفس الإسلامي على مدى أربعة عشر قرناً.',
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
    keyRefEn: '13:28 — Surah Ar-Ra\'d',
    keyRefAr: '13:28 — سورة الرعد',
    hadithEn: '"Make things easy, do not make them difficult. Give glad tidings, do not repel people." — Bukhari 69. And: "There is no disease that Allah has created except that He has also created its treatment." — Bukhari 5678',
    hadithAr: '"يسِّروا ولا تعسِّروا، وبشِّروا ولا تنفِّروا." — البخاري 69. و"ما أنزل الله داءً إلا أنزل له شفاءً." — البخاري 5678',
    scholarlySrcEn: 'Ibn al-Qayyim, Madarij al-Salikin (on tawakkul); Ibn Kathir Tafsir (13:28); Al-Ghazali, Ihya Ulum al-Din (Book of Tawakkul)',
    scholarlySrcAr: 'ابن القيم، مدارج السالكين (في التوكل)؛ تفسير ابن كثير (13:28)؛ الغزالي، إحياء علوم الدين (كتاب التوكل)',
  },
  {
    id: 'sad',
    labelEn: 'Sad & Grieving',
    labelAr: 'حزين وفي حداد',
    emoji: '😢',
    color: 'violet',
    quranResponseEn: 'The Quran does not command you not to grieve — it validates grief. Prophet Yaqub wept for Yusuf until he lost his sight from sorrow (12:84). The Prophet ﷺ himself wept for his companions and children. The Quran couples grief with certainty: Surah Ad-Duha (93) was revealed precisely when the Prophet ﷺ was in a period of profound sadness — Allah\'s first words to him were comfort and affirmation of divine care. The Islamic framework for grief includes sabr (patient endurance, not passive acceptance) and the utterance of "Inna lillahi" (2:156) as a declaration of meaning within loss.',
    quranResponseAr: 'لا يأمرك القرآن بعدم الحزن — بل يُشرعنه ويُقرّه. بكى النبي يعقوب على يوسف حتى ابيضت عيناه من الحزن (12:84)، وبكى النبي ﷺ على صحابته وأهله. يقرن القرآن الحزن باليقين: نزلت سورة الضحى (93) تحديداً في لحظة حزن عميق وانقطاع وحي — فكانت أول كلمات الله له عزاءً وتأكيداً للرعاية الإلهية. يتضمن الإطار الإسلامي للحزن الصبر (بوصفه تحملاً إيجابياً، لا استسلاماً) وقول "إنا لله" (2:156) إعلاناً للمعنى داخل المصيبة.',
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
    keyRefEn: '93:5 — Surah Ad-Duha',
    keyRefAr: '93:5 — سورة الضحى',
    hadithEn: '"When a person says Inna lillahi wa inna ilayhi raji\'un at the time of a calamity, Allah blesses him with something better than what he lost." — Sahih Muslim 918',
    hadithAr: '"ما من عبد تصيبه مصيبة فيقول: إنا لله وإنا إليه راجعون، إلا أثابه الله خيراً منها." — صحيح مسلم 918',
    scholarlySrcEn: 'Ibn Kathir Tafsir (93); Ibn al-Jawzi, Sayd al-Khatir (on grief and consolation); Al-Ghazali, Ihya (Book of Patience and Gratitude)',
    scholarlySrcAr: 'تفسير ابن كثير (93)؛ ابن الجوزي، صيد الخاطر (في الحزن والعزاء)؛ الغزالي، إحياء علوم الدين (كتاب الصبر والشكر)',
  },
  {
    id: 'hopeless',
    labelEn: 'Hopeless & Despairing',
    labelAr: 'فاقد الأمل ويائس',
    emoji: '😔',
    color: 'emerald',
    quranResponseEn: 'The Quran issues a direct divine prohibition against despair. In 39:53 Allah addresses "My servants who have transgressed against themselves" — those who feel most unworthy — with the command never to despair. In 12:87 Prophet Yaqub tells his sons: "Do not despair of Allah\'s relief — only the disbelieving people despair." Despair (ya\'s) is framed as a theological error. The story of Yusuf demonstrates hope across decades of trial: thrown in a well, enslaved, imprisoned — then exalted as a ruler. The timeline of divine plans stretches far beyond any human moment of despair.',
    quranResponseAr: 'يُصدر القرآن نهياً إلهياً صريحاً عن القنوط. تُخاطب الآية 39:53 "يا عبادي الذين أسرفوا على أنفسهم" — أي من يشعرون بأنهم الأقل استحقاقاً — بالأمر الصريح بألا يقنطوا. وفي 12:87 يقول يعقوب لأبنائه: "لا تيأسوا من روح الله — إنه لا ييأس من روح الله إلا القوم الكافرون." القنوط في هذا الإطار خطأ عقدي. تُثبت قصة يوسف صمود الأمل عبر عقود من الابتلاء: ألقي في البئر، واسترقّ، وسُجن — ثم نُصِّب حاكماً. أفق المشيئة الإلهية يمتد أبعد بكثير من أي لحظة قنوط إنسانية.',
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
    keyRefEn: '39:53 — Surah Az-Zumar',
    keyRefAr: '39:53 — سورة الزمر',
    hadithEn: 'Allah says: "I am with My servant\'s expectation of Me, so let him think of Me as he wishes." — Bukhari 7405 (Hadith Qudsi). The divine promise: your hope in Allah is always justified.',
    hadithAr: 'قال الله: "أنا عند ظن عبدي بي، فليظن بي ما شاء." — البخاري 7405 (حديث قدسي). الوعد الإلهي: حسن الظن بالله دائماً مُسوَّغ.',
    scholarlySrcEn: "Ibn al-Qayyim, al-Fawa'id (on hope and despair); Sayyid Qutb, Fi Zilal al-Quran (on 12:87 and 39:53); Ibn Kathir Tafsir (39:53)",
    scholarlySrcAr: 'ابن القيم، الفوائد (في الرجاء واليأس)؛ سيد قطب، في ظلال القرآن (في 12:87 و39:53)؛ تفسير ابن كثير (39:53)',
  },
  {
    id: 'guilty',
    labelEn: 'Guilty & Regretful',
    labelAr: 'مذنب وآسف',
    emoji: '😞',
    color: 'rose',
    quranResponseEn: 'The Quran frames repentance as "tawbah" — returning, not punishment-seeking. Allah calls Himself "al-Tawwab" (2:37, 2:128) — the Ever-Returning — meaning He turns toward you as you turn toward Him. The story of Adam and Eve (7:23) models the Quranic path: honest acknowledgment, direct appeal for mercy, and trust in divine forgiveness — and they received both mercy and purpose. No sin exceeds divine mercy (39:53). The only closing of the door is persistent rejection of faith itself, which is why 39:53 is addressed specifically to those who "have transgressed against themselves" — the most burdened of hearts.',
    quranResponseAr: 'يُصوِّر القرآن التوبة بوصفها رجوعاً، لا طلب عقاب. يُسمّي الله نفسه "التواب" (2:37، 2:128) — الكثير العفو — أي أنه يتوب عليك كما تتوب إليه. تُجسّد قصة آدم وحواء (7:23) مسار التوبة القرآني: إقرار صادق بالتقصير، ولجوء مباشر لطلب الرحمة، وثقة بالعفو الإلهي — فنالا المغفرة والرسالة معاً. لا ذنب يتجاوز رحمة الله (39:53). الباب لا يُغلق إلا بالإصرار على رد الإيمان ذاته، وهذا يفسّر لماذا تُخاطب الآية 39:53 بالذات "الذين أسرفوا على أنفسهم" — أشد القلوب ثقلاً.',
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
    keyRefEn: "7:23 — Surah Al-A'raf (Adam's repentance model)",
    keyRefAr: 'سورة الأعراف (نموذج توبة آدم) — 7:23',
    hadithEn: 'Allah says: "O son of Adam, so long as you call upon Me and hope in Me, I will forgive you no matter what you have done. O son of Adam, if your sins reached the clouds of the sky and you sought My forgiveness, I would forgive you." — Tirmidhi 3540 (Hadith Qudsi)',
    hadithAr: 'قال الله: "يا ابن آدم، إنك ما دعوتني ورجوتني غفرت لك على ما كان فيك ولا أبالي. يا ابن آدم، لو بلغت ذنوبك عنان السماء ثم استغفرتني غفرت لك." — الترمذي 3540 (حديث قدسي)',
    scholarlySrcEn: "Ibn Rajab al-Hanbali, Jami' al-Ulum wal-Hikam (on repentance); Ibn al-Qayyim, al-Jawab al-Kafi (on the breadth of Allah's mercy); Imam Nawawi, Riyadh al-Salihin",
    scholarlySrcAr: 'ابن رجب الحنبلي، جامع العلوم والحكم (في التوبة)؛ ابن القيم، الجواب الكافي (في سعة رحمة الله)؛ النووي، رياض الصالحين',
  },
  {
    id: 'grateful',
    labelEn: 'Grateful & Joyful',
    labelAr: 'شاكر وفرح',
    emoji: '😊',
    color: 'amber',
    quranResponseEn: 'Gratitude in the Quran carries cosmic weight: "If you are grateful, I will surely increase you" (14:7) is a direct divine economic principle, not merely a suggestion. Surah Al-Rahman (55) repeats "Which of your Lord\'s favors will you deny?" 31 times — a structured meditation on gratitude spanning creation, provision, knowledge, mercy, and paradise. The word "hamd" (praise-gratitude) opens the Quran itself (1:2), making every recitation of Al-Fatihah an act of gratitude. Classical Islamic scholars define shukr as three-part: recognizing the blessing, attributing it to the giver, and expressing it with heart, tongue, and action.',
    quranResponseAr: 'الشكر في القرآن ذو ثقل كوني: "لئن شكرتم لأزيدنكم" (14:7) مبدأ إلهي مباشر، لا مجرد توصية. وتُكرّر سورة الرحمن (55) "فبأي آلاء ربكما تكذبان" 31 مرة — تأملاً منهجياً في الشكر يشمل الخلق والرزق والعلم والرحمة والجنة. وتفتتح الحمد القرآن ذاته (1:2)، فكل قراءة للفاتحة عبادة شكر. يُعرِّف العلماء الكلاسيكيون الشكر بثلاثة أجزاء: الاعتراف بالنعمة، وردّها إلى المنعم، والتعبير عنها بالقلب واللسان والجوارح.',
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
    keyRefEn: '14:7 — Surah Ibrahim (the promise of increase)',
    keyRefAr: '14:7 — سورة إبراهيم (وعد الزيادة)',
    hadithEn: '"Alhamdulillah (All praise is due to Allah) fills the scale." — Sahih Muslim 223. And: "He who does not thank people has not thanked Allah." — Abu Dawud 4811, Tirmidhi 1954',
    hadithAr: '"الحمد لله تملأ الميزان." — صحيح مسلم 223. و"من لا يشكر الناس لا يشكر الله." — أبو داود 4811، الترمذي 1954',
    scholarlySrcEn: "Al-Ghazali, Ihya Ulum al-Din (Kitab al-Shukr); Ibn al-Qayyim, Uddat al-Sabirin wa Dhakhirat al-Shakirin; Ibn Kathir Tafsir (14:7, 55:13)",
    scholarlySrcAr: 'الغزالي، إحياء علوم الدين (كتاب الشكر)؛ ابن القيم، عدة الصابرين وذخيرة الشاكرين؛ تفسير ابن كثير (14:7، 55:13)',
  },
  {
    id: 'angry',
    labelEn: 'Angry & Frustrated',
    labelAr: 'غاضب ومحبط',
    emoji: '😤',
    color: 'orange',
    quranResponseEn: 'The Quran elevates anger management as a mark of taqwa: "al-kadhimin al-ghayth" (those who contain their rage, 3:134) are among the muttaqin (God-conscious). The Arabic "kadhim" means to contain or swallow — the anger may exist, but its expression is governed. The Quran documents Musa\'s anger (7:150-154) not to condemn it, but to show a prophet processing and channelling intense emotion authentically. The spiritual prescription offered is seeking refuge from Shaytan (7:200-201) — acknowledging that anger is often externally triggered and can be addressed at its spiritual root.',
    quranResponseAr: 'يرفع القرآن إدارة الغضب إلى مرتبة التقوى: "والكاظمين الغيظ" (3:134) من المتقين. "الكاظم" يعني من يحبس ويُمسك — الغضب قد يكون، لكن ضبطه هو العبادة. يُوثّق القرآن غضب موسى (7:150-154) لا لإدانته، بل ليُريك نبياً يعالج مشاعر حادة ويُوجّهها بصدق. والعلاج الروحي المقدَّم هو الاستعاذة من الشيطان (7:200-201) — إدراكاً لأن الغضب كثيراً ما يُغذّيه مُحرّك خارجي يمكن معالجته من جذره الروحي.',
    surahs: [
      { surah: 3, reasonEn: "Ali 'Imran: 'Those who suppress their anger and pardon people — Allah loves the doers of good' (3:134)", reasonAr: "آل عمران: 'وَالْكَاظِمِينَ الْغَيْظَ وَالْعَافِينَ عَنِ النَّاسِ ۗ وَاللَّهُ يُحِبُّ الْمُحْسِنِينَ' (3:134)" },
      { surah: 42, reasonEn: "Ash-Shura: 'And those who avoid major sins... and when they are angry, they forgive' (42:37)", reasonAr: "الشورى: 'وَالَّذِينَ يَجْتَنِبُونَ كَبَائِرَ الْإِثْمِ... وَإِذَا مَا غَضِبُوا هُمْ يَغْفِرُونَ' (42:37)" },
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
    keyRefEn: '3:134 — Surah Ali \'Imran (those who contain anger)',
    keyRefAr: '3:134 — سورة آل عمران (كاظمو الغيظ)',
    hadithEn: '"The strong person is not the one who defeats others in wrestling, but the one who controls himself when angry." — Bukhari 6114. And: "If one of you becomes angry while standing, let him sit; if the anger does not leave, let him lie down." — Abu Dawud 4782',
    hadithAr: '"ليس الشديد بالصُّرَعة، إنما الشديد الذي يملك نفسه عند الغضب." — البخاري 6114. و"إذا غضب أحدكم وهو قائم فليجلس، فإن ذهب عنه الغضب وإلا فليضطجع." — أبو داود 4782',
    scholarlySrcEn: "Ibn al-Qayyim, Rawdhat al-Muhibbin (on anger and self-mastery); Imam al-Nawawi, Riyadh al-Salihin (chapter on anger); Al-Ghazali, Ihya (on the condemnation of anger)",
    scholarlySrcAr: 'ابن القيم، روضة المحبين (في الغضب والسيطرة على النفس)؛ النووي، رياض الصالحين (باب الغضب)؛ الغزالي، إحياء علوم الدين (في ذم الغضب)',
  },
  {
    id: 'lonely',
    labelEn: 'Lonely & Disconnected',
    labelAr: 'وحيد ومنفصل',
    emoji: '😶',
    color: 'teal',
    quranResponseEn: 'Three Quranic verses establish divine presence at escalating levels of intimacy: 57:4 ("He is with you wherever you are"), 58:7 ("He is with them wherever they are"), and 50:16 ("closer to him than his jugular vein"). The last verse refers to Allah\'s awareness even of your thoughts before you articulate them. A Hadith Qudsi (Bukhari 7405) makes this intimate: "I am with My servant when he thinks of Me." The Quran also offers human community as a spiritual anchor: "Hold fast to the rope of Allah together" (3:103) — isolation is the exception, not the default Islamic state.',
    quranResponseAr: 'تُرسي ثلاث آيات قرآنية الحضور الإلهي بمستويات متصاعدة من القرب: 57:4 ("وهو معكم أين ما كنتم")، 58:7 ("هو معهم أين ما كانوا")، 50:16 ("أقرب إليه من حبل الوريد"). تُشير الآية الأخيرة إلى أن الله يُدرك أفكارك قبل أن تُعبّر عنها. ويُجسّد الحديث القدسي (البخاري 7405) هذا القرب: "أنا مع عبدي حين يذكرني." ويُقدّم القرآن الجماعة ملاذاً روحياً: "واعتصموا بحبل الله جميعاً" (3:103) — العزلة استثناء، لا قاعدة في الإسلام.',
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
    keyRefEn: '50:16 — Surah Qaf (closer than your jugular vein)',
    keyRefAr: '50:16 — سورة ق (أقرب من حبل الوريد)',
    hadithEn: 'Allah says: "I am with My servant when he thinks of Me. If he remembers Me privately, I remember him privately. If he mentions Me in a gathering, I mention him in a better gathering." — Bukhari 7405 (Hadith Qudsi)',
    hadithAr: 'قال الله: "أنا عند ظن عبدي بي، وأنا معه إذا ذكرني؛ فإن ذكرني في نفسه ذكرته في نفسي، وإن ذكرني في ملأ ذكرته في ملأ خير منه." — البخاري 7405 (حديث قدسي)',
    scholarlySrcEn: "Ibn al-Qayyim, Tariq al-Hijratayn (on divine company in spiritual journey); Al-Ghazali, Ihya (Book of Remembrance); Ibn Kathir Tafsir (50:16, 57:4)",
    scholarlySrcAr: 'ابن القيم، طريق الهجرتين (في الصحبة الإلهية)؛ الغزالي، إحياء علوم الدين (كتاب الذكر)؛ تفسير ابن كثير (50:16، 57:4)',
  },
  {
    id: 'overwhelmed',
    labelEn: 'Overwhelmed & Burned Out',
    labelAr: 'مثقل الكاهل ومحترق',
    emoji: '😩',
    color: 'purple',
    quranResponseEn: 'The Quran\'s guarantee in 2:286 ("Allah does not burden a soul beyond its capacity") is a divine constitutional principle, not merely consolation. Whatever you carry, the Quran declares by divine authority that your capacity matches your burden — even when you cannot feel it. Surah Ash-Sharh (94) uses the Arabic "ma\'" (WITH, not "ba\'d" = AFTER): ease is simultaneous with hardship, inherent within it, not deferred. Verse 20:2 establishes that the Quran was not revealed to cause you distress — difficulty in practice signals something is misapplied, not that the path is wrong.',
    quranResponseAr: 'الضمانة في 2:286 ("لا يُكلّف الله نفساً إلا وسعها") مبدأ إلهي دستوري، لا مجرد عزاء. مهما حملت، يُقرّ القرآن بسلطة إلهية أن طاقتك تُوازي حملك — حتى حين لا تحسّ ذلك. وتستخدم سورة الشرح (94) حرف "مع" لا "بعد": اليسر مصاحب للعسر في آنٍ معاً، كامن فيه، لا مُؤجَّل إلى ما بعده. وتؤسّس الآية 20:2 أن القرآن لم يُنزَل لتشقى — صعوبة الممارسة إشارة إلى خلل في التطبيق، لا في المنهج.',
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
    keyRefEn: '94:5-6 — Surah Ash-Sharh (ease WITH hardship, twice)',
    keyRefAr: '94:5-6 — سورة الشرح (اليسر مع العسر مرتين)',
    hadithEn: '"No fatigue, illness, worry, sadness, harm or distress befalls a Muslim — even a thorn that pricks him — except that Allah removes some of his sins thereby." — Bukhari 5641, 5642',
    hadithAr: '"ما يصيب المسلم من نصب ولا وصب ولا همٍّ ولا حزن ولا أذى ولا غمٍّ، حتى الشوكة يُشاكها، إلا كفّر الله بها من خطاياه." — البخاري 5641، 5642',
    scholarlySrcEn: "Ibn al-Jawzi, Sayd al-Khatir (on spiritual burnout and renewal); Al-Baghawi Tafsir (on 94:5); Ibn al-Qayyim, Zad al-Ma'ad (on the therapeutic nature of worship)",
    scholarlySrcAr: 'ابن الجوزي، صيد الخاطر (في الاحتراق الروحي والتجديد)؛ تفسير البغوي (في 94:5)؛ ابن القيم، زاد المعاد (في الطابع العلاجي للعبادة)',
  },
  {
    id: 'seeking',
    labelEn: 'Spiritually Seeking',
    labelAr: 'باحث روحياً',
    emoji: '🔍',
    color: 'indigo',
    quranResponseEn: 'The Quran opens with a seeker\'s dua: "Guide us to the straight path" (1:6) — recited 17 times daily in obligatory prayers, making every Muslim a perpetual seeker. The Quran describes itself as "hudhan lil-muttaqin" (guidance for those with taqwa, 2:2) — for those who bring an open, seeking heart. Surah Al-Kahf contains the Quran\'s most detailed story of knowledge-seeking: Musa (a prophet) travels to the limits of the known world to reach al-Khidr (18:66-82), modeling intellectual humility. Allah commands the Prophet ﷺ directly: "Say: My Lord, increase me in knowledge" (20:114).',
    quranResponseAr: 'يفتتح القرآن بدعاء الباحث: "اهدنا الصراط المستقيم" (1:6) — يُتلى 17 مرة يومياً في الفرائض، فكل مسلم باحث دائم. ويصف القرآن نفسه "هدى للمتقين" (2:2) — مخصوصاً لمن يحمل قلباً منفتحاً يبحث. وتتضمن سورة الكهف أكثر قصص طلب العلم تفصيلاً: يسافر موسى (نبي) إلى أطراف العالم المعروف ليبلغ الخضر (18:66-82) نموذجاً للتواضع العلمي. ويأمر الله نبيّه ﷺ مباشرةً: "قل ربّ زدني علماً" (20:114).',
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
    keyRefEn: "1:6 — Surah Al-Fatihah (the seeker's daily prayer)",
    keyRefAr: '1:6 — سورة الفاتحة (دعاء الباحث اليومي)',
    hadithEn: '"Whoever takes a path seeking knowledge, Allah will make easy for him a path to Paradise." — Sahih Muslim 2699. And: "The angels lower their wings in approval for the seeker of knowledge." — Abu Dawud 3641, Tirmidhi 2682',
    hadithAr: '"من سلك طريقاً يطلب فيه علماً سهّل الله له به طريقاً إلى الجنة." — صحيح مسلم 2699. و"إن الملائكة لتضع أجنحتها لطالب العلم رضاً بما يصنع." — أبو داود 3641، الترمذي 2682',
    scholarlySrcEn: "Ibn al-Qayyim, Miftah Dar al-Sa'adah (Book 1: on the virtue of knowledge); Al-Ghazali, Ihya Ulum al-Din (Kitab al-Ilm); Ibn Kathir Tafsir (2:2, 18:66-82, 20:114)",
    scholarlySrcAr: 'ابن القيم، مفتاح دار السعادة (ج. 1 في فضل العلم)؛ الغزالي، إحياء علوم الدين (كتاب العلم)؛ تفسير ابن كثير (2:2، 18:66-82، 20:114)',
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
          <p className={clsx('text-sm text-gray-600 max-w-md mx-auto leading-relaxed', isRtl && 'font-arabic')}>
            {isRtl ? selected.quranResponseAr : selected.quranResponseEn}
          </p>
        </div>

        {/* Quranic reference callout */}
        <div className={clsx('flex gap-2 p-2.5 rounded-xl bg-amber-50 border border-amber-100 mb-4', isRtl && 'flex-row-reverse')}>
          <BookOpen className="w-3.5 h-3.5 text-amber-500 flex-shrink-0 mt-0.5" />
          <div className="min-w-0">
            <p className={clsx('text-[10px] font-semibold text-amber-600 mb-0.5', isRtl && 'font-arabic')}>
              {isRtl ? 'المرجع القرآني الرئيسي' : 'Primary Quranic Reference'}
            </p>
            <p className={clsx('text-xs text-amber-800 leading-relaxed', isRtl ? 'font-arabic' : 'italic')}>
              {isRtl ? selected.keyRefAr : selected.keyRefEn}
            </p>
          </div>
        </div>

        {/* Affirmation verse */}
        <div className={clsx('rounded-2xl border p-5 mb-5 text-center', affirmColors)}>
          <p className="font-arabic text-xl leading-loose mb-2" dir="rtl">
            {selected.affirmationAr}
          </p>
          {!isRtl && (
            <p className="text-sm italic text-gray-600 mb-1">{selected.affirmationEn}</p>
          )}
          <p className={clsx('text-xs text-gray-400', isRtl && 'font-arabic')}>{selected.affirmatioVerseRef}</p>
        </div>

        {/* Relevant Surahs */}
        <div className="mb-4">
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

        {/* Hadith reference */}
        <div className={clsx('flex gap-2 p-2.5 rounded-xl bg-teal-50 border border-teal-100 mb-4', isRtl && 'flex-row-reverse')}>
          <span className="text-teal-500 flex-shrink-0 text-sm leading-none mt-0.5">📜</span>
          <div className="min-w-0">
            <p className={clsx('text-[10px] font-semibold text-teal-600 mb-0.5', isRtl && 'font-arabic')}>
              {isRtl ? 'حديث شريف' : 'Related Hadith'}
            </p>
            <p className={clsx('text-xs text-teal-800 leading-relaxed', isRtl ? 'font-arabic' : 'italic')}>
              {isRtl ? selected.hadithAr : selected.hadithEn}
            </p>
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
          className={clsx('flex items-center gap-3 p-4 rounded-xl border bg-white hover:shadow-sm transition-shadow mb-4', isRtl && 'flex-row-reverse')}
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

        {/* Scholarly sources */}
        <p className={clsx('text-[10px] text-gray-400 leading-relaxed', isRtl && 'font-arabic text-right')}>
          <span className="font-medium text-gray-500">{isRtl ? 'المصادر: ' : 'Sources: '}</span>
          {isRtl ? selected.scholarlySrcAr : selected.scholarlySrcEn}
        </p>

        {/* Attribution */}
        <p className={clsx('text-[10px] text-gray-300 text-center mt-4', isRtl && 'font-arabic')}>
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
