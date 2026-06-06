/**
 * Quran Topic Seeds — navigation taxonomy for Phase V.
 *
 * Each seed is a *candidate* topic. The scanner turns seeds into ayah links;
 * the resulting links default to reviewStatus="needs_review" and never
 * auto-promote to "verified".
 *
 * Hard rules:
 *   - Seed topics are navigation aids, not tafsir claims.
 *   - All Arabic aliases are written either in plain script or in normalised
 *     form; the scanner normalises both sides before matching (strip
 *     tashkeel, hamza, alif-variants, ة→ه, ى→ي).
 *   - Cross-references to existing storyIds / entityIds / themeIds /
 *     emotionIds must already exist in the platform; the validator does not
 *     enforce all existence checks (some downstream IDs are intentionally
 *     forward-defined), but reviewer notes flag mismatches.
 */

import type { QuranTopicSeed } from '../types/quranTopicAtlas';

function seed(s: QuranTopicSeed): QuranTopicSeed {
  return {
    relatedEntities: [],
    relatedStories: [],
    relatedThemes: [],
    relatedEmotions: [],
    warnings: [],
    ...s,
  };
}

// ---------------------------------------------------------------------------
// 1. Faith and Tawhid
// ---------------------------------------------------------------------------

export const FAITH_TOPICS: QuranTopicSeed[] = [
  seed({
    topicId: 'topic_allah',
    topicType: 'faith',
    labelArabic: 'الله',
    labelEnglish: 'Allah',
    aliasesArabic: ['الله', 'لله'],
    aliasesEnglish: ['Allah', 'God'],
    warnings: ['Bare lemma — extremely high frequency; rely on entity/concept anchoring for safe linking.'],
  }),
  seed({
    topicId: 'topic_tawhid',
    topicType: 'faith',
    labelArabic: 'التوحيد',
    labelEnglish: 'Tawhid',
    aliasesArabic: ['وحده', 'لا إله إلا', 'لا اله الا', 'إله واحد', 'اله واحد'],
    aliasesEnglish: ['Tawhid', 'oneness of God', 'monotheism'],
  }),
  seed({
    topicId: 'topic_shirk',
    topicType: 'faith',
    labelArabic: 'الشرك',
    labelEnglish: 'Shirk',
    aliasesArabic: ['شركاء', 'الشرك', 'يشركون', 'تشرك', 'الأنداد', 'الانداد'],
    aliasesEnglish: ['shirk', 'polytheism', 'associating partners'],
  }),
  seed({
    topicId: 'topic_iman',
    topicType: 'faith',
    labelArabic: 'الإيمان',
    labelEnglish: 'Iman',
    aliasesArabic: ['آمنوا', 'امنوا', 'الإيمان', 'الايمان', 'الذين آمنوا', 'الذين امنوا'],
    aliasesEnglish: ['iman', 'faith', 'believers'],
  }),
  seed({
    topicId: 'topic_kufr',
    topicType: 'faith',
    labelArabic: 'الكفر',
    labelEnglish: 'Kufr',
    aliasesArabic: ['كفروا', 'الكفر', 'الكافرين', 'يكفرون'],
    aliasesEnglish: ['kufr', 'disbelief'],
  }),
  seed({
    topicId: 'topic_nifaq',
    topicType: 'faith',
    labelArabic: 'النفاق',
    labelEnglish: 'Hypocrisy (nifaq)',
    aliasesArabic: ['المنافقين', 'المنافقون', 'النفاق', 'نافقوا'],
    aliasesEnglish: ['hypocrisy', 'hypocrites'],
  }),
];

// ---------------------------------------------------------------------------
// 2. Worship
// ---------------------------------------------------------------------------

