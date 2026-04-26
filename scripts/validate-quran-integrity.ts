/**
 * Quran Integrity Validator
 *
 * Validates local Quran data files and the source registry for structural
 * and content integrity. Run this after any change to content-related files.
 *
 * Usage:
 *   npx tsx scripts/validate-quran-integrity.ts
 *   npx tsx scripts/validate-quran-integrity.ts --verbose
 *   npx tsx scripts/validate-quran-integrity.ts --summary
 *
 * Exit codes:
 *   0 = all checks passed
 *   1 = one or more checks failed
 */

import { readFileSync, existsSync } from 'fs';
import { resolve, join } from 'path';

// ---------------------------------------------------------------------------
// CLI args
// ---------------------------------------------------------------------------

const args = process.argv.slice(2);
const VERBOSE = args.includes('--verbose');
const SUMMARY = args.includes('--summary');

// ---------------------------------------------------------------------------
// Paths
// ---------------------------------------------------------------------------

const ROOT = resolve(__dirname, '..');

const QURAN_JSON_PATH = join(ROOT, 'data/raw/quran_uthmani.json');
const QURAN_MANIFEST_PATH = join(ROOT, 'data/manifests/quran_hafs.json');
const TAFSIR_MANIFEST_PATH = join(ROOT, 'data/manifests/tafseer_sources.json');
const SOURCE_REGISTRY_PATH = join(ROOT, 'frontend/src/data/sourceRegistry.ts');

// ---------------------------------------------------------------------------
// Types (minimal, matching actual JSON structure)
// ---------------------------------------------------------------------------

interface QuranAyah {
  id?: number;
  sura_no: number;
  aya_no: number;
  aya_text?: string;
  text_uthmani?: string;
  [key: string]: unknown;
}

interface QuranManifest {
  total_verses?: number;
  total_surahs?: number;
  [key: string]: unknown;
}

interface TafsirSourceEntry {
  id: string;
  name_ar?: string;
  name_en?: string;
  author_ar?: string;
  author_en?: string;
  language?: string;
  [key: string]: unknown;
}

