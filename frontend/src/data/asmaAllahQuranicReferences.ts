/**
 * Curated primary Quranic-verse references for the 99 Names of Allah.
 *
 * Source: Jāmiʿ al-Tirmidhī 3507 (the widely-taught Tirmidhi 99-Names list)
 *         cross-checked against the canonical Quran text via Quran.com and
 *         the Wikipedia "Names of God in Islam" article (which compiles the
 *         Tirmidhi-list verse references). See `sourceRegistry.ts` →
 *         `tirmidhi_asma_husna_list`.
 *
 * What this is:
 *   For each of the 99 traditional Names, a small list of *primary* Quranic
 *   verses that scholars cite as the canonical evidence for that Name. These
 *   references complement (they do NOT replace) the corpus-scan occurrences
 *   counted by `scripts/build-asma-allah-atlas.ts` — many Names appear in
 *   the Quran by concept (e.g. الخافض / الباعث) but only the cited verses
 *   are the traditional reference points.
 *
 * What this is NOT:
 *   - Not the Quran text. Only surah/ayah numbers are stored here; the
 *     actual Arabic ayah lives only in `data/raw/quran_uthmani.json`.
 *   - Not tafsir. No meaning, translation, or commentary is recorded here.
 *   - Not a count of lemma occurrences — that comes from the corpus scan.
 *
 * Display contract:
 *   All entries default to `needs_review: true`. The Atlas builder attaches
 *   sourceIds = ['tirmidhi_asma_husna_list'] and `reviewStatus: 'needs_review'`
 *   to every reference. A human reviewer must promote them before display
 *   as "verified".
 */

export interface AsmaQuranicReference {
  surahNumber: number;
  ayahNumber: number;
  /** Optional note kept short — never tafsir. */
  note?: string;
}

export interface AsmaNamePrimaryReferences {
  nameId: string;
  primaryReferences: AsmaQuranicReference[];
}

// Helper to keep the list dense and free of repetition. The lemma is matched
// by nameId; primary verses are surah:ayah pairs from the Tirmidhi tradition.
const ref = (s: number, a: number, note?: string): AsmaQuranicReference =>
  note ? { surahNumber: s, ayahNumber: a, note } : { surahNumber: s, ayahNumber: a };

