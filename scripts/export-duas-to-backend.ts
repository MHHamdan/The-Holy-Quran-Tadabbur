/**
 * Export the Quranic Duʿā catalogue for the backend API.
 *
 * Generates backend/app/data/duas.json from frontend/src/data/quranicDuas.ts,
 * which is the single curated source of truth for the dataset.
 *
 * Why this exists:
 *   backend/app/api/routes/duas.py used to carry its own hand-copied Python
 *   list of the same catalogue, "kept in sync manually". It drifted to 21 of
 *   66 entries, and it duplicated Quranic Arabic as string literals in code,
 *   which the content policy forbids. Generating the file removes both
 *   problems: the API now serves whatever the curated dataset holds.
 *
 * Safety rules:
 * - No content is authored here; fields are copied verbatim from the dataset
 * - Only the fields the API actually serves are exported
 * - Entries are emitted in Quran order (surah, then ayah)
 *
 * Usage:
 *   npx tsx scripts/export-duas-to-backend.ts
 */

import { writeFileSync, mkdirSync, existsSync } from 'fs';
import { resolve, join, dirname } from 'path';

import { QURANIC_DUAS } from '../frontend/src/data/quranicDuas';

const ROOT = resolve(__dirname, '..');
const OUTPUT_JSON = join(ROOT, 'backend/app/data/duas.json');

/** Exactly the fields backend DuaOut serves — nothing more. */
interface ExportedDua {
  id: string;
  surah: number;
  ayah: number;
  ayahEnd: number | null;
  category: string;
  prophet: string | null;
  titleEn: string;
  titleAr: string;
  surahNameEn: string;
  surahNameAr: string;
  meaningEn: string;
  meaningAr: string;
  occasions: string[];
  tags: string[];
}

function main(): void {
  const errors: string[] = [];
  const seen = new Set<string>();

  const exported: ExportedDua[] = QURANIC_DUAS.map((dua) => {
    if (seen.has(dua.id)) errors.push(`Duplicate dua id: ${dua.id}`);
    seen.add(dua.id);

    if (!Number.isInteger(dua.surah) || dua.surah < 1 || dua.surah > 114) {
      errors.push(`${dua.id}: surah out of range (${dua.surah})`);
    }
    if (!Number.isInteger(dua.ayah) || dua.ayah < 1) {
      errors.push(`${dua.id}: ayah out of range (${dua.ayah})`);
    }
    if (dua.ayahEnd != null && dua.ayahEnd < dua.ayah) {
      errors.push(`${dua.id}: ayahEnd ${dua.ayahEnd} precedes ayah ${dua.ayah}`);
    }

    return {
      id: dua.id,
      surah: dua.surah,
      ayah: dua.ayah,
      ayahEnd: dua.ayahEnd ?? null,
      category: dua.category,
      prophet: dua.prophet ?? null,
      titleEn: dua.titleEn,
      titleAr: dua.titleAr,
      surahNameEn: dua.surahNameEn,
      surahNameAr: dua.surahNameAr,
      meaningEn: dua.meaningEn,
      meaningAr: dua.meaningAr,
      occasions: [...dua.occasions],
      tags: [...dua.tags],
    };
  });

  if (errors.length > 0) {
    console.error('Export aborted — dataset problems:');
    for (const error of errors) console.error(`  - ${error}`);
    process.exit(1);
  }

  exported.sort((a, b) => a.surah - b.surah || a.ayah - b.ayah);

  const payload = {
    name: 'Quranic Duʿā catalogue',
    description:
      'Generated from frontend/src/data/quranicDuas.ts by ' +
      'scripts/export-duas-to-backend.ts. Do not edit by hand.',
    generatedAt: new Date().toISOString().slice(0, 10),
    count: exported.length,
    duas: exported,
  };

  const dir = dirname(OUTPUT_JSON);
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
  writeFileSync(OUTPUT_JSON, `${JSON.stringify(payload, null, 2)}\n`, 'utf8');

  const categories = new Set(exported.map((d) => d.category));
  console.log(`Wrote ${exported.length} duas to ${OUTPUT_JSON}`);
  console.log(`  categories: ${categories.size}`);
  console.log(`  prophets:   ${new Set(exported.filter((d) => d.prophet).map((d) => d.prophet)).size}`);
}

main();
