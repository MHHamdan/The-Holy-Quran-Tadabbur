/**
 * Canonical Quran places index.
 *
 * Provides a stable placeId for every Quranic place surfaced by the
 * story registry. Uses the existing `place:*` subcategory layer as the
 * spine — each known subcategory tag maps to one canonical placeId —
 * and adds richer structure on top (type, bilingual labels, note,
 * Quran refs).
 *
 * Used by:
 *   - scripts/build-quran-story-registry.ts to populate
 *     RegistryStoryEntry.placeIds
 *   - scripts/validate-quran-story-registry.ts to validate the IDs
 *
 * Editing rules:
 *   - placeId must be lowercase snake_case prefixed with `place_`.
 *   - subcategoryAliases lists the place:* tags from the subcategory
 *     map that should resolve to this placeId. Most placeIds have
 *     exactly one alias (place_makkah ← "place:makkah"); only split or
 *     merged tags need more.
 *   - Quran references are optional but encouraged for the named
 *     locations (Madyan, Sheba, Sinai, Iram, …).
 */

import type { PlaceIndexEntry } from '../frontend/src/types/quranStoryRegistry';

export const QURAN_PLACES_INDEX: PlaceIndexEntry[] = [
  // -------------------------------------------------------------------
  // Sanctuaries (Haram zones)
  // -------------------------------------------------------------------
  {
    placeId: 'place_masjid_al_haram',
    nameArabic: 'المسجد الحرام',
    nameEnglish: 'Masjid al-Haram',
    type: 'sanctuary',
    noteEnglish: 'The sacred mosque in Makkah surrounding the Kaʿba.',
    noteArabic: 'المسجد الحرام في مكة المكرمة.',
    quranReferences: ['2:144', '17:1'],
  },
  {
    placeId: 'place_masjid_al_aqsa',
    nameArabic: 'المسجد الأقصى',
    nameEnglish: 'Masjid al-Aqsa',
    type: 'sanctuary',
    noteEnglish: 'The farther mosque in Jerusalem, destination of the Night Journey.',
    noteArabic: 'المسجد الأقصى في القدس، مقصد الإسراء.',
    quranReferences: ['17:1'],
  },
  {
    placeId: 'place_kabah',
    nameArabic: 'الكعبة المشرفة',
    nameEnglish: 'The Kaʿba',
    type: 'sanctuary',
    noteEnglish: 'The first house established for the worship of Allah.',
    noteArabic: 'البيت العتيق الذي بناه إبراهيم وإسماعيل.',
    quranReferences: ['3:96', '5:97', '22:26'],
  },
  {
    placeId: 'place_maqam_ibrahim',
    nameArabic: 'مقام إبراهيم',
    nameEnglish: "Station of Ibrahim",
    type: 'sanctuary',
    noteEnglish: 'Site near the Kaʿba named in Surah Al-Baqara and Aal Imran.',
    noteArabic: 'موضع قدم إبراهيم بجوار الكعبة.',
    quranReferences: ['2:125', '3:97'],
  },
  {
    placeId: 'place_safa_marwa',
    nameArabic: 'الصفا والمروة',
    nameEnglish: 'As-Safa and Al-Marwa',
    type: 'sanctuary',
    noteEnglish: 'The two hills walked between during ḥajj and ʿumra.',
    noteArabic: 'الصفا والمروة من شعائر الله.',
    quranReferences: ['2:158'],
  },

  // -------------------------------------------------------------------
  // Cities & towns
  // -------------------------------------------------------------------
  {
    placeId: 'place_makkah',
    nameArabic: 'مكة المكرمة',
    nameEnglish: 'Makkah',
    type: 'city',
    noteEnglish: 'Also called Bakka; the sacred city of the Kaʿba.',
    noteArabic: 'مكة المكرمة، البلد الحرام.',
    quranReferences: ['48:24', '3:96', '90:1-2'],
  },
  {
    placeId: 'place_madinah',
    nameArabic: 'المدينة المنورة',
    nameEnglish: 'Madinah',
    type: 'city',
    noteEnglish: 'Formerly Yathrib; the city of the Prophet ﷺ after the Hijrah.',
    noteArabic: 'يثرب قبل الهجرة، مدينة الرسول ﷺ.',
    quranReferences: ['33:13', '63:8'],
  },
  {
    placeId: 'place_jerusalem',
    nameArabic: 'بيت المقدس',
    nameEnglish: 'Bayt al-Maqdis (Jerusalem)',
    type: 'city',
    noteEnglish: 'The city surrounding Masjid al-Aqsa, named in the Isra story.',
    noteArabic: 'مدينة المسجد الأقصى.',
  },
  {
    placeId: 'place_egypt',
    nameArabic: 'مصر',
    nameEnglish: 'Egypt',
    type: 'city',
    noteEnglish: 'Setting of Yusuf, Musa, and the Pharaonic stories.',
    noteArabic: 'موطن يوسف وموسى ومسرح أحداث فرعون.',
    quranReferences: ['10:87', '12:21', '12:99'],
  },
  {
    placeId: 'place_babylon',
    nameArabic: 'بابل',
    nameEnglish: 'Babylon',
    type: 'city',
    noteEnglish: 'Mentioned in Surah Al-Baqara with Harut and Marut.',
    noteArabic: 'ذُكرت في سورة البقرة مع هاروت وماروت.',
    quranReferences: ['2:102'],
  },
  {
    placeId: 'place_iram',
    nameArabic: 'إرم ذات العماد',
    nameEnglish: 'Iram of the Pillars',
    type: 'city',
    noteEnglish: 'City of the people of ʿAd named in Surah Al-Fajr.',
    noteArabic: 'مدينة عاد المذكورة في سورة الفجر.',
    quranReferences: ['89:6-8'],
  },
  {
    placeId: 'place_saba_city',
    nameArabic: 'مأرب (مدينة سبأ)',
    nameEnglish: "City of Sheba (Maʾrib)",
    type: 'city',
    noteEnglish: 'Capital of the kingdom of Sheba.',
    noteArabic: 'عاصمة مملكة سبأ في اليمن.',
  },

  // -------------------------------------------------------------------
  // Regions (broader geographic areas)
  // -------------------------------------------------------------------
  {
    placeId: 'place_madyan',
    nameArabic: 'مدين',
    nameEnglish: 'Madyan',
    type: 'region',
    noteEnglish: 'Land of Shuʿayb, between Hijaz and Sinai.',
    noteArabic: 'مساكن قوم شعيب.',
    quranReferences: ['7:85', '11:84', '28:22-23'],
  },
  {
    placeId: 'place_sheba',
    nameArabic: 'سبأ',
    nameEnglish: 'Sheba (Sabaʾ)',
    type: 'region',
    noteEnglish: 'Kingdom of Bilqis in southern Arabia.',
    noteArabic: 'مملكة بلقيس جنوب الجزيرة.',
    quranReferences: ['27:22', '34:15-16'],
  },
  {
    placeId: 'place_thicket',
    nameArabic: 'الأيكة',
    nameEnglish: 'The Thicket (al-Ayka)',
    type: 'region',
    noteEnglish: 'Dwelling-place of the People of the Thicket linked with Shuʿayb.',
    noteArabic: 'موطن أصحاب الأيكة قرب مدين.',
    quranReferences: ['15:78', '26:176', '38:13', '50:14'],
  },
  {
    placeId: 'place_ad_lands',
    nameArabic: 'الأحقاف',
    nameEnglish: 'Al-Ahqaf (Land of ʿAd)',
    type: 'region',
    noteEnglish: 'The sand-dune land of the people of ʿAd in southern Arabia.',
    noteArabic: 'موطن قوم عاد في جنوب الجزيرة.',
    quranReferences: ['46:21'],
  },
  {
    placeId: 'place_thamud_lands',
    nameArabic: 'الحجر',
    nameEnglish: 'Al-Hijr (Land of Thamud)',
    type: 'region',
    noteEnglish: 'Rocky lands of Thamud, north of Madinah.',
    noteArabic: 'منازل ثمود في شمال الحجاز.',
    quranReferences: ['15:80'],
  },
  {
    placeId: 'place_rass',
    nameArabic: 'الرس',
    nameEnglish: 'Ar-Rass',
    type: 'region',
    noteEnglish: 'Land of the People of Ar-Rass, mentioned in Surahs Al-Furqan and Qaf.',
    noteArabic: 'موطن أصحاب الرس.',
    quranReferences: ['25:38', '50:12'],
  },
  {
    placeId: 'place_najran',
    nameArabic: 'نجران',
    nameEnglish: 'Najran',
    type: 'region',
    noteEnglish: 'Home of the Christian delegation that came to mubāhala.',
    noteArabic: 'موطن وفد المباهلة المسيحي.',
  },
  {
    placeId: 'place_palestine',
    nameArabic: 'الأرض المقدسة',
    nameEnglish: 'The Holy Land',
    type: 'region',
    noteEnglish: 'The land Allah blessed; Bani Israel were commanded to enter it.',
    noteArabic: 'الأرض التي بارك الله فيها للعالمين.',
    quranReferences: ['5:21', '17:1', '21:71'],
  },
  {
    placeId: 'place_byzantium',
    nameArabic: 'بلاد الروم',
    nameEnglish: 'Land of the Romans (Byzantium)',
    type: 'region',
    noteEnglish: 'The Eastern Roman empire whose lands witnessed the events of Surah Ar-Rum.',
    noteArabic: 'بلاد الإمبراطورية البيزنطية.',
    quranReferences: ['30:1-5'],
  },
  {
    placeId: 'place_persia',
    nameArabic: 'بلاد فارس',
    nameEnglish: 'Land of the Persians (Sassanian Persia)',
    type: 'region',
    noteEnglish: 'The Sassanian Persian empire, victorious before the Romans regained ground.',
    noteArabic: 'بلاد الفرس الساسانية.',
  },

  // -------------------------------------------------------------------
  // Mountains
  // -------------------------------------------------------------------
  {
    placeId: 'place_mount_sinai',
    nameArabic: 'الطور (سيناء)',
    nameEnglish: 'Mount Sinai (At-Tur)',
    type: 'mountain',
    noteEnglish: 'Mountain where Musa received revelation and the Tablets.',
    noteArabic: 'الجبل الذي كلم الله عليه موسى.',
    quranReferences: ['19:52', '20:80', '52:1', '95:2'],
  },
  {
    placeId: 'place_mount_judi',
    nameArabic: 'الجودي',
    nameEnglish: 'Mount Judi',
    type: 'mountain',
    noteEnglish: 'The mountain on which the Ark of Nuh came to rest.',
    noteArabic: 'الجبل الذي استقرت عليه سفينة نوح.',
    quranReferences: ['11:44'],
  },
  {
    placeId: 'place_cave_hira',
    nameArabic: 'غار حراء',
    nameEnglish: 'Cave of Hiraʾ',
    type: 'mountain',
    noteEnglish: 'Cave on Jabal An-Nur where the first revelation came to the Prophet ﷺ.',
    noteArabic: 'الغار الذي نزل فيه الوحي على النبي ﷺ.',
  },

  // -------------------------------------------------------------------
  // Water bodies
  // -------------------------------------------------------------------
  {
    placeId: 'place_red_sea',
    nameArabic: 'البحر (بحر فرعون)',
    nameEnglish: "Sea (Sea of Pharaoh)",
    type: 'water_body',
    noteEnglish: 'The sea Allah split open for Musa and Bani Israel.',
    noteArabic: 'البحر الذي فلقه الله لموسى.',
    quranReferences: ['2:50', '20:77', '26:63'],
  },
  {
    placeId: 'place_two_seas',
    nameArabic: 'مجمع البحرين',
    nameEnglish: 'Junction of the Two Seas',
    type: 'water_body',
    noteEnglish: 'The meeting-point of two seas, setting of the Musa & Khidr story.',
    noteArabic: 'مجمع البحرين في قصة موسى والخضر.',
    quranReferences: ['18:60'],
  },
  {
    placeId: 'place_well_yusuf',
    nameArabic: 'بئر يوسف',
    nameEnglish: 'Well of Yusuf',
    type: 'water_body',
    noteEnglish: 'The well into which Yusuf was cast by his brothers.',
    noteArabic: 'الجب الذي ألقي فيه يوسف.',
    quranReferences: ['12:10', '12:15'],
  },
  {
    placeId: 'place_river_nile',
    nameArabic: 'النيل',
    nameEnglish: 'Nile (River of Musa)',
    type: 'water_body',
    noteEnglish: 'The river into which the mother of Musa was inspired to cast him.',
    noteArabic: 'النهر الذي ألقي فيه موسى صغيراً.',
    quranReferences: ['20:39', '28:7'],
  },
  {
    placeId: 'place_well_madyan',
    nameArabic: 'بئر مدين',
    nameEnglish: 'Well of Madyan',
    type: 'water_body',
    noteEnglish: 'The watering place where Musa met the daughters of Shuʿayb.',
    noteArabic: 'البئر التي ورد عليها موسى في مدين.',
    quranReferences: ['28:23'],
  },

  // -------------------------------------------------------------------
  // Landmarks (specific named locations and zones)
  // -------------------------------------------------------------------
  {
    placeId: 'place_cave_kahf',
    nameArabic: 'كهف أصحاب الكهف',
    nameEnglish: 'Cave of the Sleepers',
    type: 'landmark',
    noteEnglish: 'The cave that sheltered the Youth of the Cave.',
    noteArabic: 'كهف أصحاب الكهف والرقيم.',
    quranReferences: ['18:9-26'],
  },
  {
    placeId: 'place_cave_thawr',
    nameArabic: 'غار ثور',
    nameEnglish: 'Cave of Thawr',
    type: 'landmark',
    noteEnglish: 'The cave where the Prophet ﷺ and Abu Bakr hid during the Hijrah.',
    noteArabic: 'غار ثور في الهجرة النبوية.',
    quranReferences: ['9:40'],
  },
  {
    placeId: 'place_ukhdud',
    nameArabic: 'الأخدود',
    nameEnglish: 'The Ditch (Ukhdud)',
    type: 'landmark',
    noteEnglish: 'The trench in which the believers were burned, in Surah Al-Burūj.',
    noteArabic: 'الأخدود الذي حُرق فيه المؤمنون.',
    quranReferences: ['85:4-8'],
  },
  {
    placeId: 'place_garden',
    nameArabic: 'الجنة (الدنيوية)',
    nameEnglish: 'Earthly Garden',
    type: 'landmark',
    noteEnglish: 'Generic earthly garden referenced in parables.',
    noteArabic: 'جنة دنيوية في الأمثال القرآنية.',
  },
  {
    placeId: 'place_two_gardens',
    nameArabic: 'الجنتان',
    nameEnglish: 'The Two Gardens (Al-Kahf)',
    type: 'landmark',
    noteEnglish: 'The two gardens of the parable in Surah Al-Kahf.',
    noteArabic: 'جنتا الرجلين في سورة الكهف.',
    quranReferences: ['18:32-44'],
  },
  {
    placeId: 'place_garden_owners_field',
    nameArabic: 'بستان أصحاب الجنة',
    nameEnglish: 'Garden of the Owners (Al-Qalam)',
    type: 'landmark',
    noteEnglish: "The orchard parable in Surah Al-Qalam.",
    noteArabic: 'بستان أصحاب الجنة في سورة القلم.',
    quranReferences: ['68:17-33'],
  },
  {
    placeId: 'place_village_ruined',
    nameArabic: 'القرية الخاوية',
    nameEnglish: 'The Ruined Town',
    type: 'landmark',
    noteEnglish: 'The town the man passed by; he was caused to die a hundred years.',
    noteArabic: 'القرية التي مر بها الرجل.',
    quranReferences: ['2:259'],
  },
  {
    placeId: 'place_village_yasin',
    nameArabic: 'قرية أصحاب يس',
    nameEnglish: 'Town of the Three Messengers',
    type: 'landmark',
    noteEnglish: 'The town visited by the three messengers in Surah Ya-Sin.',
    noteArabic: 'القرية التي جاءها المرسلون في سورة يس.',
    quranReferences: ['36:13-29'],
  },
  {
    placeId: 'place_prison_egypt',
    nameArabic: 'سجن مصر',
    nameEnglish: 'Prison of Egypt',
    type: 'landmark',
    noteEnglish: 'The prison where Yusuf was held and interpreted dreams.',
    noteArabic: 'السجن الذي دخله يوسف وأوّل فيه الرؤى.',
    quranReferences: ['12:33-42'],
  },

  // -------------------------------------------------------------------
  // Battlefields (named expeditions / sites of Sirah events)
  // -------------------------------------------------------------------
  {
    placeId: 'place_badr',
    nameArabic: 'بدر',
    nameEnglish: 'Badr',
    type: 'battlefield',
    noteEnglish: 'Site of the first major battle of the Muslims.',
    noteArabic: 'موضع غزوة بدر الكبرى.',
    quranReferences: ['3:123'],
  },
  {
    placeId: 'place_uhud',
    nameArabic: 'أحد',
    nameEnglish: 'Uhud',
    type: 'battlefield',
    noteEnglish: 'Jabal Uhud, north of Madinah, site of the second major battle.',
    noteArabic: 'جبل أحد، شمال المدينة.',
    quranReferences: ['3:121-128'],
  },
  {
    placeId: 'place_hudaybiyyah',
    nameArabic: 'الحديبية',
    nameEnglish: 'Al-Hudaybiyyah',
    type: 'battlefield',
    noteEnglish: 'Site of the treaty between the Muslims and Quraysh.',
    noteArabic: 'موضع صلح الحديبية.',
    quranReferences: ['48:1', '48:24'],
  },
  {
    placeId: 'place_tabuk',
    nameArabic: 'تبوك',
    nameEnglish: 'Tabuk',
    type: 'battlefield',
    noteEnglish: 'Northern expedition addressed in Surah At-Tawba.',
    noteArabic: 'موضع غزوة تبوك.',
  },
  {
    placeId: 'place_hunayn',
    nameArabic: 'حنين',
    nameEnglish: 'Hunayn',
    type: 'battlefield',
    noteEnglish: 'Valley where the Muslims rallied after initial setback (Surah At-Tawba).',
    noteArabic: 'وادي حنين، ذُكر في سورة التوبة.',
    quranReferences: ['9:25-26'],
  },
  {
    placeId: 'place_khandaq',
    nameArabic: 'الخندق (المدينة)',
    nameEnglish: 'The Trench (around Madinah)',
    type: 'battlefield',
    noteEnglish: 'Defensive trench dug around Madinah in the Battle of Al-Ahzab.',
    noteArabic: 'الخندق الذي حُفر حول المدينة في غزوة الأحزاب.',
    quranReferences: ['33:9-27'],
  },

  // -------------------------------------------------------------------
  // Structures (vessels and named buildings that anchor stories)
  // -------------------------------------------------------------------
  {
    placeId: 'place_ark_nuh',
    nameArabic: 'سفينة نوح',
    nameEnglish: 'Ark of Nuh',
    type: 'structure',
    noteEnglish: 'The ship Nuh built by revelation, riding out the Flood.',
    noteArabic: 'سفينة نوح التي بناها بأمر الله.',
    quranReferences: ['11:37-38', '23:27'],
  },
  {
    placeId: 'place_palace_sulayman',
    nameArabic: 'صرح سليمان',
    nameEnglish: 'Palace of Sulayman',
    type: 'structure',
    noteEnglish: 'The glass-paved court where Bilqis met Sulayman.',
    noteArabic: 'الصرح الممرد من قوارير في قصة بلقيس.',
    quranReferences: ['27:44'],
  },
  {
    placeId: 'place_palace_firawn',
    nameArabic: 'قصر فرعون',
    nameEnglish: "Palace of Fir'awn",
    type: 'structure',
    noteEnglish: "Pharaoh's court — setting of confrontations with Musa.",
    noteArabic: 'قصر فرعون ومسرح مواجهات موسى.',
  },
  {
    placeId: 'place_saba_dam',
    nameArabic: 'سد مأرب (سد سبأ)',
    nameEnglish: 'Dam of Maʾrib (Sheba)',
    type: 'structure',
    noteEnglish: 'The dam whose collapse caused the Flood of al-ʿArim.',
    noteArabic: 'السد الذي أرسل عليه سيل العرم.',
    quranReferences: ['34:16'],
  },
  {
    placeId: 'place_dhulqarnayn_barrier',
    nameArabic: 'سد ذي القرنين',
    nameEnglish: 'Barrier of Dhul-Qarnayn',
    type: 'structure',
    noteEnglish: 'The iron-and-copper barrier built against Yaʾjuj wa Maʾjuj.',
    noteArabic: 'السد الذي بناه ذو القرنين دون يأجوج ومأجوج.',
    quranReferences: ['18:94-97'],
  },

  // -------------------------------------------------------------------
  // Otherworldly (kept here for completeness — UI may dedupe with the
  // existing afterlife: subcategories)
  // -------------------------------------------------------------------
  {
    placeId: 'place_paradise',
    nameArabic: 'الجنة',
    nameEnglish: 'Paradise (Jannah)',
    type: 'otherworldly',
    noteEnglish: 'The everlasting garden promised to the believers.',
    noteArabic: 'دار النعيم للمؤمنين.',
  },
  {
    placeId: 'place_hell',
    nameArabic: 'النار (جهنم)',
    nameEnglish: 'Hellfire (Jahannam)',
    type: 'otherworldly',
    noteEnglish: 'The abode of those who rejected faith.',
    noteArabic: 'دار العذاب للكافرين.',
  },
  {
    placeId: 'place_araf',
    nameArabic: 'الأعراف',
    nameEnglish: 'Al-Aʿraf (The Heights)',
    type: 'otherworldly',
    noteEnglish: 'The heights between Paradise and Hell.',
    noteArabic: 'سور بين الجنة والنار.',
    quranReferences: ['7:46-49'],
  },
  {
    placeId: 'place_sidrat_muntaha',
    nameArabic: 'سدرة المنتهى',
    nameEnglish: 'Sidrat al-Muntaha',
    type: 'otherworldly',
    noteEnglish: 'The Lote-Tree of the Furthest Limit, seen at the Miʿraj.',
    noteArabic: 'سدرة المنتهى التي رآها النبي ﷺ ليلة المعراج.',
    quranReferences: ['53:14'],
  },
];

