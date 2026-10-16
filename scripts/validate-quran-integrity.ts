/**
 * Quran Integrity Validator
 *
 * Validates local Quran data files and the source registry for structural
 * and content integrity. Run this after any change to content-related files.
 *
 * Enabled rows of tafseer_sources are cross-checked against the manifest too
 * (needs python3 + asyncpg). DATABASE_URL comes from the environment, else
 * from the repository's .env (the main checkout's .env in a git worktree).
 * Without a database the check is skipped with a warning; --require-db (or
 * REQUIRE_DB_CHECK=1) makes that an error.
 *
 * Usage:
 *   npx tsx scripts/validate-quran-integrity.ts
 *   npx tsx scripts/validate-quran-integrity.ts --verbose
 *   npx tsx scripts/validate-quran-integrity.ts --summary
 *   npx tsx scripts/validate-quran-integrity.ts --require-db
 *
 * Exit codes:
 *   0 = all checks passed
 *   1 = one or more checks failed
 */

import { readFileSync, existsSync, readdirSync, statSync } from 'fs';
import { spawnSync } from 'child_process';
import { QURANIC_DUAS } from '../frontend/src/data/quranicDuas';
import { CONFUSION_PAIRS, REPEATED_PHRASES } from '../frontend/src/data/quranMemorizationLinks';
import { resolve, join, relative } from 'path';

// ---------------------------------------------------------------------------
// CLI args
// ---------------------------------------------------------------------------

const args = process.argv.slice(2);
const VERBOSE = args.includes('--verbose');
const SUMMARY = args.includes('--summary');
const REQUIRE_DB = args.includes('--require-db') || process.env.REQUIRE_DB_CHECK === '1';

// ---------------------------------------------------------------------------
// Paths
// ---------------------------------------------------------------------------

const ROOT = resolve(__dirname, '..');

const QURAN_JSON_PATH = join(ROOT, 'data/raw/quran_tanzil.json');
const QURAN_MANIFEST_PATH = join(ROOT, 'data/manifests/quran_hafs.json');
const TAFSIR_MANIFEST_PATH = join(ROOT, 'data/manifests/tafseer_sources.json');
const SOURCE_REGISTRY_PATH = join(ROOT, 'frontend/src/data/sourceRegistry.ts');
const READER_TAFSIR_EDITIONS_PATH = join(ROOT, 'frontend/src/components/quran/tafsirEditions.tsx');

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
// Tafsir licence cross-check: manifest x registry (x database when reachable)
// ---------------------------------------------------------------------------

interface ManifestLicence {
  type?: string;
  verified_date?: string | null;
  [key: string]: unknown;
}

interface RegistryEntryInfo {
  id: string;
  licenseStatus?: string;
  blocked: boolean;
  /** licenseOrTerms or sourceUrl credits the riotu-lab/Quran-Tafseers dataset. */
  creditsHfDataset: boolean;
}

/** Manifest record of where a source's stored text really came from. */
interface StoredCopy {
  seeded_from?: string;
  owner_review?: boolean;
  registry_status?: string;
}

