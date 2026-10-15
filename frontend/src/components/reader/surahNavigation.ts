/**
 * Structural navigation metadata for the readers (no Qur'an text).
 *
 * SURAH_FIRST_PAGE and SURAH_FIRST_JUZ are the `page` and `jozz` fields of
 * each surah's first ayah, and JUZ_FIRST_PAGE the `page` of each juz's first
 * ayah, in the canonical data/raw/quran_tanzil.json
 * (604-page Madinah layout, the numbering /quran/page/:n uses).
 * backend/tests/test_reader_navigation_index.py checks them against that file.
 */

// Index 0 = Surah 1
export const SURAH_FIRST_PAGE: readonly number[] = [
  1, 2, 50, 77, 106, 128, 151, 177, 187, 208, 221, 235, 249, 255, 262, 267, 282, 293, 305, 312,
  322, 332, 342, 350, 359, 367, 377, 385, 396, 404, 411, 415, 418, 428, 434, 440, 446, 453, 458, 467,
  477, 483, 489, 496, 499, 502, 507, 511, 515, 518, 520, 523, 526, 528, 531, 534, 537, 542, 545, 549,
  551, 553, 554, 556, 558, 560, 562, 564, 566, 568, 570, 572, 574, 575, 577, 578, 580, 582, 583, 585,
  586, 587, 587, 589, 590, 591, 591, 592, 593, 594, 595, 595, 596, 596, 597, 597, 598, 598, 599, 599,
  600, 600, 601, 601, 601, 602, 602, 602, 603, 603, 603, 604, 604, 604,
];

// Index 0 = Surah 1
export const SURAH_FIRST_JUZ: readonly number[] = [
  1, 1, 3, 4, 6, 7, 8, 9, 10, 11, 11, 12, 13, 13, 14, 14, 15, 15, 16, 16,
  17, 17, 18, 18, 18, 19, 19, 20, 20, 21, 21, 21, 21, 22, 22, 22, 23, 23, 23, 24,
  24, 25, 25, 25, 25, 26, 26, 26, 26, 26, 26, 27, 27, 27, 27, 27, 27, 28, 28, 28,
  28, 28, 28, 28, 28, 28, 29, 29, 29, 29, 29, 29, 29, 29, 29, 29, 29, 30, 30, 30,
  30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30,
  30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30,
];

// Index 0 = Juz 1: page of each juz's first ayah.
export const JUZ_FIRST_PAGE: readonly number[] = [
  1, 22, 42, 62, 82, 102, 121, 142, 162, 182,
  201, 222, 242, 262, 282, 302, 322, 342, 362, 382,
  402, 422, 442, 462, 482, 502, 522, 542, 562, 582,
];

export const firstPageOfSurah = (surah: number): number => SURAH_FIRST_PAGE[surah - 1] ?? 1;
export const firstPageOfJuz = (juz: number): number => JUZ_FIRST_PAGE[juz - 1] ?? 1;

export const TOTAL_SURAHS = 114;
export const TOTAL_MUSHAF_PAGES = 604;

/** The last surah starting on or before this page (selected value of the mushaf surah select). */
export function surahOnPage(page: number): number {
  let surah = 1;
  for (let i = 0; i < SURAH_FIRST_PAGE.length; i++) {
    if (SURAH_FIRST_PAGE[i] <= page) surah = i + 1;
    else break;
  }
  return surah;
}

// Curated Makki/Madani classification — scholarly consensus (Al-Suyuti).
// This is structural UI metadata, not Quran text.
export type RevelationType = 'makki' | 'madani' | 'unknown';

export const SURAH_REVELATION: Readonly<Record<number, RevelationType>> = {
  1:'makki',2:'madani',3:'madani',4:'madani',5:'madani',6:'makki',7:'makki',
  8:'madani',9:'madani',10:'makki',11:'makki',12:'makki',13:'unknown',14:'makki',
  15:'makki',16:'makki',17:'makki',18:'makki',19:'makki',20:'makki',21:'makki',
  22:'unknown',23:'makki',24:'madani',25:'makki',26:'makki',27:'makki',28:'makki',
  29:'unknown',30:'makki',31:'makki',32:'makki',33:'madani',34:'makki',35:'makki',
  36:'makki',37:'makki',38:'makki',39:'makki',40:'makki',41:'makki',42:'makki',
  43:'makki',44:'makki',45:'makki',46:'makki',47:'madani',48:'madani',49:'madani',
  50:'makki',51:'makki',52:'makki',53:'makki',54:'makki',55:'unknown',56:'makki',
  57:'madani',58:'madani',59:'madani',60:'madani',61:'madani',62:'madani',63:'madani',
  64:'madani',65:'madani',66:'madani',67:'makki',68:'makki',69:'makki',70:'makki',
  71:'makki',72:'makki',73:'makki',74:'makki',75:'makki',76:'unknown',77:'makki',
  78:'makki',79:'makki',80:'makki',81:'makki',82:'makki',83:'makki',84:'makki',
  85:'makki',86:'makki',87:'makki',88:'makki',89:'makki',90:'makki',91:'makki',
  92:'makki',93:'makki',94:'makki',95:'makki',96:'makki',97:'unknown',98:'madani',
  99:'unknown',100:'makki',101:'makki',102:'makki',103:'makki',104:'makki',105:'makki',
  106:'makki',107:'makki',108:'makki',109:'makki',110:'madani',111:'makki',112:'makki',
  113:'makki',114:'makki',
};