/**
 * Map every `place:*` subcategory tag that appears in
 * scripts/storySubcategoryMap.ts to a canonical placeId. Subcategory
 * tags that are intentionally generic (e.g. "place:village") map to a
 * representative landmark; storyId-specific extras live in
 * STORY_EXTRA_PLACES.
 */
export const SUBCATEGORY_TO_PLACE: Record<string, string[]> = {
  'place:masjid_al_haram': ['place_masjid_al_haram', 'place_kabah'],
  'place:masjid_al_aqsa': ['place_masjid_al_aqsa', 'place_jerusalem'],
  'place:makkah': ['place_makkah'],
  'place:madinah': ['place_madinah'],
  'place:egypt': ['place_egypt'],
  'place:sheba': ['place_sheba', 'place_saba_city'],
  'place:madyan': ['place_madyan'],
  'place:thicket': ['place_thicket'],
  'place:ad_lands': ['place_ad_lands'],
  'place:hijr': ['place_thamud_lands'],
  'place:rass': ['place_rass'],
  'place:najran': ['place_najran'],
  'place:mount_sinai': ['place_mount_sinai'],
  'place:mount_judi': ['place_mount_judi'],
  'place:cave': ['place_cave_kahf'],
  'place:ditch': ['place_ukhdud'],
  'place:garden': ['place_garden'],
  'place:two_gardens': ['place_two_gardens'],
  'place:village': ['place_village_ruined'],
  'place:prison': ['place_prison_egypt'],
  'place:well': ['place_well_yusuf'],
  'place:sea': ['place_red_sea'],
  'place:badr': ['place_badr'],
  'place:uhud': ['place_uhud'],
  'place:hudaybiyyah': ['place_hudaybiyyah'],
  'place:tabuk': ['place_tabuk'],
};

