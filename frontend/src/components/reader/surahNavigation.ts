/**
 * Structural navigation metadata for the readers (no Qur'an text).
 *
 * SURAH_FIRST_PAGE and SURAH_FIRST_JUZ are the `page` and `jozz` fields of
 * each surah's first ayah in the canonical data/raw/quran_tanzil.json
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

export const firstPageOfSurah = (surah: number): number => SURAH_FIRST_PAGE[surah - 1] ?? 1;

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