interface TafsirManifest {
  sources?: TafsirSourceEntry[];
  [key: string]: unknown;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const TOTAL_SURAHS = 114;
const TOTAL_AYAHS = 6236;

// Standard ayah count per surah (1-indexed)
const AYAHS_PER_SURAH: Record<number, number> = {
  1:7, 2:286, 3:200, 4:176, 5:120, 6:165, 7:206, 8:75, 9:129, 10:109,
  11:123, 12:111, 13:43, 14:52, 15:99, 16:128, 17:111, 18:110, 19:98, 20:135,
  21:112, 22:78, 23:118, 24:64, 25:77, 26:227, 27:93, 28:88, 29:69, 30:60,
  31:34, 32:30, 33:73, 34:54, 35:45, 36:83, 37:182, 38:88, 39:75, 40:85,
  41:54, 42:53, 43:89, 44:59, 45:37, 46:35, 47:38, 48:29, 49:18, 50:45,
  51:60, 52:49, 53:62, 54:55, 55:78, 56:96, 57:29, 58:22, 59:24, 60:13,
  61:14, 62:11, 63:11, 64:18, 65:12, 66:12, 67:30, 68:52, 69:52, 70:44,
  71:28, 72:28, 73:20, 74:56, 75:40, 76:31, 77:50, 78:40, 79:46, 80:42,
  81:29, 82:19, 83:36, 84:25, 85:22, 86:17, 87:19, 88:26, 89:30, 90:20,
  91:15, 92:21, 93:11, 94:8, 95:8, 96:19, 97:5, 98:8, 99:8, 100:11,
  101:11, 102:8, 103:3, 104:9, 105:5, 106:4, 107:7, 108:3, 109:6, 110:3,
  111:5, 112:4, 113:5, 114:6,
};

type CheckResult = { name: string; passed: boolean; errors: string[]; warnings: string[] };

function check(name: string, fn: () => { errors: string[]; warnings: string[] }): CheckResult {
  try {
    const { errors, warnings } = fn();
    return { name, passed: errors.length === 0, errors, warnings };
  } catch (e) {
    return {
      name,
      passed: false,
      errors: [`Check threw exception: ${e instanceof Error ? e.message : String(e)}`],
      warnings: [],
    };
  }
}

function loadJson<T>(path: string, label: string): T | null {
  if (!existsSync(path)) {
    return null;
  }
  try {
    const raw = readFileSync(path, 'utf-8');
    return JSON.parse(raw) as T;
  } catch (e) {
    return null;
  }
}

// ---------------------------------------------------------------------------
// Checks
// ---------------------------------------------------------------------------

function checkQuranFileExists(): CheckResult {
  return check('Quran data file exists', () => {
    const errors: string[] = [];
    if (!existsSync(QURAN_JSON_PATH)) {
      errors.push(`Quran data file not found: ${QURAN_JSON_PATH}`);
    }
    return { errors, warnings: [] };
  });
}

function checkQuranStructure(ayahs: QuranAyah[]): CheckResult {
  return check('Quran data is a non-empty array', () => {
    const errors: string[] = [];
    if (!Array.isArray(ayahs)) {
      errors.push('Quran data is not an array');
    } else if (ayahs.length === 0) {
      errors.push('Quran data array is empty');
    }
    return { errors, warnings: [] };
  });
}

function checkTotalAyahs(ayahs: QuranAyah[]): CheckResult {
  return check(`Total ayahs = ${TOTAL_AYAHS}`, () => {
    const errors: string[] = [];
    if (ayahs.length !== TOTAL_AYAHS) {
      errors.push(`Expected ${TOTAL_AYAHS} ayahs, found ${ayahs.length}`);
    }
    return { errors, warnings: [] };
  });
}

function checkTotalSurahs(ayahs: QuranAyah[]): CheckResult {
  return check(`Total surahs = ${TOTAL_SURAHS}`, () => {
    const errors: string[] = [];
    const surahNos = new Set(ayahs.map((a) => a.sura_no));
    if (surahNos.size !== TOTAL_SURAHS) {
      errors.push(`Expected ${TOTAL_SURAHS} unique surahs, found ${surahNos.size}`);
    }
    return { errors, warnings: [] };
  });
}

function checkValidSurahNumbers(ayahs: QuranAyah[]): CheckResult {
  return check('All sura_no values are in range 1–114', () => {
    const errors: string[] = [];
    const invalid = ayahs.filter((a) => a.sura_no < 1 || a.sura_no > 114 || !Number.isInteger(a.sura_no));
    if (invalid.length > 0) {
      errors.push(`${invalid.length} ayahs have invalid sura_no. First: ${JSON.stringify(invalid[0])}`);
    }
    return { errors, warnings: [] };
  });
}

function checkValidAyahNumbers(ayahs: QuranAyah[]): CheckResult {
  return check('All aya_no values are ≥ 1', () => {
    const errors: string[] = [];
    const invalid = ayahs.filter((a) => a.aya_no < 1 || !Number.isInteger(a.aya_no));
    if (invalid.length > 0) {
      errors.push(`${invalid.length} ayahs have invalid aya_no. First: ${JSON.stringify(invalid[0])}`);
    }
    return { errors, warnings: [] };
  });
}

function checkNoDuplicateKeys(ayahs: QuranAyah[]): CheckResult {
  return check('No duplicate ayah keys (sura:aya)', () => {
    const errors: string[] = [];
    const seen = new Map<string, number>();
    const duplicates: string[] = [];
    for (const ayah of ayahs) {
      const key = `${ayah.sura_no}:${ayah.aya_no}`;
      const count = (seen.get(key) ?? 0) + 1;
      seen.set(key, count);
      if (count === 2) duplicates.push(key);
    }
    if (duplicates.length > 0) {
      errors.push(`${duplicates.length} duplicate keys found. First: ${duplicates[0]}`);
    }
    return { errors, warnings: [] };
  });
}

function checkNoMissingKeys(ayahs: QuranAyah[]): CheckResult {
  return check('No missing ayah keys (complete sequence per surah)', () => {
    const errors: string[] = [];
    const bysurah = new Map<number, Set<number>>();
    for (const ayah of ayahs) {
      if (!bysurah.has(ayah.sura_no)) bysurah.set(ayah.sura_no, new Set());
      bysurah.get(ayah.sura_no)!.add(ayah.aya_no);
    }
    for (let s = 1; s <= TOTAL_SURAHS; s++) {
      const expected = AYAHS_PER_SURAH[s];
      const found = bysurah.get(s);
      if (!found) {
        errors.push(`Surah ${s}: no ayahs found`);
        continue;
      }
      for (let a = 1; a <= expected; a++) {
        if (!found.has(a)) {
          errors.push(`Missing ayah ${s}:${a}`);
          if (errors.length > 20) {
            errors.push('... (truncated, too many missing ayahs)');
            return { errors, warnings: [] };
          }
        }
      }
    }
    return { errors, warnings: [] };
  });
}

function checkNoEmptyArabicText(ayahs: QuranAyah[]): CheckResult {
  return check('No empty Arabic Quran text fields', () => {
    const errors: string[] = [];
    const empty = ayahs.filter((a) => {
      const text = a.aya_text ?? a.text_uthmani ?? '';
      return !text || String(text).trim() === '';
    });
    if (empty.length > 0) {
      errors.push(`${empty.length} ayahs have empty Arabic text. First: ${JSON.stringify(empty[0])}`);
    }
    return { errors, warnings: [] };
  });
}

function checkArabicTextNotEnglish(ayahs: QuranAyah[]): CheckResult {
  return check('Arabic text does not contain Latin characters (not English)', () => {
    const errors: string[] = [];
    // Arabic text should not have a large proportion of Latin ASCII characters
    const latinPattern = /[a-zA-Z]{5,}/;
    const suspicious = ayahs.filter((a) => {
      const text = String(a.aya_text ?? a.text_uthmani ?? '');
      return latinPattern.test(text);
    });
    if (suspicious.length > 0) {
      errors.push(
        `${suspicious.length} ayahs appear to contain Latin/English text in the Arabic field. First: ${JSON.stringify(suspicious[0])}`
      );
    }
    return { errors, warnings: [] };
  });
}

function checkAyahCountPerSurah(ayahs: QuranAyah[]): CheckResult {
  return check('Ayah count per surah matches expected values', () => {
    const errors: string[] = [];
    const bysurah = new Map<number, number>();
    for (const ayah of ayahs) {
      bysurah.set(ayah.sura_no, (bysurah.get(ayah.sura_no) ?? 0) + 1);
    }
    for (let s = 1; s <= TOTAL_SURAHS; s++) {
      const expected = AYAHS_PER_SURAH[s];
      const found = bysurah.get(s) ?? 0;
      if (found !== expected) {
        errors.push(`Surah ${s}: expected ${expected} ayahs, found ${found}`);
      }
    }
    return { errors, warnings: [] };
  });
}

function checkTafsirSourcesHaveIds(manifest: TafsirManifest): CheckResult {
  return check('Every tafsir source entry has a non-empty id', () => {
    const errors: string[] = [];
    const sources = manifest.sources ?? [];
    const missing = sources.filter((s) => !s.id || String(s.id).trim() === '');
    if (missing.length > 0) {
      errors.push(`${missing.length} tafsir sources have no id`);
    }
    return { errors, warnings: [] };
  });
}

function checkTafsirSourceRequiredFields(manifest: TafsirManifest): CheckResult {
  return check('Every tafsir source has name_ar, name_en, author_en, language', () => {
    const errors: string[] = [];
    const sources = manifest.sources ?? [];
    for (const source of sources) {
      for (const field of ['name_ar', 'name_en', 'author_en', 'language'] as const) {
        if (!source[field] || String(source[field]).trim() === '') {
          errors.push(`Tafsir source "${source.id}": missing field "${field}"`);
        }
      }
    }
    return { errors, warnings: [] };
  });
}

function checkSourceRegistryFile(): CheckResult {
  return check('Source registry file exists', () => {
    const errors: string[] = [];
    if (!existsSync(SOURCE_REGISTRY_PATH)) {
      errors.push(`Source registry not found: ${SOURCE_REGISTRY_PATH}`);
    }
    return { errors, warnings: [] };
  });
}

/** Extract just the SOURCE_REGISTRY array literal from the file, before any helper functions. */
function extractRegistryArrayText(raw: string): string {
  const arrayStart = raw.indexOf('SOURCE_REGISTRY: Source[] = [');
  if (arrayStart === -1) return '';
  // The array ends at the first ]; on its own after the opening
  const afterDecl = raw.indexOf('[', arrayStart);
  if (afterDecl === -1) return '';
  // Find the end marker — the helpers section starts after the array
  const helpersMarker = raw.indexOf('// ---------------------------------------------------------------------------\n// Lookup helpers');
  if (helpersMarker > afterDecl) {
    return raw.slice(afterDecl, helpersMarker);
  }
  return raw.slice(afterDecl);
}

/** Extract source object blocks from the registry array text. Each block is {…}. */
function extractSourceBlocks(arrayText: string): string[] {
  const blocks: string[] = [];
  let depth = 0;
  let start = -1;
  for (let i = 0; i < arrayText.length; i++) {
    const ch = arrayText[i];
    if (ch === '{') {
      if (depth === 0) start = i;
      depth++;
    } else if (ch === '}') {
      depth--;
      if (depth === 0 && start !== -1) {
        blocks.push(arrayText.slice(start, i + 1));
        start = -1;
      }
    }
  }
  return blocks;
}

function checkSourceRegistryRequiredFields(): CheckResult {
  return check('Source registry: all entries have required fields', () => {
    const errors: string[] = [];
    const warnings: string[] = [];

    if (!existsSync(SOURCE_REGISTRY_PATH)) {
      errors.push('Source registry file not found — skipping field validation');
      return { errors, warnings };
    }

    const raw = readFileSync(SOURCE_REGISTRY_PATH, 'utf-8');
    const arrayText = extractRegistryArrayText(raw);
    if (!arrayText) {
      errors.push('Could not find SOURCE_REGISTRY array in registry file');
      return { errors, warnings };
    }

    const REQUIRED_FIELDS = [
      'sourceId', 'titleArabic', 'titleEnglish', 'author', 'language',
      'type', 'reliabilityLevel', 'licenseOrTerms', 'sourceUrl',
      'lastVerifiedAt', 'notes',
    ];

    const seenIds = new Set<string>();
    const blocks = extractSourceBlocks(arrayText);

    if (blocks.length === 0) {
      errors.push('No source objects found in registry array');
      return { errors, warnings };
    }

    for (const block of blocks) {
      const idMatch = block.match(/sourceId:\s*['"]([^'"]+)['"]/);
      const id = idMatch ? idMatch[1] : 'UNKNOWN';

      if (seenIds.has(id)) {
        errors.push(`Duplicate sourceId in registry: "${id}"`);
      }
      seenIds.add(id);

      for (const field of REQUIRED_FIELDS) {
        const fieldPattern = new RegExp(`\\b${field}:\\s*['"\`]`);
        if (!fieldPattern.test(block)) {
          errors.push(`Source "${id}": missing field "${field}" in registry`);
        }
      }
    }

    return { errors, warnings };
  });
}

function checkNoExperimentalSourcesInCanonical(): CheckResult {
  return check('No experimental source is labeled as canonical', () => {
    const errors: string[] = [];
    if (!existsSync(SOURCE_REGISTRY_PATH)) return { errors, warnings: [] };

    const raw = readFileSync(SOURCE_REGISTRY_PATH, 'utf-8');
    const arrayText = extractRegistryArrayText(raw);
    if (!arrayText) return { errors, warnings: [] };

    const blocks = extractSourceBlocks(arrayText);
    for (const block of blocks) {
      const idMatch = block.match(/sourceId:\s*['"]([^'"]+)['"]/);
      const id = idMatch ? idMatch[1] : 'UNKNOWN';
      const isExperimental = /reliabilityLevel:\s*['"]experimental['"]/.test(block);
      const isCanonical = /reliabilityLevel:\s*['"]canonical['"]/.test(block);
      const isUnverified = /lastVerifiedAt:\s*['"]unverified['"]/.test(block);
      if (isExperimental && isCanonical) {
        errors.push(`Source "${id}": reliabilityLevel cannot be both "experimental" and "canonical"`);
      }
      if (isUnverified && isCanonical) {
        errors.push(`Source "${id}": lastVerifiedAt="unverified" is incompatible with reliabilityLevel="canonical"`);
      }
    }
    return { errors, warnings: [] };
  });
}

// ---------------------------------------------------------------------------
// Run all checks
// ---------------------------------------------------------------------------

async function main() {
  const results: CheckResult[] = [];
  let totalErrors = 0;
  let totalWarnings = 0;

  if (!SUMMARY) {
    console.log('='.repeat(60));
    console.log('  Quran Content Integrity Validator');
    console.log('='.repeat(60));
    console.log();
  }

  // --- File existence ---
  results.push(checkQuranFileExists());
  results.push(checkSourceRegistryFile());

  // --- Load Quran data ---
  let ayahs: QuranAyah[] = [];
  if (existsSync(QURAN_JSON_PATH)) {
    const raw = readFileSync(QURAN_JSON_PATH, 'utf-8');
    try {
      const parsed = JSON.parse(raw);
      // Handle both array and object-with-array formats
      ayahs = Array.isArray(parsed) ? parsed : (parsed.verses ?? parsed.data ?? parsed.ayahs ?? []);
    } catch {
      results.push({
        name: 'Quran JSON is valid JSON',
        passed: false,
        errors: ['Failed to parse quran_uthmani.json as JSON'],
        warnings: [],
      });
    }
  }

  if (ayahs.length > 0) {
    results.push(checkQuranStructure(ayahs));
    results.push(checkTotalAyahs(ayahs));
    results.push(checkTotalSurahs(ayahs));
    results.push(checkValidSurahNumbers(ayahs));
    results.push(checkValidAyahNumbers(ayahs));
    results.push(checkNoDuplicateKeys(ayahs));
    results.push(checkNoMissingKeys(ayahs));
    results.push(checkNoEmptyArabicText(ayahs));
    results.push(checkArabicTextNotEnglish(ayahs));
    results.push(checkAyahCountPerSurah(ayahs));
  } else if (existsSync(QURAN_JSON_PATH)) {
    results.push({
      name: 'Quran data loaded',
      passed: false,
      errors: ['Quran JSON parsed but no ayahs array found — check file structure'],
      warnings: [],
    });
  }

  // --- Load tafsir manifest ---
  const tafsirManifest = loadJson<TafsirManifest>(TAFSIR_MANIFEST_PATH, 'tafsir manifest');
  if (tafsirManifest) {
    results.push(checkTafsirSourcesHaveIds(tafsirManifest));
    results.push(checkTafsirSourceRequiredFields(tafsirManifest));
  } else {
    results.push({
      name: 'Tafsir sources manifest',
      passed: false,
      errors: [`Could not load ${TAFSIR_MANIFEST_PATH}`],
      warnings: [],
    });
  }

  // --- Source registry checks ---
  results.push(checkSourceRegistryRequiredFields());
  results.push(checkNoExperimentalSourcesInCanonical());

  // --- Report ---
  for (const result of results) {
    totalErrors += result.errors.length;
    totalWarnings += result.warnings.length;

    if (!SUMMARY) {
      const icon = result.passed ? '✓' : '✗';
      const color = result.passed ? '\x1b[32m' : '\x1b[31m';
      const reset = '\x1b[0m';
      console.log(`${color}${icon}${reset} ${result.name}`);

      if (VERBOSE || !result.passed) {
        for (const err of result.errors) {
          console.log(`    \x1b[31mERROR:\x1b[0m ${err}`);
        }
      }
      for (const warn of result.warnings) {
        console.log(`    \x1b[33mWARN:\x1b[0m ${warn}`);
      }
    }
  }

  const passed = results.filter((r) => r.passed).length;
  const failed = results.filter((r) => !r.passed).length;

  if (!SUMMARY) {
    console.log();
    console.log('='.repeat(60));
    console.log(`  Results: ${passed} passed, ${failed} failed, ${totalWarnings} warnings`);
    console.log('='.repeat(60));
  } else {
    console.log(`Quran integrity: ${passed} passed, ${failed} failed, ${totalWarnings} warnings`);
  }

  if (failed > 0) {
    if (!SUMMARY) {
      console.log('\n\x1b[31mINTEGRITY CHECK FAILED\x1b[0m — fix errors before merging.\n');
    }
    process.exit(1);
  } else {
    if (!SUMMARY) {
      console.log('\n\x1b[32mAll integrity checks passed.\x1b[0m\n');
    }
    process.exit(0);
  }
}

main().catch((e) => {
  console.error('Validator crashed:', e);
  process.exit(1);
});