/**
 * Per-story extras: places that the subcategory tags alone don't cover.
 * Build script unions these with subcategory-resolved IDs.
 */
export const STORY_EXTRA_PLACES: Record<string, string[]> = {
  story_adam: ['place_paradise'],
  story_iblis_refusal: ['place_paradise'],
  story_angels_prostration: ['place_paradise'],
  story_fall_from_paradise: ['place_paradise'],
  story_paradise: ['place_paradise'],
  story_hell: ['place_hell'],
  story_tree_cursed: ['place_hell'],
  story_araf_people: ['place_araf'],
  story_isra_miraj: [
    'place_masjid_al_haram',
    'place_masjid_al_aqsa',
    'place_jerusalem',
    'place_sidrat_muntaha',
  ],
  story_hijrah: ['place_makkah', 'place_madinah', 'place_cave_thawr'],
  story_muhammad: ['place_makkah', 'place_madinah', 'place_cave_hira'],
  story_ibrahim: ['place_makkah', 'place_kabah', 'place_maqam_ibrahim', 'place_palestine', 'place_babylon'],
  story_ibrahim_nimrod: ['place_babylon'],
  story_ismail: ['place_makkah', 'place_kabah', 'place_maqam_ibrahim', 'place_safa_marwa'],
  story_yusuf: ['place_egypt', 'place_well_yusuf', 'place_prison_egypt'],
  story_yusuf_prison: ['place_prison_egypt'],
  story_yusuf_brothers: ['place_egypt', 'place_well_yusuf'],
  story_yusuf_dream: ['place_egypt'],
  story_zulaykha: ['place_egypt'],
  story_musa: ['place_egypt', 'place_red_sea', 'place_mount_sinai', 'place_madyan', 'place_river_nile'],
  story_musa_midian: ['place_madyan', 'place_well_madyan'],
  story_musa_mountain: ['place_mount_sinai'],
  story_musa_burning_bush: ['place_mount_sinai'],
  story_musa_firaun_dialogue: ['place_egypt', 'place_palace_firawn'],
  story_magicians: ['place_egypt', 'place_palace_firawn'],
  story_sea_crossing: ['place_red_sea', 'place_egypt'],
  story_haman: ['place_egypt'],
  story_qarun: ['place_egypt'],
  story_samiri: ['place_mount_sinai'],
  story_golden_calf: ['place_mount_sinai'],
  story_asiya: ['place_egypt', 'place_palace_firawn'],
  story_mother_musa: ['place_egypt', 'place_river_nile'],
  story_believer_firaun: ['place_egypt', 'place_palace_firawn'],
  story_ancient_egypt: ['place_egypt', 'place_river_nile'],
  story_bani_israel: ['place_egypt', 'place_palestine', 'place_mount_sinai'],
  story_bilqis: ['place_sheba', 'place_saba_city', 'place_palace_sulayman'],
  story_sulayman: ['place_sheba', 'place_palace_sulayman', 'place_jerusalem'],
  story_dhulqarnayn: ['place_dhulqarnayn_barrier'],
  story_yajuj_majuj: ['place_dhulqarnayn_barrier'],
  story_saba: ['place_sheba', 'place_saba_city', 'place_saba_dam'],
  story_thamud: ['place_thamud_lands'],
  story_ad: ['place_ad_lands', 'place_iram'],
  story_hud: ['place_ad_lands', 'place_iram'],
  story_salih: ['place_thamud_lands'],
  story_lut: ['place_palestine'],
  story_shuayb: ['place_madyan', 'place_thicket'],
  story_madyan: ['place_madyan', 'place_thicket'],
  story_kahf: ['place_cave_kahf'],
  story_seven_sleepers_dog: ['place_cave_kahf'],
  story_sleepers_numbers: ['place_cave_kahf'],
  story_khidr: ['place_two_seas'],
  story_ditch: ['place_ukhdud'],
  story_three_messengers: ['place_village_yasin'],
  story_garden_owners: ['place_garden_owners_field'],
  story_two_gardens: ['place_two_gardens'],
  story_two_men: ['place_two_gardens'],
  story_empty_village: ['place_village_ruined'],
  story_village_fish: ['place_red_sea'],
  story_sabbath_breakers: ['place_red_sea'],
  story_nuh: ['place_ark_nuh', 'place_mount_judi'],
  story_son_nuh: ['place_ark_nuh', 'place_mount_judi'],
  story_nuh_people: ['place_ark_nuh'],
  story_elephant: ['place_makkah', 'place_kabah', 'place_masjid_al_haram'],
  story_qiblah_change: ['place_makkah', 'place_madinah', 'place_kabah'],
  story_najran: ['place_najran', 'place_madinah'],
  story_badr: ['place_badr', 'place_madinah'],
  story_uhud: ['place_uhud', 'place_madinah'],
  story_hudaybiyyah: ['place_hudaybiyyah', 'place_makkah'],
  story_conquest_makkah: ['place_makkah', 'place_kabah'],
  story_tabuk: ['place_tabuk', 'place_madinah'],
  story_ifk: ['place_madinah'],
  story_abu_lahab: ['place_makkah'],
  story_abasa: ['place_madinah'],
  story_maryam: ['place_masjid_al_aqsa', 'place_jerusalem'],
  story_maryam_birth: ['place_masjid_al_aqsa', 'place_jerusalem'],
  story_isa: ['place_palestine', 'place_jerusalem'],
  story_isa_miracles: ['place_palestine', 'place_jerusalem'],
  story_isa_ascension: ['place_palestine'],
  story_zakariyya_yahya: ['place_masjid_al_aqsa'],
  story_harut_marut: ['place_babylon'],
  // Sirah-page entries
  storypage_muhammad: ['place_makkah', 'place_madinah', 'place_cave_hira'],
  storypage_ismail: ['place_makkah', 'place_kabah'],
  storypage_sulayman: ['place_jerusalem', 'place_sheba', 'place_palace_sulayman'],
  storypage_yaqub: ['place_palestine'],
  storypage_ishaq: ['place_palestine'],
  storypage_harun: ['place_egypt', 'place_mount_sinai'],
  story_khandaq: ['place_madinah', 'place_khandaq'],
  story_romans_persians: ['place_byzantium', 'place_persia', 'place_jerusalem'],
  story_conquest_makkah: ['place_makkah', 'place_kabah', 'place_hunayn'],
};