export const WORSHIP_TOPICS: QuranTopicSeed[] = [
  seed({
    topicId: 'topic_salah',
    topicType: 'worship',
    labelArabic: 'الصلاة',
    labelEnglish: 'Prayer (Salah)',
    aliasesArabic: ['الصلاة', 'الصلوة', 'أقيموا الصلاة', 'يقيمون الصلاة'],
    aliasesEnglish: ['salah', 'prayer'],
  }),
  seed({
    topicId: 'topic_zakat',
    topicType: 'worship',
    labelArabic: 'الزكاة',
    labelEnglish: 'Zakat',
    aliasesArabic: ['الزكاة', 'الزكوة', 'آتوا الزكاة'],
    aliasesEnglish: ['zakat', 'almsgiving'],
  }),
  seed({
    topicId: 'topic_fasting',
    topicType: 'worship',
    labelArabic: 'الصيام',
    labelEnglish: 'Fasting (Sawm)',
    aliasesArabic: ['الصيام', 'الصوم', 'صيام', 'كتب عليكم الصيام', 'رمضان'],
    aliasesEnglish: ['fasting', 'sawm', 'Ramadan'],
  }),
  seed({
    topicId: 'topic_hajj',
    topicType: 'worship',
    labelArabic: 'الحج',
    labelEnglish: 'Hajj',
    aliasesArabic: ['الحج', 'حج البيت', 'العمرة'],
    aliasesEnglish: ['hajj', 'pilgrimage', 'umrah'],
  }),
  seed({
    topicId: 'topic_dua',
    topicType: 'worship',
    labelArabic: 'الدعاء',
    labelEnglish: "Du'a",
    aliasesArabic: ['ادعوا', 'ربنا', 'دعوني', 'دعاء', 'استجيب', 'استجبت'],
    aliasesEnglish: ["dua", 'supplication', 'prayer of asking'],
  }),
  seed({
    topicId: 'topic_dhikr',
    topicType: 'worship',
    labelArabic: 'الذكر',
    labelEnglish: 'Dhikr',
    aliasesArabic: ['اذكروا', 'الذاكرين', 'تذكرون', 'يذكرون', 'سبحان'],
    aliasesEnglish: ['dhikr', 'remembrance'],
    warnings: ['"الذكر" is also used for the Quran itself; downgrade ambiguous matches.'],
  }),
];

// ---------------------------------------------------------------------------
// 3. Character and ethics
// ---------------------------------------------------------------------------

export const ETHICS_TOPICS: QuranTopicSeed[] = [
  seed({
    topicId: 'topic_patience',
    topicType: 'ethics',
    labelArabic: 'الصبر',
    labelEnglish: 'Patience',
    aliasesArabic: ['الصبر', 'الصابرين', 'اصبر', 'اصبروا', 'صبر'],
    aliasesEnglish: ['patience', 'sabr', 'steadfastness'],
    relatedEmotions: ['emotion_sadness', 'emotion_endurance'],
  }),
  seed({
    topicId: 'topic_gratitude',
    topicType: 'ethics',
    labelArabic: 'الشكر',
    labelEnglish: 'Gratitude',
    aliasesArabic: ['الشكر', 'الشاكرين', 'اشكروا', 'تشكرون'],
    aliasesEnglish: ['gratitude', 'shukr', 'thankfulness'],
    relatedEmotions: ['emotion_gratitude'],
  }),
  seed({
    topicId: 'topic_honesty',
    topicType: 'ethics',
    labelArabic: 'الصدق',
    labelEnglish: 'Honesty',
    aliasesArabic: ['الصدق', 'الصادقين', 'صدقوا'],
    aliasesEnglish: ['truthfulness', 'honesty', 'sidq'],
  }),
  seed({
    topicId: 'topic_justice',
    topicType: 'ethics',
    labelArabic: 'العدل',
    labelEnglish: 'Justice',
    aliasesArabic: ['العدل', 'القسط', 'بالعدل', 'يأمر بالعدل'],
    aliasesEnglish: ['justice', 'qist', 'fairness'],
  }),
  seed({
    topicId: 'topic_mercy',
    topicType: 'ethics',
    labelArabic: 'الرحمة',
    labelEnglish: 'Mercy',
    aliasesArabic: ['الرحمة', 'رحمته', 'الرحمن', 'الرحيم'],
    aliasesEnglish: ['mercy', 'rahma'],
    relatedEmotions: ['emotion_hope'],
  }),
  seed({
    topicId: 'topic_forgiveness',
    topicType: 'ethics',
    labelArabic: 'العفو والمغفرة',
    labelEnglish: 'Forgiveness',
    aliasesArabic: ['الغفور', 'يغفر', 'استغفروا', 'استغفر', 'العفو', 'المغفرة'],
    aliasesEnglish: ['forgiveness', 'maghfira', 'pardon'],
    relatedEmotions: ['emotion_guilt', 'emotion_hope'],
  }),
  seed({
    topicId: 'topic_humility',
    topicType: 'ethics',
    labelArabic: 'التواضع',
    labelEnglish: 'Humility',
    aliasesArabic: ['تواضع', 'الخاشعين', 'خاشعون', 'الخشوع'],
    aliasesEnglish: ['humility', 'khushu'],
  }),
  seed({
    topicId: 'topic_arrogance',
    topicType: 'ethics',
    labelArabic: 'الكبر',
    labelEnglish: 'Arrogance',
    aliasesArabic: ['استكبر', 'استكبروا', 'المستكبرين', 'الكبرياء'],
    aliasesEnglish: ['arrogance', 'pride', 'istikbar'],
  }),
  seed({
    topicId: 'topic_envy',
    topicType: 'ethics',
    labelArabic: 'الحسد',
    labelEnglish: 'Envy',
    aliasesArabic: ['حسد', 'حاسد', 'يحسدون'],
    aliasesEnglish: ['envy', 'hasad'],
  }),
  seed({
    topicId: 'topic_anger',
    topicType: 'ethics',
    labelArabic: 'الغضب',
    labelEnglish: 'Anger',
    aliasesArabic: ['الغضب', 'غضب', 'غاضبا', 'الكاظمين الغيظ', 'الغيظ'],
    aliasesEnglish: ['anger', 'wrath', 'ghadab'],
  }),
  seed({
    topicId: 'topic_trustworthiness',
    topicType: 'ethics',
    labelArabic: 'الأمانة',
    labelEnglish: 'Trustworthiness',
    aliasesArabic: ['الأمانة', 'الأمانات', 'أمين'],
    aliasesEnglish: ['trustworthiness', 'amana'],
  }),
];