/** sourceId -> licence facts parsed from the SOURCE_REGISTRY array literal. */
function readRegistryEntries(): Map<string, RegistryEntryInfo> {
  const out = new Map<string, RegistryEntryInfo>();
  if (!existsSync(SOURCE_REGISTRY_PATH)) return out;
  const blocks = extractSourceBlocks(extractRegistryArrayText(readFileSync(SOURCE_REGISTRY_PATH, 'utf-8')));
  for (const block of blocks) {
    const id = block.match(/sourceId:\s*['"]([^'"]+)['"]/)?.[1];
    if (!id) continue;
    const licenseStatus = block.match(/licenseStatus:\s*['"]([^'"]+)['"]/)?.[1];
    const notesBlocked = /notes:\s*['"`]\s*DO NOT DISPLAY/.test(block);
    const terms = block.match(/licenseOrTerms:\s*(['"`])((?:\\.|(?!\1).)*)\1/)?.[2] ?? '';
    const url = block.match(/sourceUrl:\s*['"`]([^'"`]+)['"`]/)?.[1] ?? '';
    const creditsHfDataset = /riotu-lab\/Quran-Tafseers/.test(`${terms} ${url}`);
    out.set(id, { id, licenseStatus, blocked: licenseStatus === 'blocked' || notesBlocked, creditsHfDataset });
  }
  return out;
}

const NOT_SHIPPABLE_STATUSES = new Set(['blocked', 'unverified', 'pending']);
const AVAILABLE_STATUSES = new Set(['available', 'available_via_api']);

/**
 * Every tafsir source the product may serve must be registered with a licence
 * that is neither blocked nor unverified, and the manifest must record when
 * that licence was verified. "May serve" means: listed in the manifest's
 * enabled_ids, or carrying an available status.
 *
 * Exception: ids in the manifest's licence_hold_ids keep their enabled row and
 * stored text but must NOT be licence-verified anywhere (empty verified_date,
 * registry neither cleared nor restricted, DB license_verified=0) and must not
 * be offered by the reader editions list, so no licensed-only path serves them.
 */
function checkTafsirLicenceCrossCheck(manifest: TafsirManifest): CheckResult {
  return check('Tafsir sources: enabled ids are registered with verified licences', () => {
    const errors: string[] = [];
    const warnings: string[] = [];
    const registry = readRegistryEntries();
    const sources = (manifest.sources ?? []) as TafsirSourceEntry[];
    const placeholders = ((manifest as Record<string, unknown>).placeholder_sources ?? []) as TafsirSourceEntry[];
    const byId = new Map(sources.map((s) => [s.id, s]));
    const enabledIds = (manifest as Record<string, unknown>).enabled_ids as string[] | undefined;

    if (!Array.isArray(enabledIds) || enabledIds.length === 0) {
      errors.push('tafseer_sources.json has no "enabled_ids" list (ids allowed to be enabled in tafseer_sources)');
    }

    const holdIds = new Set<string>(
      ((manifest as Record<string, unknown>).licence_hold_ids as string[] | undefined) ?? [],
    );
    const mustBeShippable = new Set<string>(enabledIds ?? []);
    for (const s of [...sources, ...placeholders]) {
      if (AVAILABLE_STATUSES.has(String(s.status ?? ''))) mustBeShippable.add(s.id);
    }
    // The Mushaf list may only use ids from this file (test_tafsir_edition_licences).
    const readerSources = [READER_TAFSIR_EDITIONS_PATH]
      .filter((p) => existsSync(p))
      .map((p) => [p, readFileSync(p, 'utf-8')] as const);
    for (const id of holdIds) {
      mustBeShippable.delete(id);
      const entry = byId.get(id);
      const licence = entry?.license as ManifestLicence | undefined;
      if (!entry) errors.push(`licence_hold_ids: "${id}" is not in manifest.sources`);
      else if (licence && typeof licence === 'object' && licence.verified_date) {
        errors.push(`"${id}" is on licence hold but manifest license.verified_date is set`);
      }
      const reg = registry.get(id);
      if (!reg) errors.push(`"${id}" is on licence hold but has no sourceRegistry.ts entry`);
      else if (reg.licenseStatus === 'cleared' || reg.licenseStatus === 'restricted') {
        errors.push(`"${id}" is on licence hold but sourceRegistry licenseStatus is "${reg.licenseStatus}"`);
      }
      for (const [path, text] of readerSources) {
        if (text.includes(`db_source_id: '${id}'`)) {
          errors.push(`${relative(ROOT, path)}: offers "${id}", which is on licence hold`);
        }
      }
    }

    for (const id of mustBeShippable) {
      const entry = byId.get(id);
      if (!entry) {
        errors.push(`"${id}" may be served but is not in manifest.sources (placeholder entries carry no licence record)`);
      } else {
        const licence = entry.license as ManifestLicence | string | undefined;
        if (typeof licence !== 'object' || !licence) {
          errors.push(`"${id}": manifest license is not a structured record`);
        } else {
          if (!licence.verified_date) errors.push(`"${id}": manifest license.verified_date is null`);
          if (String(licence.type ?? '').startsWith('pending')) {
            errors.push(`"${id}": manifest licence type is "${licence.type}"`);
          }
        }
      }
      const reg = registry.get(id);
      const storedCopy = entry?.stored_copy as StoredCopy | undefined;
      if (!reg) {
        errors.push(`"${id}" may be served but has no sourceRegistry.ts entry`);
      } else if (
        reg.licenseStatus === 'unverified' &&
        !reg.blocked &&
        storedCopy?.owner_review === true &&
        storedCopy.registry_status === 'unverified'
      ) {
        // The work's licence is verified (checked above) but the terms of the
        // digital edition the stored text came from are not recorded. That is
        // stated in the footer and queued for the owner, not hidden.
        warnings.push(
          `"${id}": stored copy from ${storedCopy.seeded_from ?? 'an unrecorded origin'} has unrecorded ` +
          'digital-edition terms (registry "unverified"); owner review: reseed from the pinned dataset or record the terms',
        );
      } else if (reg.blocked || NOT_SHIPPABLE_STATUSES.has(reg.licenseStatus ?? '')) {
        errors.push(`"${id}": sourceRegistry licenseStatus is "${reg.licenseStatus ?? 'blocked'}"`);
      }
      if (reg && storedCopy) {
        // The footer must not credit a dataset the stored text did not come from.
        if (storedCopy.registry_status && reg.licenseStatus !== storedCopy.registry_status) {
          errors.push(
            `"${id}": manifest stored_copy.registry_status is "${storedCopy.registry_status}" ` +
            `but sourceRegistry licenseStatus is "${reg.licenseStatus}"`,
          );
        }
        if (reg.creditsHfDataset) {
          errors.push(
            `"${id}": sourceRegistry credits riotu-lab/Quran-Tafseers in licenseOrTerms/sourceUrl, ` +
            `but the stored copy was seeded from ${storedCopy.seeded_from ?? 'another origin'} (manifest stored_copy)`,
          );
        }
      }
    }

    // Database: enabled rows must be in enabled_ids. Optional, needs DATABASE_URL.
    const db = readEnabledDbSources();
    if (db.error) {
      if (REQUIRE_DB) errors.push(`database cross-check could not run: ${db.error}`);
      else warnings.push(`database cross-check skipped: ${db.error}`);
    } else {
      for (const row of db.rows) {
        if (holdIds.has(row.id)) {
          if (row.license_verified !== 0) {
            errors.push(`DB tafseer_sources "${row.id}" is on licence hold but license_verified=${row.license_verified}`);
          }
          continue;
        }
        if (!mustBeShippable.has(row.id)) {
          errors.push(`DB tafseer_sources "${row.id}" is enabled but not in manifest enabled_ids`);
        }
        if (row.license_verified !== 1) {
          errors.push(`DB tafseer_sources "${row.id}" is enabled with license_verified=${row.license_verified}`);
        }
      }
    }
    return { errors, warnings };
  });
}

interface DbSourceRow { id: string; license_verified: number }

/** KEY=VALUE pairs of a dotenv file (no interpolation). */
function readDotenv(path: string): Record<string, string> {
  const out: Record<string, string> = {};
  if (!existsSync(path)) return out;
  for (const line of readFileSync(path, 'utf-8').split(/\r?\n/)) {
    const m = line.match(/^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$/);
    if (!m) continue;
    out[m[1]] = m[2].replace(/^(['"])(.*)\1$/, '$2');
  }
  return out;
}

/**
 * DATABASE_URL from the environment, else from the repository's .env (in a
 * linked git worktree, the main checkout's .env), so a local run does the
 * database cross-check by default instead of silently skipping it.
 */
function resolveDatabaseUrl(): { url?: string; from?: string } {
  if (process.env.DATABASE_URL) return { url: process.env.DATABASE_URL, from: 'environment' };
  const candidates = [join(ROOT, '.env'), join(ROOT, 'backend/.env')];
  const common = spawnSync('git', ['rev-parse', '--path-format=absolute', '--git-common-dir'], {
    cwd: ROOT, encoding: 'utf-8', timeout: 5000,
  });
  if (common.status === 0 && common.stdout.trim()) {
    const mainRoot = resolve(common.stdout.trim(), '..');
    if (mainRoot !== ROOT) candidates.push(join(mainRoot, '.env'), join(mainRoot, 'backend/.env'));
  }
  for (const path of candidates) {
    const url = readDotenv(path).DATABASE_URL;
    if (url) return { url, from: path };
  }
  return {};
}

function readEnabledDbSources(): { rows: DbSourceRow[]; error?: string } {
  const { url } = resolveDatabaseUrl();
  if (!url) return { rows: [], error: 'DATABASE_URL not set and not found in .env' };
  const py = [
    'import asyncio, json, os, asyncpg',
    'async def main():',
    "    c = await asyncpg.connect(os.environ['DATABASE_URL'].replace('+asyncpg', ''))",
    "    rows = await c.fetch('SELECT id, license_verified FROM tafseer_sources WHERE is_enabled = 1')",
    '    print(json.dumps([dict(r) for r in rows]))',
    '    await c.close()',
    'asyncio.run(main())',
  ].join('\n');
  const r = spawnSync('python3', ['-c', py], { encoding: 'utf-8', env: { ...process.env, DATABASE_URL: url }, timeout: 20000 });
  if (r.status !== 0) return { rows: [], error: (r.stderr || r.error?.message || 'query failed').trim().split('\n').pop() };
  try {
    return { rows: JSON.parse(r.stdout) as DbSourceRow[] };
  } catch {
    return { rows: [], error: 'could not parse query output' };
  }
}

// ---------------------------------------------------------------------------
// Duʿā excerpts: verbatim Tanzil Uthmani, one segment per verse of the range
// ---------------------------------------------------------------------------

const DUA_SEGMENT_SEPARATOR = ' ۝ ';

function checkDuasVerbatim(ayahs: QuranAyah[]): CheckResult {
  return check('Duʿā Arabic (quranicDuas.ts) is verbatim Tanzil text for its range', () => {
    const errors: string[] = [];
    const byKey = new Map(ayahs.map((a) => [`${a.sura_no}:${a.aya_no}`, String(a.aya_text ?? '')]));
    for (const dua of QURANIC_DUAS) {
      const last = dua.ayahEnd ?? dua.ayah;
      const segments = dua.ayatUthmani.split(DUA_SEGMENT_SEPARATOR);
      const expected = last - dua.ayah + 1;
      if (segments.length !== expected) {
        errors.push(`${dua.id}: ${segments.length} segment(s) for ${expected} verse(s) ${dua.surah}:${dua.ayah}-${last}`);
        continue;
      }
      segments.forEach((seg, i) => {
        const ref = `${dua.surah}:${dua.ayah + i}`;
        const verse = byKey.get(ref);
        if (!verse) {
          errors.push(`${dua.id}: no verse ${ref}`);
          return;
        }
        const at = verse.indexOf(seg);
        if (!seg.trim() || at === -1) {
          errors.push(`${dua.id}: segment ${i + 1} is not verbatim text of ${ref}`);
          return;
        }
        const before = at === 0 ? ' ' : verse[at - 1];
        const after = at + seg.length === verse.length ? ' ' : verse[at + seg.length];
        if (before !== ' ' || after !== ' ') {
          errors.push(`${dua.id}: segment ${i + 1} of ${ref} does not start and end on word boundaries`);
        }
      });
    }
    return { errors, warnings: [] };
  });
}

// ---------------------------------------------------------------------------
// Memorisation data: phrases occur where the data says they do
// ---------------------------------------------------------------------------

/** Letters only (no marks, tatweel, pause signs; alif/ya/ta-marbuta unified). */
function skeleton(text: string): string {
  return text
    .replace(/\uFEFF/g, '')
    .replace(/[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED\u0640\u06DE\u06E9]/g, '')
    .replace(/ءا/g, 'ا')
    .replace(/[ٱأإآ]/g, 'ا')
    .replace(/[ىئ]/g, 'ي')
    .replace(/ؤ/g, 'و')
    .replace(/ة/g, 'ه')
    .replace(/ء/g, '')
    .replace(/\s+/g, '');
}

function checkMemorizationPhrases(ayahs: QuranAyah[]): CheckResult {
  return check('Memorisation phrases occur in the verses and surahs they cite', () => {
    const errors: string[] = [];
    const verseSk = new Map<string, string>();
    const surahSk = new Map<number, string>();
    for (const a of ayahs) {
      const sk = skeleton(String(a.aya_text ?? '')) + '|' + skeleton(String(a.aya_text_emlaey ?? ''));
      verseSk.set(`${a.sura_no}:${a.aya_no}`, sk);
      surahSk.set(a.sura_no, (surahSk.get(a.sura_no) ?? '') + '|' + sk);
    }
    for (const phrase of REPEATED_PHRASES) {
      const sk = skeleton(phrase.phraseArabic);
      if (!sk) {
        errors.push(`${phrase.id}: empty phrase (missing excerpt key?)`);
        continue;
      }
      for (const occ of phrase.occurrences) {
        if (!(verseSk.get(`${occ.surah}:${occ.ayah}`) ?? '').includes(sk)) {
          errors.push(`${phrase.id}: phrase not in ${occ.surah}:${occ.ayah}`);
        }
      }
    }
    // Quoted vowelled Arabic in the pair notes must come from the surahs compared.
    const quoted = /"([^"]*[\u064B-\u0652][^"]*[\u064B-\u0652][^"]*)"/g;
    for (const pair of CONFUSION_PAIRS) {
      const hay = (surahSk.get(pair.ayahA.surah) ?? '') + (surahSk.get(pair.ayahB.surah) ?? '');
      const notes = [pair.keyDifference?.ar, pair.memorizerTip?.ar, pair.confusionReason?.ar].join(' ');
      for (const m of notes.matchAll(quoted)) {
        if (!hay.includes(skeleton(m[1]))) {
          errors.push(`${pair.id}: quoted text not found in surah ${pair.ayahA.surah} or ${pair.ayahB.surah}: ${m[1]}`);
        }
      }
    }
    return { errors, warnings: [] };
  });
}

// ---------------------------------------------------------------------------
// Attribution: every view that renders Qur'an text credits Tanzil
// ---------------------------------------------------------------------------

/*
 * A view renders Qur'an text when either
 *   (a) it reads a verse-text field of an API verse object (text_uthmani,
 *       verse.text_ar, ...) or calls quranExcerpt() itself, or
 *   (b) it imports, directly or through other .ts modules, a data module
 *       built on the canonical excerpts (utils/quranExcerpt.ts or
 *       data/generated/quranExcerpts.json), e.g. revelationTimeline.ts.
 * (b) follows the import graph, so a new page that quotes verses through a
 * data module is caught without anyone adding its name here.
 *
 * Every such view must render <QuranTextAttribution> (or <LiveVerse>, which
 * renders it). A missing attribution is an error, except for the views listed
 * in ATTRIBUTION_KNOWN_GAPS (reported as warnings, each with its owner) and
 * METADATA_ONLY (import a verse module but render none of its verse fields).
 */

/** (a) Fields that carry Qur'an text, and direct excerpt calls. */
const VERSE_FIELD_PATTERN = new RegExp(
  [
    String.raw`\b(text_uthmani|text_imlaei|ayahTextUthmani|firstAyahPreview|lastAyahPreview|ayatUthmani|verseTextFor)\b`,
    String.raw`\b(verse|ayah|aya|v)\??\.text_ar\b`,
    String.raw`quranExcerpt\(`,
  ].join('|'),
);
/** Ways a component satisfies the Tanzil attribution requirement. */
const ATTRIBUTION_PATTERN = /<QuranTextAttribution\b|<LiveVerse\b/;
/** (b) Roots of the data path: the canonical excerpt accessor and its data. */
const EXCERPT_ROOTS = ['frontend/src/utils/quranExcerpt.ts', 'frontend/src/data/generated/quranExcerpts.json'];

/** Views that render Qur'an text without attribution today; warnings, not errors. */
// Empty since 2026-10-16: /ask, the quiz, the Juz navigator and the daily
// challenge all carry QuranTextAttribution, so any new gap is an error.
const ATTRIBUTION_KNOWN_GAPS: Record<string, string> = {};

/** Import a verse data module but render none of its verse-bearing fields (checked 2026-10-15). */
const METADATA_ONLY: Record<string, string> = {
  'frontend/src/pages/ReadingStatsPage.tsx': 'JUZ_OVERVIEW numbers and names only',
  'frontend/src/pages/SurahComparePage.tsx': 'SURAH_ATLAS_DATA ayah counts and TIMELINE_BY_SURAH period only',
  'frontend/src/components/stories/WhereElseMentionedPanel.tsx': 'QURAN_STORIES_FIRST_BATCH verse references only',
};

function listSources(dir: string, out: string[] = []): string[] {
  for (const name of readdirSync(dir)) {
    if (name === 'node_modules' || name === '__tests__') continue;
    const p = join(dir, name);
    if (statSync(p).isDirectory()) listSources(p, out);
    else if (/\.(tsx?|json)$/.test(p) && !/\.(test|spec)\.tsx?$/.test(p)) out.push(p);
  }
  return out;
}

const IMPORT_RE = /(?:import|export)\s[^'"]*?from\s+['"](\.{1,2}\/[^'"]+)['"]|import\(\s*['"](\.{1,2}\/[^'"]+)['"]\s*\)/g;

/** Repo-relative paths of the local modules a file imports. */
function localImports(file: string, src: string, known: Set<string>): string[] {
  const out: string[] = [];
  for (const m of src.matchAll(IMPORT_RE)) {
    const base = resolve(file, '..', m[1] ?? m[2]);
    for (const cand of [base, `${base}.ts`, `${base}.tsx`, join(base, 'index.ts'), join(base, 'index.tsx')]) {
      const rel = cand.slice(ROOT.length + 1);
      if (known.has(rel)) { out.push(rel); break; }
    }
  }
  return out;
}

/** Views (.tsx) that render Qur'an text, with the reason each was detected. */
function findVerseTextViews(): Map<string, { reason: string; attributed: boolean }> {
  const files = listSources(join(ROOT, 'frontend/src'));
  const known = new Set(files.map((f) => f.slice(ROOT.length + 1)));
  const src = new Map<string, string>();
  const imports = new Map<string, string[]>();
  for (const f of files) {
    const rel = f.slice(ROOT.length + 1);
    const text = f.endsWith('.json') ? '' : readFileSync(f, 'utf-8');
    src.set(rel, text);
    imports.set(rel, localImports(f, text, known));
  }
  // .ts modules that (transitively) carry canonical excerpts.
  const verseModules = new Set(EXCERPT_ROOTS);
  for (let changed = true; changed;) {
    changed = false;
    for (const [rel, deps] of imports) {
      if (!rel.endsWith('.ts') || verseModules.has(rel)) continue;
      if (deps.some((d) => verseModules.has(d))) { verseModules.add(rel); changed = true; }
    }
  }
  const views = new Map<string, { reason: string; attributed: boolean }>();
  for (const [rel, text] of src) {
    if (!rel.endsWith('.tsx')) continue;
    const attributed = ATTRIBUTION_PATTERN.test(text);
    const field = text.match(VERSE_FIELD_PATTERN)?.[0];
    if (field) {
      views.set(rel, { reason: `renders ${field.replace(/\($/, '()')}`, attributed });
      continue;
    }
    const via = (imports.get(rel) ?? []).find((d) => verseModules.has(d));
    if (via && !(rel in METADATA_ONLY)) views.set(rel, { reason: `imports ${via}`, attributed });
  }
  return views;
}

function checkQuranAttribution(): CheckResult {
  return check('Views that render Qur\'an text show the Tanzil attribution', () => {
    const errors: string[] = [];
    const warnings: string[] = [];
    const views = findVerseTextViews();
    for (const [rel, { reason, attributed }] of views) {
      if (attributed) continue;
      const gap = ATTRIBUTION_KNOWN_GAPS[rel];
      if (gap) warnings.push(`${rel}: ${reason} without QuranTextAttribution (known gap: ${gap})`);
      else errors.push(`${rel}: ${reason} without QuranTextAttribution`);
    }
    for (const rel of Object.keys(ATTRIBUTION_KNOWN_GAPS)) {
      const v = views.get(rel);
      if (!v || v.attributed) warnings.push(`${rel}: listed in ATTRIBUTION_KNOWN_GAPS but no longer a gap; remove it`);
    }
    for (const rel of Object.keys(METADATA_ONLY)) {
      if (!existsSync(join(ROOT, rel))) warnings.push(`${rel}: listed in METADATA_ONLY but missing; remove it`);
    }
    return { errors, warnings };
  });
}

// ---------------------------------------------------------------------------
// Qur'an excerpts: generated file matches the canonical text
// ---------------------------------------------------------------------------

function checkQuranExcerptsCurrent(): CheckResult {
  return check("Qur'an excerpts (quranExcerpts.json) rebuilt from the canonical text", () => {
    const errors: string[] = [];
    const r = spawnSync(process.execPath, [
      ...process.execArgv,
      join(ROOT, 'scripts/build-quran-excerpts.ts'),
      '--check',
    ], { encoding: 'utf-8', timeout: 60000 });
    if (r.status !== 0) {
      errors.push((r.stderr || r.stdout || 'build-quran-excerpts --check failed').trim().split('\n').slice(-3).join(' | '));
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
        errors: ['Failed to parse quran_tanzil.json as JSON'],
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
    results.push(checkDuasVerbatim(ayahs));
    results.push(checkMemorizationPhrases(ayahs));
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
    results.push(checkTafsirLicenceCrossCheck(tafsirManifest));
  } else {
    results.push({
      name: 'Tafsir sources manifest',
      passed: false,
      errors: [`Could not load ${TAFSIR_MANIFEST_PATH}`],
      warnings: [],
    });
  }

  // --- Generated Qur'an excerpts and their attribution ---
  results.push(checkQuranExcerptsCurrent());
  results.push(checkQuranAttribution());

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
