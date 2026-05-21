/**
 * Canonical Quran Story Registry — shared schema for /stories and /story-atlas.
 *
 * Goals:
 *   - Single source of truth merging authored stories, generated prophet
 *     story pages, and entity / topic / knowledge-graph layers.
 *   - Every entry carries explicit Quran references — never invented.
 *   - Every generated candidate defaults to needs_review.
 *
 * Read by:
 *   - frontend/src/pages/StoryAtlasPage.tsx
 *   - frontend/src/pages/StoriesPage.tsx (via storyRegistryAdapter)
 *   - scripts/validate-quran-story-registry.ts
 *   - backend/app/api/routes/story_atlas_registry.py
 */

export type RegistryStoryCategory =
  | 'prophet'
  | 'prophetic_sirah'
  | 'person'
  | 'nation'
  | 'parable'
  | 'historical'
  | 'unseen'
  | 'compact_profile'
  | 'needs_review';

export type RegistryStorySourceType =
  | 'authored_story'
  | 'prophet_story_page'
  | 'entity_story_cluster'
  | 'generated_candidate';

export type RegistryStoryReviewStatus =
  | 'verified'
  | 'needs_review'
  | 'missing_metadata';

export type RegistryQuranReferenceLinkType =
  | 'explicit'
  | 'contextual'
  | 'coreference'
  | 'story_segment'
  | 'needs_review';

export interface RegistryQuranReference {
  surahNumber: number;
  ayahStart: number;
  ayahEnd?: number;
  linkType: RegistryQuranReferenceLinkType;
  reviewStatus: 'verified' | 'needs_review';
}

export interface RegistryStoryEntry {
  storyId: string;
  titleArabic: string;
  titleEnglish: string;
  category: RegistryStoryCategory;
  sourceType: RegistryStorySourceType;
  quranReferences: RegistryQuranReference[];
  relatedProphets: string[];
  relatedEntities: string[];
  relatedTopics: string[];
  relatedStories: string[];
  segmentCount: number;
  surahCount: number;
  ayahRangeCount: number;
  hasDetailPage: boolean;
  detailRoute?: string;
  reviewStatus: RegistryStoryReviewStatus;
  humanReviewRequired: boolean;
  warnings: string[];
  /**
   * Free-form thematic tags inherited from the manifest (e.g. "patience",
   * "repentance"). Helpful for theme-based search but unstructured.
   */
  themes: string[];
  /**
   * Structured subcategory tags using a "group:tag" convention so the UI
   * can present a two-level filter. Examples: "animal:cow", "animal:bee",
   * "object:staff", "place:cave", "miracle:sea_parting".
   *
   * The first segment (before the colon) is the parent group; the second
   * segment is the specific tag. A story can belong to many subcategories.
   * Defaults to [] when the storyId is not present in the hand-authored
   * subcategory map.
   */
  subcategories: string[];
  /**
   * Main characters / figures inherited from the manifest. Used by the UI
   * for "people" facets that aren't necessarily prophets.
   */
  mainFigures: string[];
  /**
   * Canonical person IDs that appear in this story. Resolved by the build
   * script from mainFigures aliases (Fir'awn → person_firawn) and from
   * the story's relatedProphets list (prophet_musa kept verbatim). Allows
   * the UI to facet stories by person without depending on free-text
   * spelling variants in mainFigures.
   */
  peopleIds: string[];
}

export interface RegistryCoverageSummary {
  totalStories: number;
  authoredStories: number;
  prophetProfiles: number;
  generatedCandidates: number;
  missingMetadataCount: number;
  surahsCovered: number;
  prophetsCovered: number;
  ayahRangesLinked: number;
  reviewPendingCount: number;
}

export interface QuranStoryRegistryFile {
  version: string;
  generatedAt: string;
  categories: RegistryStoryCategory[];
  coverage: RegistryCoverageSummary;
  stories: RegistryStoryEntry[];
  warnings: string[];
}

export const REGISTRY_CATEGORY_LABELS: Record<
  RegistryStoryCategory,
  { ar: string; en: string }