// ---------------------------------------------------------------------------
// 4. Emotional and spiritual healing
// ---------------------------------------------------------------------------

export const EMOTIONAL_TOPICS: QuranTopicSeed[] = [
  seed({
    topicId: 'topic_sadness',
    topicType: 'emotional_theme',
    labelArabic: 'الحزن',
    labelEnglish: 'Sadness',
    aliasesArabic: ['تحزن', 'الحزن', 'لا تحزن', 'حزن'],
    aliasesEnglish: ['sadness', 'grief'],
    relatedEmotions: ['emotion_sadness'],
  }),
  seed({
    topicId: 'topic_fear',
    topicType: 'emotional_theme',
    labelArabic: 'الخوف',
    labelEnglish: 'Fear',
    aliasesArabic: ['الخوف', 'تخافوا', 'تخاف', 'لا تخف'],
    aliasesEnglish: ['fear', 'khawf'],
    relatedEmotions: ['emotion_fear'],
  }),
  seed({
    topicId: 'topic_anxiety',
    topicType: 'emotional_theme',
    labelArabic: 'الهم والحزن',
    labelEnglish: 'Anxiety',
    aliasesArabic: ['الهم', 'الكرب', 'يحزنك', 'لا تيأسوا'],
    aliasesEnglish: ['anxiety', 'distress', 'worry'],
    relatedEmotions: ['emotion_anxiety'],
  }),
  seed({
    topicId: 'topic_hope',
    topicType: 'emotional_theme',
    labelArabic: 'الرجاء',
    labelEnglish: 'Hope',
    aliasesArabic: ['يرجون', 'الرجاء', 'فأبشروا', 'تفلحون'],
    aliasesEnglish: ['hope', 'raja'],
    relatedEmotions: ['emotion_hope'],
  }),
  seed({
    topicId: 'topic_guilt',
    topicType: 'emotional_theme',
    labelArabic: 'الذنب',
    labelEnglish: 'Guilt',
    aliasesArabic: ['ذنوبهم', 'ذنوبكم', 'الذنوب', 'أخطأنا'],
    aliasesEnglish: ['guilt', 'sin'],
    relatedEmotions: ['emotion_guilt'],
  }),
  seed({
    topicId: 'topic_repentance',
    topicType: 'emotional_theme',
    labelArabic: 'التوبة',
    labelEnglish: 'Repentance',
    aliasesArabic: ['التوبة', 'تابوا', 'يتوب', 'استغفروا', 'تاب الله'],
    aliasesEnglish: ['repentance', 'tawba'],
  }),
  seed({
    topicId: 'topic_tawakkul',
    topicType: 'emotional_theme',
    labelArabic: 'التوكل',
    labelEnglish: 'Trust in Allah',
    aliasesArabic: ['توكل', 'يتوكلون', 'المتوكلين', 'حسبنا الله'],
    aliasesEnglish: ['tawakkul', 'reliance', 'trust in God'],
  }),
  seed({
    topicId: 'topic_sakina',
    topicType: 'emotional_theme',
    labelArabic: 'السكينة',
    labelEnglish: 'Tranquility',
    aliasesArabic: ['السكينة', 'لتسكنوا', 'مطمئنة', 'الاطمئنان'],
    aliasesEnglish: ['tranquility', 'sakina', 'peace of heart'],
  }),
];

