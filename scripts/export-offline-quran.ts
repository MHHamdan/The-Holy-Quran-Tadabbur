/**
 * Export the canonical Qur'an text for offline reading:
 *   frontend/public/offline-quran/{1..114}.json   one surah per file
 *   frontend/public/offline-quran/manifest.json   copyright, checksums, page index
 *
 * The verse text is copied VERBATIM from data/raw/quran_tanzil.json (Tanzil
 * Uthmani + Simple, the same text the API serves from quran_verses). Nothing is
 * normalised, trimmed or re-encoded: the strings are passed through
 * JSON.stringify unchanged. Structure fields (hizb, rub', sajdah, quarter
 * start) are derived exactly as backend/scripts/ingest/seed_quran.py and the
 * /quran routes derive them, from data/manifests/quran_structure_markers.json.
 *
 * The Tanzil licence requires its copyright notice in every file that contains
 * a substantial portion of the text, so each surah file carries both blocks.
 *
 * The files are committed (the web Docker build only sees frontend/), and the
 * frontend loads them with fetch() (static assets, never JS chunks), so the
 * PWA 2 MiB chunk limit does not apply. frontend/src/lib/offlineQuran.test.ts
 * proves they equal quran_tanzil.json for all 6,236 ayat, and the Vite plugin
 * in frontend/vite.config.ts refuses to build when they are stale.
 *
 * Usage:
 *   npx tsx scripts/export-offline-quran.ts          # write the files
 *   npx tsx scripts/export-offline-quran.ts --check  # exit 1 if any file is stale
 */
import { createHash } from 'crypto';
import { existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from 'fs';
import { join, resolve } from 'path';

const ROOT = resolve(__dirname, '..');
const TANZIL = join(ROOT, 'data/raw/quran_tanzil.json');
const MARKERS = join(ROOT, 'data/manifests/quran_structure_markers.json');
const OUT_DIR = join(ROOT, 'frontend/public/offline-quran');

export const OFFLINE_FORMAT = 'tadabbur-offline-quran/1';

interface TanzilVerse {
  id: number;
  sura_no: number;
  sura_name_ar: string;
  sura_name_en: string;
  aya_no: number;
  aya_text: string;
  aya_text_emlaey: string;
  bismillah: string | null;
  bismillah_emlaey: string | null;
  page: number;
  jozz: number;
}

interface Tanzil {
  copyright: { uthmani: string; simple: string; attribution: string };
  source_sha256: Record<string, string>;
  verses: TanzilVerse[];
}

interface Markers {
  hizb_quarters: [number, number][];
  sajdahs: { sura: number; aya: number; type: string }[];
}

const sha256 = (data: string | Buffer) => createHash('sha256').update(data).digest('hex');

/** Every output file name -> exact content. */
export function buildOfflineFiles(tanzilRaw: string, markersRaw: string): Map<string, string> {
  const tanzil = JSON.parse(tanzilRaw) as Tanzil;
  const markers = JSON.parse(markersRaw) as Markers;
  if (tanzil.verses.length !== 6236) throw new Error(`expected 6236 verses, got ${tanzil.verses.length}`);

  const quarterStart = new Map<string, number>();
  markers.hizb_quarters.forEach(([s, a], i) => quarterStart.set(`${s}:${a}`, i + 1));
  const sajdah = new Map(markers.sajdahs.map((x) => [`${x.sura}:${x.aya}`, x.type]));

  const copyright = {
    uthmani: tanzil.copyright.uthmani,
    simple: tanzil.copyright.simple,
    attribution: tanzil.copyright.attribution,
  };

  const bySura = new Map<number, TanzilVerse[]>();
  for (const v of tanzil.verses) {
    if (!bySura.has(v.sura_no)) bySura.set(v.sura_no, []);
    bySura.get(v.sura_no)!.push(v);
  }

  const files = new Map<string, string>();
  const pages: Record<string, [[number, number], [number, number]]> = {};
  let rub = 0;
  for (let s = 1; s <= 114; s++) {
    const verses = bySura.get(s);
    if (!verses) throw new Error(`surah ${s} missing`);
    const out = verses.map((v) => {
      const key = `${v.sura_no}:${v.aya_no}`;
      rub = quarterStart.get(key) ?? rub;
      const p = String(v.page);
      if (!pages[p]) pages[p] = [[v.sura_no, v.aya_no], [v.sura_no, v.aya_no]];
      else pages[p][1] = [v.sura_no, v.aya_no];
      return {
        id: v.id,
        aya_no: v.aya_no,
        text_uthmani: v.aya_text,
        text_imlaei: v.aya_text_emlaey,
        bismillah_uthmani: v.bismillah,
        bismillah_imlaei: v.bismillah_emlaey,
        page_no: v.page,
        juz_no: v.jozz,
        hizb_no: Math.floor((rub - 1) / 4) + 1,
        rub_no: rub,
        sajda_type: sajdah.get(key) ?? null,
        quarter_start: quarterStart.has(key),
      };
    });
    const body = {
      format: OFFLINE_FORMAT,
      copyright,
      sura_no: s,
      sura_name_ar: verses[0].sura_name_ar,
      sura_name_en: verses[0].sura_name_en,
      verses: out,
    };
    files.set(`${s}.json`, JSON.stringify(body) + '\n');
  }

  const manifest = {
    format: OFFLINE_FORMAT,
    description:
      "Qur'an text for offline reading, copied verbatim from data/raw/quran_tanzil.json by scripts/export-offline-quran.ts. Do not edit.",
    copyright,
    source: 'data/raw/quran_tanzil.json',
    source_sha256: sha256(tanzilRaw),
    tanzil_source_sha256: tanzil.source_sha256,
    structure_markers_sha256: sha256(markersRaw),
    verse_count: tanzil.verses.length,
    // Mushaf page -> [first [sura, aya], last [sura, aya]]
    pages,
    files: Object.fromEntries([...files].map(([name, content]) => [name, sha256(content)])),
  };
  files.set('manifest.json', JSON.stringify(manifest, null, 1) + '\n');
  return files;
}

function main() {
  const files = buildOfflineFiles(readFileSync(TANZIL, 'utf-8'), readFileSync(MARKERS, 'utf-8'));
  if (process.argv.includes('--check')) {
    const stale = [...files].filter(([name, content]) => {
      const p = join(OUT_DIR, name);
      return !existsSync(p) || readFileSync(p, 'utf-8') !== content;
    });
    const extra = existsSync(OUT_DIR) ? readdirSync(OUT_DIR).filter((n) => n.endsWith('.json') && !files.has(n)) : [];
    if (stale.length || extra.length) {
      console.error(
        `offline-quran is stale (${stale.length} changed, ${extra.length} extra); run: npx tsx scripts/export-offline-quran.ts`,
      );
      process.exit(1);
    }
    console.log(`offline-quran up to date (${files.size} files)`);
    return;
  }
  mkdirSync(OUT_DIR, { recursive: true });
  let written = 0;
  for (const [name, content] of files) {
    const p = join(OUT_DIR, name);
    if (existsSync(p) && readFileSync(p, 'utf-8') === content) continue;
    writeFileSync(p, content, 'utf-8');
    written++;
  }
  console.log(`offline-quran: ${files.size} files, ${written} written -> frontend/public/offline-quran/`);
}

if (process.argv[1] && resolve(process.argv[1]) === resolve(__filename)) main();