> = {
  prophet: { ar: 'الأنبياء', en: 'Prophets' },
  prophetic_sirah: { ar: 'السيرة النبوية', en: 'Prophetic Sirah' },
  person: { ar: 'شخصيات', en: 'People' },
  nation: { ar: 'الأمم', en: 'Nations' },
  parable: { ar: 'أمثال', en: 'Parables' },
  historical: { ar: 'تاريخية', en: 'Historical' },
  unseen: { ar: 'الغيب', en: 'Unseen' },
  compact_profile: { ar: 'ملفات موجزة', en: 'Compact Profiles' },
  needs_review: { ar: 'تحتاج مراجعة', en: 'Needs Review' },
};

export const REGISTRY_CATEGORY_ORDER: RegistryStoryCategory[] = [
  'prophet',
  'prophetic_sirah',
  'person',
  'nation',
  'parable',
  'historical',
  'unseen',
  'compact_profile',
  'needs_review',
];

// ---------------------------------------------------------------------------
// Subcategory taxonomy ("group:tag" convention)
// ---------------------------------------------------------------------------

/**
 * Top-level subcategory groups. Each story may belong to many subcategories,
 * across more than one group (e.g. "animal:cow" + "object:calf_gold" +
 * "vice:idolatry" for the Golden Calf incident).
 */
export type SubcategoryGroup =
  | 'animal'
  | 'place'
  | 'object'
  | 'event'
  | 'miracle'
  | 'family'
  | 'role'
  | 'afterlife'
  | 'nature'
  | 'virtue'
  | 'vice';

export const SUBCATEGORY_GROUP_ORDER: SubcategoryGroup[] = [
  'animal',
  'place',
  'object',
  'event',
  'miracle',
  'family',
  'role',
  'afterlife',
  'nature',
  'virtue',
  'vice',
];

export const SUBCATEGORY_GROUP_LABELS: Record<SubcategoryGroup, { ar: string; en: string }> = {
  animal: { ar: 'الحيوانات', en: 'Animals' },
  place: { ar: 'الأماكن', en: 'Places' },
  object: { ar: 'الأشياء', en: 'Objects' },
  event: { ar: 'الأحداث', en: 'Events' },
  miracle: { ar: 'المعجزات', en: 'Miracles' },
  family: { ar: 'العائلة', en: 'Family' },
  role: { ar: 'الأدوار', en: 'Roles' },
  afterlife: { ar: 'الآخرة', en: 'Afterlife' },
  nature: { ar: 'الطبيعة', en: 'Nature' },
  virtue: { ar: 'الفضائل', en: 'Virtues' },
  vice: { ar: 'الرذائل', en: 'Vices' },
};

/**
 * Bilingual labels for individual subcategory tags. Keyed by the full
 * "group:tag" string so the same short word (e.g. "garden") can map to a
 * different label under "place" than under "object".
 *
 * Tags not in this table fall back to a humanised version of the tag word.
 */