// ---------------------------------------------------------------------------
// 5. Stories and trials
// ---------------------------------------------------------------------------

export const STORY_TOPICS: QuranTopicSeed[] = [
  seed({
    topicId: 'topic_prophets_trials',
    topicType: 'story_theme',
    labelArabic: 'ابتلاء الأنبياء',
    labelEnglish: 'Trials of the prophets',
    aliasesArabic: ['ابتلى', 'ابتلينا', 'الصابرين', 'فصبر'],
    aliasesEnglish: ['trials of prophets'],
  }),
  seed({
    topicId: 'topic_rejection_of_messengers',
    topicType: 'story_theme',
    labelArabic: 'تكذيب الرسل',
    labelEnglish: 'Rejection of messengers',
    aliasesArabic: ['كذبوا الرسل', 'كذب', 'كذبت', 'يكذبون'],
    aliasesEnglish: ['rejection of messengers'],
  }),
  seed({
    topicId: 'topic_rescue_after_hardship',
    topicType: 'story_theme',
    labelArabic: 'النجاة بعد الشدة',
    labelEnglish: 'Rescue after hardship',
    aliasesArabic: ['فأنجيناه', 'نجيناه', 'فنجيناه', 'أنجاكم'],
    aliasesEnglish: ['rescue after hardship'],
  }),
  seed({
    topicId: 'topic_migration',
    topicType: 'story_theme',
    labelArabic: 'الهجرة',
    labelEnglish: 'Migration',
    aliasesArabic: ['هاجروا', 'يهاجر', 'المهاجرين'],
    aliasesEnglish: ['migration', 'hijra'],
  }),
  seed({
    topicId: 'topic_oppression',
    topicType: 'story_theme',
    labelArabic: 'الظلم والاستضعاف',
    labelEnglish: 'Oppression',
    aliasesArabic: ['ظلم', 'الظالمين', 'المستضعفين', 'تظلمون'],
    aliasesEnglish: ['oppression', 'wrongdoing'],
  }),
  seed({
    topicId: 'topic_repentance_after_error',
    topicType: 'story_theme',
    labelArabic: 'العودة بعد الخطأ',
    labelEnglish: 'Repentance after error',
    aliasesArabic: ['فتاب عليه', 'تاب الله', 'فأناب'],
    aliasesEnglish: ['repentance after error'],
  }),
];

// ---------------------------------------------------------------------------
// 6. Hereafter
// ---------------------------------------------------------------------------