// === The 99 Names of Allah — primary Quranic references ===
// Order matches the Tirmidhi narration. The Divine Name "Allah" (اسم الجلالة)
// is intentionally NOT listed here — it has thousands of occurrences and is
// covered by the separate `divineNameAllah` panel.
export const ASMA_ALLAH_PRIMARY_REFERENCES: AsmaNamePrimaryReferences[] = [
  { nameId: 'ar_rahman',          primaryReferences: [ref(1, 3), ref(55, 1), ref(17, 110)] },
  { nameId: 'ar_raheem',          primaryReferences: [ref(1, 3), ref(2, 163)] },
  { nameId: 'al_malik',           primaryReferences: [ref(20, 114), ref(23, 116), ref(59, 23), ref(62, 1)] },
  { nameId: 'al_quddus',          primaryReferences: [ref(59, 23), ref(62, 1)] },
  { nameId: 'as_salam',           primaryReferences: [ref(59, 23)] },
  { nameId: 'al_mumin',           primaryReferences: [ref(59, 23)] },
  { nameId: 'al_muhaymin',        primaryReferences: [ref(59, 23)] },
  { nameId: 'al_aziz',            primaryReferences: [ref(4, 158), ref(9, 40), ref(48, 7), ref(59, 23)] },
  { nameId: 'al_jabbar',          primaryReferences: [ref(59, 23)] },
  { nameId: 'al_mutakabbir',      primaryReferences: [ref(59, 23)] },
  { nameId: 'al_khaliq',          primaryReferences: [ref(6, 102), ref(13, 16), ref(36, 81), ref(40, 62), ref(59, 24)] },
  { nameId: 'al_bari',            primaryReferences: [ref(59, 24)] },
  { nameId: 'al_musawwir',        primaryReferences: [ref(59, 24)] },
  { nameId: 'al_ghaffar',         primaryReferences: [ref(20, 82), ref(38, 66), ref(39, 5), ref(40, 42), ref(71, 10)] },
  { nameId: 'al_qahhar',          primaryReferences: [ref(12, 39), ref(13, 16), ref(14, 48), ref(38, 65), ref(39, 4), ref(40, 16)] },
  { nameId: 'al_wahhab',          primaryReferences: [ref(3, 8), ref(38, 9), ref(38, 35)] },
  { nameId: 'ar_razzaq',          primaryReferences: [ref(51, 58)] },
  { nameId: 'al_fattah',          primaryReferences: [ref(34, 26)] },
  { nameId: 'al_alim',            primaryReferences: [ref(2, 158), ref(3, 92), ref(4, 35), ref(24, 41), ref(33, 40)] },
  { nameId: 'al_qabid',           primaryReferences: [ref(2, 245, 'concept; the lemma "القابض" is not in the Quran — hadith tradition.')] },
  { nameId: 'al_basit',           primaryReferences: [ref(2, 245, 'concept; the lemma "الباسط" is not in the Quran — hadith tradition.')] },
  { nameId: 'al_khafid',          primaryReferences: [ref(56, 3, 'concept; the lemma "الخافض" is not in the Quran — hadith tradition.')] },
  { nameId: 'ar_rafi',            primaryReferences: [ref(6, 83), ref(58, 11)] },
  { nameId: 'al_muizz',           primaryReferences: [ref(3, 26, 'concept; the lemma "المعز" is not in the Quran — hadith tradition.')] },
  { nameId: 'al_mudhill',         primaryReferences: [ref(3, 26, 'concept; the lemma "المذل" is not in the Quran — hadith tradition.')] },
  { nameId: 'as_sami',            primaryReferences: [ref(2, 127), ref(2, 256), ref(8, 17), ref(49, 1)] },
  { nameId: 'al_basir',           primaryReferences: [ref(4, 58), ref(17, 1), ref(42, 11), ref(42, 27)] },
  { nameId: 'al_hakam',           primaryReferences: [ref(22, 69)] },
  { nameId: 'al_adl',             primaryReferences: [ref(6, 115, 'concept of justice; not a frequent lemma form.')] },
  { nameId: 'al_latif',           primaryReferences: [ref(22, 63), ref(31, 16), ref(33, 34), ref(67, 14)] },
  { nameId: 'al_khabir',          primaryReferences: [ref(6, 18), ref(17, 30), ref(49, 13), ref(59, 18)] },
  { nameId: 'al_halim',           primaryReferences: [ref(2, 235), ref(17, 44), ref(22, 59), ref(35, 41)] },
  { nameId: 'al_azim',            primaryReferences: [ref(2, 255), ref(42, 4), ref(56, 96)] },
  { nameId: 'al_ghafur',          primaryReferences: [ref(2, 173), ref(8, 69), ref(16, 110), ref(41, 32)] },
  { nameId: 'ash_shakur',         primaryReferences: [ref(35, 30), ref(35, 34), ref(42, 23), ref(64, 17)] },
  { nameId: 'al_aliyy',           primaryReferences: [ref(2, 255), ref(4, 34), ref(31, 30), ref(42, 4)] },
  { nameId: 'al_kabir',           primaryReferences: [ref(13, 9), ref(22, 62), ref(31, 30), ref(34, 23)] },
  { nameId: 'al_hafiz',           primaryReferences: [ref(11, 57), ref(34, 21), ref(42, 6)] },
  { nameId: 'al_muqit',           primaryReferences: [ref(4, 85)] },
  { nameId: 'al_hasib',           primaryReferences: [ref(4, 6), ref(4, 86), ref(33, 39)] },
  { nameId: 'al_jalil',           primaryReferences: [ref(55, 27), ref(55, 78, 'appears within "ذو الجلال والإكرام".')] },
  { nameId: 'al_karim',           primaryReferences: [ref(27, 40), ref(82, 6)] },
  { nameId: 'ar_raqib',           primaryReferences: [ref(4, 1), ref(5, 117), ref(33, 52)] },
  { nameId: 'al_mujib',           primaryReferences: [ref(11, 61)] },
  { nameId: 'al_wasi',            primaryReferences: [ref(2, 247), ref(2, 268), ref(3, 73), ref(5, 54)] },
  { nameId: 'al_hakim',           primaryReferences: [ref(2, 32), ref(2, 129), ref(31, 27)] },
  { nameId: 'al_wadud',           primaryReferences: [ref(11, 90), ref(85, 14)] },
  { nameId: 'al_majid_glorious',  primaryReferences: [ref(11, 73), ref(85, 15)] },
  { nameId: 'al_baith',           primaryReferences: [ref(22, 7, 'concept of resurrection; the lemma "الباعث" is not in the Quran as a divine-name.')] },
  { nameId: 'ash_shahid',         primaryReferences: [ref(4, 166), ref(22, 17), ref(41, 53), ref(48, 28)] },
  { nameId: 'al_haqq',            primaryReferences: [ref(6, 62), ref(22, 6), ref(23, 116), ref(24, 25)] },
  { nameId: 'al_wakil',           primaryReferences: [ref(3, 173), ref(4, 171), ref(28, 28), ref(73, 9)] },
  { nameId: 'al_qawiyy',          primaryReferences: [ref(22, 40), ref(22, 74), ref(42, 19), ref(57, 25)] },
  { nameId: 'al_matin',           primaryReferences: [ref(51, 58)] },
  { nameId: 'al_waliyy',          primaryReferences: [ref(4, 45), ref(7, 196), ref(42, 28), ref(45, 19)] },
  { nameId: 'al_hamid',           primaryReferences: [ref(14, 8), ref(31, 12), ref(31, 26), ref(41, 42)] },
  { nameId: 'al_muhsi',           primaryReferences: [ref(72, 28, 'concept of counting; the lemma "المحصي" is not in the Quran — hadith tradition.'), ref(78, 29, 'concept of counting; the lemma "المحصي" is not in the Quran — hadith tradition.')] },
  { nameId: 'al_mubdi',           primaryReferences: [ref(10, 34), ref(27, 64), ref(29, 19), ref(85, 13)] },
  { nameId: 'al_muid',            primaryReferences: [ref(10, 34), ref(27, 64), ref(29, 19), ref(85, 13)] },
  { nameId: 'al_muhyi',           primaryReferences: [ref(7, 158), ref(15, 23), ref(30, 50), ref(57, 2)] },
  { nameId: 'al_mumit',           primaryReferences: [ref(3, 156), ref(7, 158), ref(15, 23), ref(57, 2)] },
  { nameId: 'al_hayy',            primaryReferences: [ref(2, 255), ref(3, 2), ref(20, 111), ref(25, 58), ref(40, 65)] },
  { nameId: 'al_qayyum',          primaryReferences: [ref(2, 255), ref(3, 2), ref(20, 111)] },
  { nameId: 'al_wajid',           primaryReferences: [ref(38, 44, 'concept of finding; the lemma "الواجد" is not in the Quran — hadith tradition.')] },
  { nameId: 'al_majid_noble',     primaryReferences: [ref(11, 73), ref(85, 15)] },
  { nameId: 'al_wahid',           primaryReferences: [ref(13, 16), ref(14, 48), ref(38, 65), ref(39, 4)] },
  { nameId: 'al_ahad',            primaryReferences: [ref(112, 1)] },
  { nameId: 'as_samad',           primaryReferences: [ref(112, 2)] },
  { nameId: 'al_qadir',           primaryReferences: [ref(6, 65), ref(46, 33), ref(75, 40)] },
  { nameId: 'al_muqtadir',        primaryReferences: [ref(18, 45), ref(54, 42), ref(54, 55)] },
  { nameId: 'al_muqaddim',        primaryReferences: [ref(16, 61, 'concept of advancing; the lemma "المقدم" is not in the Quran as a divine name — hadith tradition.')] },
  { nameId: 'al_muakhkhir',       primaryReferences: [ref(71, 4, 'concept of delaying; the lemma "المؤخر" is not in the Quran as a divine name — hadith tradition.')] },
  { nameId: 'al_awwal',           primaryReferences: [ref(57, 3)] },
  { nameId: 'al_akhir',           primaryReferences: [ref(57, 3)] },
  { nameId: 'az_zahir',           primaryReferences: [ref(57, 3)] },
  { nameId: 'al_batin',           primaryReferences: [ref(57, 3)] },
  { nameId: 'al_wali',            primaryReferences: [ref(13, 11)] },
  { nameId: 'al_mutaali',         primaryReferences: [ref(13, 9)] },
  { nameId: 'al_barr',            primaryReferences: [ref(52, 28)] },
  { nameId: 'at_tawwab',          primaryReferences: [ref(2, 128), ref(4, 64), ref(49, 12), ref(110, 3)] },
  { nameId: 'al_muntaqim',        primaryReferences: [ref(32, 22), ref(43, 41), ref(44, 16)] },
  { nameId: 'al_afuww',           primaryReferences: [ref(4, 43), ref(4, 99), ref(4, 149), ref(22, 60), ref(58, 2)] },
  { nameId: 'ar_rauf',            primaryReferences: [ref(9, 117), ref(57, 9), ref(59, 10)] },
  { nameId: 'malik_al_mulk',      primaryReferences: [ref(3, 26)] },
  { nameId: 'dhul_jalali_wal_ikram', primaryReferences: [ref(55, 27), ref(55, 78)] },
  { nameId: 'al_muqsit',          primaryReferences: [ref(3, 18), ref(5, 42), ref(57, 25)] },
  { nameId: 'al_jami',            primaryReferences: [ref(3, 9)] },
  { nameId: 'al_ghaniyy',         primaryReferences: [ref(39, 7), ref(47, 38), ref(57, 24)] },
  { nameId: 'al_mughni',          primaryReferences: [ref(9, 28, 'concept of enriching; the lemma "المغني" is not in the Quran as a divine-name form.')] },
  { nameId: 'al_mani',            primaryReferences: [ref(33, 17, 'concept of preventing; the lemma "المانع" is not in the Quran — hadith tradition.')] },
  { nameId: 'ad_darr',            primaryReferences: [ref(6, 17), ref(58, 10)] },
  { nameId: 'an_nafi',            primaryReferences: [ref(30, 37)] },
  { nameId: 'an_nur',             primaryReferences: [ref(24, 35)] },
  { nameId: 'al_hadi',            primaryReferences: [ref(22, 54), ref(25, 31)] },
  { nameId: 'al_badi',            primaryReferences: [ref(2, 117), ref(6, 101)] },
  { nameId: 'al_baqi',            primaryReferences: [ref(55, 27, 'concept; appears in the phrase "ويبقى وجه ربك".')] },
  { nameId: 'al_warith',          primaryReferences: [ref(15, 23), ref(57, 10)] },
  { nameId: 'ar_rashid',          primaryReferences: [ref(18, 10, 'concept of rightly-guiding; the lemma "الرشيد" appears in 11:87 as character-noun.')] },
  { nameId: 'as_sabur',           primaryReferences: [ref(2, 153), ref(3, 200), ref(103, 3, 'concept of patience; the lemma "الصبور" is not in the Quran as a divine name.')] },
];

export function getPrimaryReferences(nameId: string): AsmaQuranicReference[] {
  return ASMA_ALLAH_PRIMARY_REFERENCES.find((e) => e.nameId === nameId)?.primaryReferences ?? [];
}