export const SUBCATEGORY_TAG_LABELS: Record<string, { ar: string; en: string }> = {
  // animals
  'animal:cow': { ar: 'البقرة', en: 'Cow' },
  'animal:calf': { ar: 'العجل', en: 'Calf' },
  'animal:bee': { ar: 'النحل', en: 'Bee' },
  'animal:elephant': { ar: 'الفيل', en: 'Elephant' },
  'animal:ant': { ar: 'النملة', en: 'Ant' },
  'animal:spider': { ar: 'العنكبوت', en: 'Spider' },
  'animal:fly': { ar: 'الذباب', en: 'Fly' },
  'animal:hoopoe': { ar: 'الهدهد', en: 'Hoopoe' },
  'animal:raven': { ar: 'الغراب', en: 'Raven' },
  'animal:dog': { ar: 'الكلب', en: 'Dog' },
  'animal:fish': { ar: 'السمكة', en: 'Fish' },
  'animal:whale': { ar: 'الحوت', en: 'Whale' },
  'animal:camel': { ar: 'الناقة', en: 'She-Camel' },
  'animal:horse': { ar: 'الخيل', en: 'Horses' },
  'animal:donkey': { ar: 'الحمار', en: 'Donkey' },
  'animal:snake': { ar: 'الحية', en: 'Serpent' },
  'animal:birds': { ar: 'الطير', en: 'Birds' },
  'animal:sheep': { ar: 'الغنم', en: 'Sheep' },
  'animal:wolf': { ar: 'الذئب', en: 'Wolf' },
  'animal:monkey': { ar: 'القردة', en: 'Monkeys' },
  'animal:pig': { ar: 'الخنازير', en: 'Pigs' },
  'animal:locust': { ar: 'الجراد', en: 'Locusts' },
  'animal:frog': { ar: 'الضفادع', en: 'Frogs' },
  'animal:lice': { ar: 'القمل', en: 'Lice' },
  // places
  'place:cave': { ar: 'الكهف', en: 'Cave' },
  'place:garden': { ar: 'الجنة الدنيوية', en: 'Earthly Garden' },
  'place:two_gardens': { ar: 'الجنتين', en: 'Two Gardens' },
  'place:makkah': { ar: 'مكة', en: 'Makkah' },
  'place:madinah': { ar: 'المدينة', en: 'Madinah' },
  'place:masjid_al_haram': { ar: 'المسجد الحرام', en: 'Masjid al-Haram' },
  'place:masjid_al_aqsa': { ar: 'المسجد الأقصى', en: 'Masjid al-Aqsa' },
  'place:mount_sinai': { ar: 'الطور', en: 'Mount Sinai' },
  'place:mount_judi': { ar: 'الجودي', en: 'Mount Judi' },
  'place:madyan': { ar: 'مدين', en: 'Madyan' },
  'place:egypt': { ar: 'مصر', en: 'Egypt' },
  'place:sheba': { ar: 'سبأ', en: 'Sheba' },
  'place:thicket': { ar: 'الأيكة', en: 'The Thicket' },
  'place:ditch': { ar: 'الأخدود', en: 'The Ditch' },
  'place:hijr': { ar: 'الحجر', en: 'Al-Hijr' },
  'place:rass': { ar: 'الرس', en: 'Ar-Rass' },
  'place:badr': { ar: 'بدر', en: 'Badr' },
  'place:uhud': { ar: 'أحد', en: 'Uhud' },
  'place:hudaybiyyah': { ar: 'الحديبية', en: 'Hudaybiyyah' },
  'place:tabuk': { ar: 'تبوك', en: 'Tabuk' },
  'place:najran': { ar: 'نجران', en: 'Najran' },
  'place:sea': { ar: 'البحر', en: 'Sea' },
  'place:well': { ar: 'البئر', en: 'Well' },
  'place:village': { ar: 'القرية', en: 'Village' },
  'place:prison': { ar: 'السجن', en: 'Prison' },
  'place:ad_lands': { ar: 'الأحقاف', en: 'Lands of Aad' },
  // objects
  'object:staff': { ar: 'العصا', en: 'Staff' },
  'object:tablets': { ar: 'الألواح', en: 'Tablets' },
  'object:ark_covenant': { ar: 'التابوت', en: 'Ark of the Covenant' },
  'object:ring': { ar: 'الخاتم', en: 'Ring (of Sulayman)' },
  'object:throne': { ar: 'العرش (بلقيس)', en: 'Throne (of Bilqis)' },
  'object:ship': { ar: 'السفينة', en: 'Ship / Ark' },
  'object:cup': { ar: 'الصواع', en: 'Cup (of Yusuf)' },
  'object:shirt_yusuf': { ar: 'قميص يوسف', en: 'Shirt of Yusuf' },
  'object:manna_salwa': { ar: 'المن والسلوى', en: 'Manna and Salwa' },
  'object:calf_gold': { ar: 'العجل الذهبي', en: 'Golden Calf' },
  'object:idols': { ar: 'الأصنام', en: 'Idols' },
  'object:mountain_lifted': { ar: 'الجبل المرفوع', en: 'Lifted Mountain' },
  'object:tree_zaqqum': { ar: 'شجرة الزقوم', en: 'Tree of Zaqqum' },
  'object:scripture': { ar: 'الكتاب', en: 'Scripture' },
  'object:hoopoe_letter': { ar: 'كتاب الهدهد', en: "Hoopoe's Letter" },
  'object:rock': { ar: 'الصخرة', en: 'Rock' },
  'object:table_spread': { ar: 'المائدة', en: 'Heavenly Table-Spread' },
  // events
  'event:creation': { ar: 'الخلق', en: 'Creation' },
  'event:fall_from_paradise': { ar: 'الهبوط من الجنة', en: 'Fall from Paradise' },
  'event:flood': { ar: 'الطوفان', en: 'The Flood' },
  'event:battle': { ar: 'معركة', en: 'Battle' },
  'event:hijrah': { ar: 'الهجرة', en: 'Hijrah' },
  'event:isra_miraj': { ar: 'الإسراء والمعراج', en: 'Isra & Miraj' },
  'event:mubahala': { ar: 'المباهلة', en: 'Mubahala' },
  'event:slander': { ar: 'الإفك', en: 'Slander (Ifk)' },
  'event:revelation': { ar: 'الوحي', en: 'Revelation' },
  'event:exodus': { ar: 'الخروج من مصر', en: 'Exodus' },
  'event:sacrifice': { ar: 'الذبح', en: 'Sacrifice' },
  'event:building_kaaba': { ar: 'بناء الكعبة', en: 'Building the Kaʿba' },
  'event:treaty': { ar: 'المعاهدة', en: 'Treaty' },
  'event:expedition': { ar: 'الغزوة', en: 'Expedition' },
  'event:qiblah_change': { ar: 'تحويل القبلة', en: 'Qiblah Change' },
  'event:conquest': { ar: 'الفتح', en: 'Conquest' },
  'event:dream': { ar: 'الرؤيا', en: 'Dream' },
  'event:judgment': { ar: 'القضاء', en: 'Judgment / Verdict' },
  'event:dialogue': { ar: 'الحوار', en: 'Dialogue' },
  'event:trial': { ar: 'الابتلاء', en: 'Trial' },
  'event:first_murder': { ar: 'أول قتل', en: 'First Murder' },
  // miracles
  'miracle:sea_parting': { ar: 'فلق البحر', en: 'Sea Parting' },
  'miracle:fire_cool': { ar: 'النار بردًا', en: 'Fire Made Cool' },
  'miracle:dead_revived': { ar: 'إحياء الموتى', en: 'Dead Revived' },
  'miracle:bird_creation': { ar: 'خلق الطير', en: 'Bird from Clay' },
  'miracle:food_from_heaven': { ar: 'طعام من السماء', en: 'Food from Heaven' },
  'miracle:water_from_rock': { ar: 'الماء من الصخرة', en: 'Water from Rock' },
  'miracle:healing_blind': { ar: 'شفاء الأكمه', en: 'Healing the Blind' },
  'miracle:healing_leper': { ar: 'شفاء الأبرص', en: 'Healing the Leper' },
  'miracle:talking_baby': { ar: 'الرضيع المتكلم', en: 'Talking Baby' },
  'miracle:transformation_monkeys': { ar: 'المسخ قردة', en: 'Transformation to Monkeys' },
  'miracle:staff_to_serpent': { ar: 'انقلاب العصا حية', en: 'Staff into Serpent' },
  'miracle:white_hand': { ar: 'اليد البيضاء', en: 'White Hand' },
  'miracle:she_camel': { ar: 'الناقة المعجزة', en: "Salih's She-Camel" },
  'miracle:elephant_birds': { ar: 'طير أبابيل', en: 'Birds of Ababil' },
  'miracle:throne_transport': { ar: 'نقل العرش', en: 'Throne Transported' },
  'miracle:fish_swallow': { ar: 'ابتلاع الحوت', en: 'Whale Swallowing' },
  'miracle:ant_speech': { ar: 'كلام النملة', en: 'Speech of the Ant' },
  'miracle:hoopoe_speech': { ar: 'كلام الهدهد', en: 'Speech of the Hoopoe' },
  'miracle:donkey_revived': { ar: 'إحياء الحمار', en: 'Donkey Revived' },
  'miracle:cave_sleep': { ar: 'نوم الكهف', en: 'Sleep of the Cave' },
  // family
  'family:husband_wife': { ar: 'الزوجان', en: 'Husband & Wife' },
  'family:parent_child': { ar: 'الوالد والولد', en: 'Parent & Child' },
  'family:brothers': { ar: 'الإخوة', en: 'Brothers' },
  'family:mother': { ar: 'الأم', en: 'Mother' },
  'family:father': { ar: 'الأب', en: 'Father' },
  'family:son': { ar: 'الابن', en: 'Son' },
  'family:daughter': { ar: 'الابنة', en: 'Daughter' },
  // roles
  'role:prophet': { ar: 'نبي', en: 'Prophet' },
  'role:messenger': { ar: 'رسول', en: 'Messenger' },
  'role:king': { ar: 'ملك', en: 'King' },
  'role:queen': { ar: 'ملكة', en: 'Queen' },
  'role:magician': { ar: 'ساحر', en: 'Magician' },
  'role:priest': { ar: 'كاهن', en: 'Priest' },
  'role:slave': { ar: 'عبد', en: 'Slave' },
  'role:slave_girl': { ar: 'الجارية', en: 'Slave Girl' },
  'role:companion': { ar: 'صحابي', en: 'Companion' },
  'role:wife_of_prophet': { ar: 'زوجة نبي', en: 'Wife of a Prophet' },
  'role:wife_of_tyrant': { ar: 'زوجة طاغية', en: 'Wife of a Tyrant' },
  'role:disbeliever': { ar: 'كافر', en: 'Disbeliever' },
  // afterlife
  'afterlife:paradise': { ar: 'الجنة', en: 'Paradise' },
  'afterlife:hell': { ar: 'النار', en: 'Hellfire' },
  'afterlife:mizan': { ar: 'الميزان', en: 'The Scale' },
  'afterlife:trumpet': { ar: 'الصور', en: 'The Trumpet' },
  'afterlife:intercession': { ar: 'الشفاعة', en: 'Intercession' },
  'afterlife:resurrection': { ar: 'البعث', en: 'Resurrection' },
  'afterlife:hour': { ar: 'الساعة', en: 'The Hour' },
  'afterlife:judgment_day': { ar: 'يوم القيامة', en: 'Day of Judgment' },
  'afterlife:araf': { ar: 'الأعراف', en: 'Al-Aʿraf' },
  'afterlife:covenant_souls': { ar: 'ميثاق الأرواح', en: "Souls' Covenant" },
  // nature
  'nature:water': { ar: 'الماء', en: 'Water' },
  'nature:fire': { ar: 'النار', en: 'Fire' },
  'nature:wind': { ar: 'الرياح', en: 'Wind' },
  'nature:rain': { ar: 'المطر', en: 'Rain' },
  'nature:mountain': { ar: 'الجبل', en: 'Mountain' },
  'nature:earthquake': { ar: 'الزلزال', en: 'Earthquake' },
  'nature:stars': { ar: 'النجوم', en: 'Stars' },
  'nature:moon': { ar: 'القمر', en: 'Moon' },
  'nature:sun': { ar: 'الشمس', en: 'Sun' },
  'nature:plant': { ar: 'النبات', en: 'Plant' },
  'nature:sky': { ar: 'السماء', en: 'Sky' },
  // virtues
  'virtue:patience': { ar: 'الصبر', en: 'Patience' },
  'virtue:repentance': { ar: 'التوبة', en: 'Repentance' },
  'virtue:gratitude': { ar: 'الشكر', en: 'Gratitude' },
  'virtue:sincerity': { ar: 'الإخلاص', en: 'Sincerity' },
  'virtue:justice': { ar: 'العدل', en: 'Justice' },
  'virtue:mercy': { ar: 'الرحمة', en: 'Mercy' },
  'virtue:humility': { ar: 'التواضع', en: 'Humility' },
  'virtue:charity': { ar: 'الصدقة', en: 'Charity' },
  'virtue:sacrifice': { ar: 'التضحية', en: 'Sacrifice' },
  'virtue:trust_in_allah': { ar: 'التوكل', en: 'Trust in Allah' },
  'virtue:knowledge': { ar: 'العلم', en: 'Knowledge' },
  'virtue:wisdom': { ar: 'الحكمة', en: 'Wisdom' },
  'virtue:chastity': { ar: 'العفة', en: 'Chastity' },
  'virtue:courage': { ar: 'الشجاعة', en: 'Courage' },
  // vices
  'vice:arrogance': { ar: 'الكبر', en: 'Arrogance' },
  'vice:disbelief': { ar: 'الكفر', en: 'Disbelief' },
  'vice:idolatry': { ar: 'الشرك', en: 'Idolatry' },
  'vice:tyranny': { ar: 'الطغيان', en: 'Tyranny' },
  'vice:jealousy': { ar: 'الحسد', en: 'Jealousy' },
  'vice:greed': { ar: 'الجشع', en: 'Greed' },
  'vice:betrayal': { ar: 'الخيانة', en: 'Betrayal' },
  'vice:slander': { ar: 'البهتان', en: 'Slander' },
  'vice:deception': { ar: 'المكر', en: 'Deception' },
  'vice:oppression': { ar: 'الظلم', en: 'Oppression' },
  'vice:hypocrisy': { ar: 'النفاق', en: 'Hypocrisy' },
  'vice:disobedience': { ar: 'العصيان', en: 'Disobedience' },
};