export const HEREAFTER_TOPICS: QuranTopicSeed[] = [
  seed({
    topicId: 'topic_resurrection',
    topicType: 'hereafter',
    labelArabic: 'البعث',
    labelEnglish: 'Resurrection',
    aliasesArabic: ['يبعثون', 'البعث', 'يوم يبعثون', 'يوم يقوم الناس'],
    aliasesEnglish: ['resurrection'],
  }),
  seed({
    topicId: 'topic_judgment',
    topicType: 'hereafter',
    labelArabic: 'يوم القيامة',
    labelEnglish: 'Day of Judgment',
    aliasesArabic: ['يوم القيامة', 'يوم الدين', 'الحساب'],
    aliasesEnglish: ['Day of Judgment', 'accountability'],
  }),
  seed({
    topicId: 'topic_paradise',
    topicType: 'hereafter',
    labelArabic: 'الجنة',
    labelEnglish: 'Paradise',
    aliasesArabic: ['الجنة', 'جنات', 'جنات النعيم', 'الفردوس'],
    aliasesEnglish: ['paradise', 'janna', 'gardens'],
  }),
  seed({
    topicId: 'topic_hellfire',
    topicType: 'hereafter',
    labelArabic: 'النار',
    labelEnglish: 'Hellfire',
    aliasesArabic: ['النار', 'جهنم', 'سعير', 'الجحيم'],
    aliasesEnglish: ['hellfire', 'jahannam'],
  }),
  seed({
    topicId: 'topic_accountability',
    topicType: 'hereafter',
    labelArabic: 'الحساب',
    labelEnglish: 'Accountability',
    aliasesArabic: ['الحساب', 'يحاسبون', 'سريع الحساب', 'موازين'],
    aliasesEnglish: ['accountability', 'reckoning'],
  }),
];

// ---------------------------------------------------------------------------
// 7. Creation and signs
// ---------------------------------------------------------------------------

export const CREATION_TOPICS: QuranTopicSeed[] = [
  seed({
    topicId: 'topic_heavens_earth',
    topicType: 'creation_sign',
    labelArabic: 'السماوات والأرض',
    labelEnglish: 'Heavens and earth',
    aliasesArabic: ['السماوات والأرض', 'السماوات', 'الأرض', 'خلق السماوات'],
    aliasesEnglish: ['heavens and earth'],
  }),
  seed({
    topicId: 'topic_rain',
    topicType: 'creation_sign',
    labelArabic: 'المطر والماء',
    labelEnglish: 'Rain and water',
    aliasesArabic: ['ماء', 'الماء', 'مطرا', 'أنزل من السماء'],
    aliasesEnglish: ['rain', 'water'],
  }),
  seed({
    topicId: 'topic_mountains',
    topicType: 'creation_sign',
    labelArabic: 'الجبال',
    labelEnglish: 'Mountains',
    aliasesArabic: ['الجبال', 'جبال', 'رواسي'],
    aliasesEnglish: ['mountains'],
  }),
  seed({
    topicId: 'topic_sea',
    topicType: 'creation_sign',
    labelArabic: 'البحر',
    labelEnglish: 'Sea',
    aliasesArabic: ['البحر', 'البحرين', 'البحار'],
    aliasesEnglish: ['sea'],
  }),
  seed({
    topicId: 'topic_animals',
    topicType: 'creation_sign',
    labelArabic: 'الحيوان والأنعام',
    labelEnglish: 'Animals',
    aliasesArabic: ['الأنعام', 'دابة', 'الدواب', 'بهيمة'],
    aliasesEnglish: ['animals', 'livestock', 'creatures'],
  }),
  seed({
    topicId: 'topic_night_day',
    topicType: 'creation_sign',
    labelArabic: 'الليل والنهار',
    labelEnglish: 'Night and day',
    aliasesArabic: ['الليل والنهار', 'الليل', 'النهار', 'فلق الإصباح'],
    aliasesEnglish: ['night and day'],
  }),
  seed({
    topicId: 'topic_human_creation',
    topicType: 'creation_sign',
    labelArabic: 'خلق الإنسان',
    labelEnglish: 'Human creation',
    aliasesArabic: ['خلق الإنسان', 'الإنسان', 'الانسان', 'من نطفة', 'من تراب', 'من طين'],
    aliasesEnglish: ['creation of humans', 'human creation'],
  }),
];

// ---------------------------------------------------------------------------
// 8. Social life
// ---------------------------------------------------------------------------

export const SOCIAL_TOPICS: QuranTopicSeed[] = [
  seed({
    topicId: 'topic_parents',
    topicType: 'social_theme',
    labelArabic: 'الوالدان',
    labelEnglish: 'Parents',
    aliasesArabic: ['الوالدين', 'الوالدان', 'بالوالدين', 'أمك', 'أبيك'],
    aliasesEnglish: ['parents'],
  }),
  seed({
    topicId: 'topic_family',
    topicType: 'social_theme',
    labelArabic: 'الأسرة',
    labelEnglish: 'Family',
    aliasesArabic: ['أهلك', 'أهلكم', 'أهله', 'الأقربون'],
    aliasesEnglish: ['family', 'household'],
  }),
  seed({
    topicId: 'topic_marriage',
    topicType: 'social_theme',
    labelArabic: 'الزواج',
    labelEnglish: 'Marriage',
    aliasesArabic: ['أزواج', 'أزواجكم', 'فانكحوا', 'النكاح'],
    aliasesEnglish: ['marriage'],
  }),
  seed({
    topicId: 'topic_children',
    topicType: 'social_theme',
    labelArabic: 'الأبناء والأولاد',
    labelEnglish: 'Children',
    aliasesArabic: ['أولادكم', 'الأولاد', 'البنين', 'ذرية'],
    aliasesEnglish: ['children'],
  }),
  seed({
    topicId: 'topic_neighbors',
    topicType: 'social_theme',
    labelArabic: 'الجار',
    labelEnglish: 'Neighbors',
    aliasesArabic: ['الجار', 'الجار ذي القربى', 'الجار الجنب'],
    aliasesEnglish: ['neighbors'],
  }),
  seed({
    topicId: 'topic_community',
    topicType: 'social_theme',
    labelArabic: 'الأمة والجماعة',
    labelEnglish: 'Community',
    aliasesArabic: ['أمة', 'الأمة', 'بالمعروف', 'الناس'],
    aliasesEnglish: ['community', 'ummah'],
  }),
  seed({
    topicId: 'topic_wealth',
    topicType: 'social_theme',
    labelArabic: 'المال',
    labelEnglish: 'Wealth',
    aliasesArabic: ['المال', 'الأموال', 'الكنوز', 'الذهب والفضة'],
    aliasesEnglish: ['wealth'],
  }),
  seed({
    topicId: 'topic_charity',
    topicType: 'social_theme',
    labelArabic: 'الصدقة',
    labelEnglish: 'Charity',
    aliasesArabic: ['الصدقات', 'صدقة', 'أنفقوا', 'الإنفاق'],
    aliasesEnglish: ['charity', 'sadaqa', 'spending in the way of Allah'],
  }),
  seed({
    topicId: 'topic_trade',
    topicType: 'social_theme',
    labelArabic: 'التجارة',
    labelEnglish: 'Trade',
    aliasesArabic: ['تجارة', 'البيع', 'الميزان', 'الكيل'],
    aliasesEnglish: ['trade', 'commerce'],
  }),
];

// ---------------------------------------------------------------------------
// 9. Knowledge and guidance
// ---------------------------------------------------------------------------

export const GUIDANCE_TOPICS: QuranTopicSeed[] = [
  seed({
    topicId: 'topic_revelation',
    topicType: 'concept_cluster',
    labelArabic: 'الوحي والتنزيل',
    labelEnglish: 'Revelation',
    aliasesArabic: ['أنزل', 'أوحى', 'الوحي', 'منزل', 'تنزيل'],
    aliasesEnglish: ['revelation'],
  }),
  seed({
    topicId: 'topic_quran',
    topicType: 'concept_cluster',
    labelArabic: 'القرآن',
    labelEnglish: 'The Quran',
    aliasesArabic: ['القرآن', 'الفرقان', 'الكتاب', 'الذكر'],
    aliasesEnglish: ['Quran', 'Furqan', 'The Book'],
    warnings: ['Generic aliases overlap with non-Quran usages; downgrade.'],
  }),
  seed({
    topicId: 'topic_wisdom',
    topicType: 'concept_cluster',
    labelArabic: 'الحكمة',
    labelEnglish: 'Wisdom',
    aliasesArabic: ['الحكمة', 'الحكماء', 'يؤت الحكمة'],
    aliasesEnglish: ['wisdom', 'hikma'],
  }),
  seed({
    topicId: 'topic_guidance',
    topicType: 'concept_cluster',
    labelArabic: 'الهداية',
    labelEnglish: 'Guidance',
    aliasesArabic: ['الهدى', 'يهدي', 'اهدنا', 'المهتدين'],
    aliasesEnglish: ['guidance', 'huda'],
  }),
  seed({
    topicId: 'topic_misguidance',
    topicType: 'concept_cluster',
    labelArabic: 'الضلال',
    labelEnglish: 'Misguidance',
    aliasesArabic: ['الضالين', 'يضل', 'الضلالة', 'ضلوا'],
    aliasesEnglish: ['misguidance', 'dalal'],
  }),
  seed({
    topicId: 'topic_reflection',
    topicType: 'concept_cluster',
    labelArabic: 'التدبر والتفكر',
    labelEnglish: 'Reflection',
    aliasesArabic: ['يتفكرون', 'تتفكروا', 'يتدبرون', 'التفكر'],
    aliasesEnglish: ['reflection', 'tadabbur', 'tafakkur'],
  }),
  seed({
    topicId: 'topic_signs',
    topicType: 'concept_cluster',
    labelArabic: 'الآيات',
    labelEnglish: 'Signs',
    aliasesArabic: ['آيات', 'الآيات', 'لآيات', 'من آياته'],
    aliasesEnglish: ['signs', 'ayat'],
  }),
];