// ---------------------------------------------------------------------------
// People taxonomy (canonical Quranic persons)
// ---------------------------------------------------------------------------

/**
 * Coarse role buckets used to facet the People filter. A person carries
 * exactly one primary role. Prophet IDs come straight from the prophets
 * atlas so the People index is *additive* — it never re-declares a prophet
 * profile, it just lifts them into a unified people view.
 */
export type PersonRole =
  | 'prophet'
  | 'righteous_figure'
  | 'monarch'
  | 'antagonist'
  | 'companion'
  | 'family_member'
  | 'angel'
  | 'unseen_being'
  | 'collective';

export const PERSON_ROLE_ORDER: PersonRole[] = [
  'prophet',
  'righteous_figure',
  'monarch',
  'antagonist',
  'companion',
  'family_member',
  'angel',
  'unseen_being',
  'collective',
];

export const PERSON_ROLE_LABELS: Record<PersonRole, { ar: string; en: string }> = {
  prophet: { ar: 'الأنبياء', en: 'Prophets' },
  righteous_figure: { ar: 'الصالحون', en: 'Righteous figures' },
  monarch: { ar: 'الملوك والملكات', en: 'Monarchs' },
  antagonist: { ar: 'المعارضون', en: 'Antagonists' },
  companion: { ar: 'الصحابة', en: 'Companions' },
  family_member: { ar: 'أهل البيت', en: 'Family members' },
  angel: { ar: 'الملائكة', en: 'Angels' },
  unseen_being: { ar: 'كائنات الغيب', en: 'Unseen beings' },
  collective: { ar: 'مجموعات', en: 'Groups' },
};

export interface PersonIndexEntry {
  personId: string;
  nameArabic: string;
  nameEnglish: string;
  role: PersonRole;
  /**
   * Optional one-line bilingual description that the UI can show next to
   * the chip on hover. Kept brief and factual — never tafsir.
   */
  noteArabic?: string;
  noteEnglish?: string;
}

/**
 * Split a "group:tag" string into its parts. Returns null if the input is
 * not well-formed (no colon, empty halves).
 */
export function parseSubcategory(s: string): { group: SubcategoryGroup; tag: string } | null {
  const idx = s.indexOf(':');
  if (idx <= 0 || idx === s.length - 1) return null;
  const group = s.slice(0, idx) as SubcategoryGroup;
  const tag = s.slice(idx + 1);
  if (!SUBCATEGORY_GROUP_ORDER.includes(group)) return null;
  return { group, tag };
}

/**
 * Resolve a subcategory string to a bilingual label, falling back to a
 * humanised version of the tag word if no explicit label exists.
 */
export function getSubcategoryLabel(s: string): { ar: string; en: string } {
  const explicit = SUBCATEGORY_TAG_LABELS[s];
  if (explicit) return explicit;
  const parsed = parseSubcategory(s);
  if (!parsed) return { ar: s, en: s };
  const humanised = parsed.tag
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');
  return { ar: humanised, en: humanised };
}

/**
 * Maps legacy category aliases (used by the backend `stories` table and
 * older atlas builds) to registry categories so the unified registry can
 * absorb both without dropping rows.
 */
export const REGISTRY_CATEGORY_ALIASES: Record<string, RegistryStoryCategory> = {
  prophet: 'prophet',
  prophetic: 'prophet',
  prophetic_sira: 'prophetic_sirah',
  prophetic_sirah: 'prophetic_sirah',
  named_char: 'person',
  person: 'person',
  righteous: 'person',
  companions: 'person',
  battles: 'historical',
  nation: 'nation',
  parable: 'parable',
  historical: 'historical',
  unseen: 'unseen',
  compact_profile: 'compact_profile',
  mission_summary: 'prophetic_sirah',
  needs_review: 'needs_review',
};