// ---------------------------------------------------------------------------
// 10. Commands and prohibitions
// ---------------------------------------------------------------------------

export const COMMAND_PROHIBITION_TOPICS: QuranTopicSeed[] = [
  seed({
    topicId: 'topic_command_worship',
    topicType: 'command',
    labelArabic: 'الأمر بالعبادة',
    labelEnglish: 'Command to worship',
    aliasesArabic: ['اعبدوا', 'فاعبدوا', 'فاعبدوني', 'لا تعبدوا إلا'],
    aliasesEnglish: ['command to worship Allah'],
  }),
  seed({
    topicId: 'topic_command_justice',
    topicType: 'command',
    labelArabic: 'الأمر بالعدل',
    labelEnglish: 'Command to justice',
    aliasesArabic: ['يأمر بالعدل', 'بالقسط', 'كونوا قوامين'],
    aliasesEnglish: ['command to justice'],
  }),
  seed({
    topicId: 'topic_prohibition_oppression',
    topicType: 'prohibition',
    labelArabic: 'النهي عن الظلم',
    labelEnglish: 'Prohibition of oppression',
    aliasesArabic: ['لا تظلموا', 'لا تظلمن', 'لا يحب الظالمين'],
    aliasesEnglish: ['prohibition of oppression'],
  }),
  seed({
    topicId: 'topic_prohibition_arrogance',
    topicType: 'prohibition',
    labelArabic: 'النهي عن الكبر',
    labelEnglish: 'Prohibition of arrogance',
    aliasesArabic: ['لا تستكبروا', 'لا تمش في الأرض مرحا', 'لا يحب المستكبرين'],
    aliasesEnglish: ['prohibition of arrogance'],
  }),
  seed({
    topicId: 'topic_prohibition_corruption',
    topicType: 'prohibition',
    labelArabic: 'النهي عن الفساد',
    labelEnglish: 'Prohibition of corruption',
    aliasesArabic: ['لا تفسدوا', 'الفساد في الأرض', 'يفسدون'],
    aliasesEnglish: ['prohibition of corruption'],
  }),
];

// ---------------------------------------------------------------------------
// Combined export
// ---------------------------------------------------------------------------

export const QURAN_TOPIC_SEEDS: QuranTopicSeed[] = [
  ...FAITH_TOPICS,
  ...WORSHIP_TOPICS,
  ...ETHICS_TOPICS,
  ...EMOTIONAL_TOPICS,
  ...STORY_TOPICS,
  ...HEREAFTER_TOPICS,
  ...CREATION_TOPICS,
  ...SOCIAL_TOPICS,
  ...GUIDANCE_TOPICS,
  ...COMMAND_PROHIBITION_TOPICS,
];

export function getTopicSeedById(topicId: string): QuranTopicSeed | undefined {
  return QURAN_TOPIC_SEEDS.find((t) => t.topicId === topicId);
}

export function getTopicIds(): string[] {
  return QURAN_TOPIC_SEEDS.map((t) => t.topicId);
}
