/**
 * Quranic Arabic Corpus (QAC) proper-noun lemmas + token-safe alias matching.
 *
 * Shared by:
 *   - scripts/scan-quran-entity-mentions.ts
 *   - scripts/scan-quran-story-connections.ts
 *   - scripts/validate-surah-atlas-story-refs.ts
 *   - scripts/validate-quran-story-connections.ts
 *
 * Why: substring matching on normalised ayah text produced false entity hits
 * (the divine name al-'Aziz tagged as the 'Aziz of Egypt, "صالحا" (righteous)
 * tagged as the prophet Salih, "اليهود" / "مشهود" tagged as the prophet Hud).
 * Named people, prophets and nations are now resolved from QAC `POS:PN`
 * lemma tags, which disambiguate e.g. LEM:huwd (the prophet) from LEM:huwd2
 * ("Jews"). Alias matching is kept only for descriptive aliases and works on
 * whole tokens with a whitelist of clitic prefixes.
 *
 * Input: data/raw/quranic-corpus-morphology.txt (QAC v0.4, GPL, not
 * committed — see .gitignore). Callers must handle `null` when the file is
 * absent (CI / fresh worktrees).
 *
 * No Quran text is emitted by this module.
 */

import { existsSync, readFileSync } from 'fs';
import { join, resolve } from 'path';

const ROOT = resolve(__dirname, '..');
export const QAC_PATH = join(ROOT, 'data/raw/quranic-corpus-morphology.txt');

/**
 * entityId → QAC proper-noun lemma(s). Entity ids are shared between
 * quranEntitySeeds.ts and quranStoryEntitySeeds.ts.
 *
 * Only lemmas tagged POS:PN in QAC are listed. Entities whose names QAC does
 * not tag as proper nouns (Dhul-Kifl, Dhul-Qarnayn, Bilqis, ...) fall back to
 * token-safe alias matching at reduced confidence.
 */
export const LEMMA_BY_ENTITY: Readonly<Record<string, readonly string[]>> = {
  // Prophets
  entity_prophet_adam: ['A^dam'],
  entity_prophet_idris: ['<idoriys'],
  entity_prophet_nuh: ['nuwH'],
  entity_prophet_hud: ['huwd'], // NOT huwd2 ("Jews", 2:111/135/140)
  entity_prophet_salih: ['Sa`liH2'],
  entity_prophet_ibrahim: ['<iboraAhiym'],
  entity_prophet_lut: ['luwT'],
  entity_prophet_ismail: ['<isomaAEiyl'],
  entity_prophet_ishaq: ['<isoHaAq'],
  entity_prophet_yaqub: ['yaEoquwb'],
  entity_prophet_yusuf: ['yuwsuf'],
  entity_prophet_shuayb: ['$uEayob'],
  entity_prophet_musa: ['muwsaY`'],
  entity_prophet_harun: ['ha`ruwn'],
  entity_prophet_dawud: ['daAwud'],
  entity_prophet_sulayman: ['sulayoma`n'],
  entity_prophet_ayyub: ['>ay~uwb'],
  entity_prophet_yunus: ['yuwnus'],
  entity_prophet_zakariyya: ['zakariy~aA'],
  entity_prophet_yahya: ['yaHoyaY`'],
  entity_prophet_isa: ['EiysaY', 'masiyH'],
  entity_prophet_ilyas: ['<iloyaAs'],
  entity_prophet_alyasa: ['{loyasaEa'],
  entity_prophet_muhammad: ['muHam~ad', '>aHomad'],
  // Named persons
  entity_person_maryam: ['maroyam'],
  entity_person_firawn: ['firoEawon'],
  entity_person_haman: ['ha`ma`n'],
  entity_person_qarun: ['qa`ruwn'],
  entity_person_talut: ['TaAluwt'],
  entity_person_jalut: ['jaAluwt'],
  entity_person_luqman: ['luqoma`n'],
  entity_person_imran: ['Eimora`n'],
  entity_person_iblis: ['<iboliys'],
  entity_person_zayd: ['zayod'],
  // Nations / peoples
  entity_people_aad: ['EaAd2'],
  entity_people_thamud: ['vamuwd'],
  entity_people_madyan: ['madoyan'],
  entity_people_quraysh: ['qurayo$'],
  entity_people_yajuj_majuj: ['ya>ojuwj', 'ma>ojuwj'],
  entity_people_saba: ['saba<'],
  // Places
  entity_place_makkah: ['mak~ap', 'bak~ap'],
  entity_place_madinah: ['madiynap', 'yavorib'], // PN madiynap = al-Madinah only
  entity_place_egypt: ['miSor'],
  entity_place_madyan_place: ['madoyan'],
  entity_place_saba_place: ['saba<'],
  entity_place_babylon: ['baAbil'],
  entity_place_arafat: ['Earafa`t'],
  entity_place_ahqaf: ['>aHoqaAf'],
  entity_place_kaaba: ['kaEobap'],
  // Angels
  entity_angel_jibreel: ['jiboriyl'],
  entity_angel_mikail: ['miykaY`l'],
};

export type ProperNounIndex = Map<string, Set<string>>; // lemma → {"s:a"}

let cachedIndex: ProperNounIndex | null | undefined;

/** Parse QAC and return lemma → set of "surah:ayah" for every POS:PN token. */
export function loadQacProperNounIndex(path = QAC_PATH): ProperNounIndex | null {
  if (cachedIndex !== undefined && path === QAC_PATH) return cachedIndex;
  if (!existsSync(path)) {
    if (path === QAC_PATH) cachedIndex = null;
    return null;
  }
  const idx: ProperNounIndex = new Map();
  const text = readFileSync(path, 'utf-8');
  for (const line of text.split('\n')) {
    if (!line.startsWith('(')) continue;
    const cols = line.split('\t');
    if (cols.length < 4) continue;
    const feat = cols[3];
    if (!feat.includes('POS:PN')) continue;
    const lem = /LEM:([^|]+)/.exec(feat);
    if (!lem) continue;
    const [s, a] = cols[0].slice(1, -1).split(':');
    const key = `${Number(s)}:${Number(a)}`;
    let set = idx.get(lem[1]);
    if (!set) {
      set = new Set();
      idx.set(lem[1], set);
    }
    set.add(key);
  }
  if (path === QAC_PATH) cachedIndex = idx;
  return idx;
}

/** Ayah keys ("s:a") where any lemma of `entityId` occurs, or null if unmapped / QAC missing. */
export function qacAyahsForEntity(entityId: string, idx: ProperNounIndex | null): Set<string> | null {
  const lemmas = LEMMA_BY_ENTITY[entityId];
  if (!lemmas || !idx) return null;
  const out = new Set<string>();
  for (const l of lemmas) for (const k of idx.get(l) ?? []) out.add(k);
  return out;
}

// ---------------------------------------------------------------------------
// Token-safe alias matching
// ---------------------------------------------------------------------------

/**
 * Clitic prefixes that may attach to an alias token. Order does not matter —
 * matching tests each prefix explicitly. Prefixes that end in "ال" are only
 * used when the alias itself has no article.
 */
// 'ي' / 'يا' cover the vocative particle, which the Uthmani script fuses to the noun.
const PREFIXES_PLAIN = ['', 'و', 'ف', 'ب', 'ل', 'ك', 'وب', 'فب', 'ول', 'فل', 'وك', 'فك', 'ي', 'يا'];
const PREFIXES_ARTICLE = ['ال', 'وال', 'فال', 'بال', 'كال', 'وبال', 'فبال'];

/** Return true when `token` is `alias` with an allowed clitic prefix (or none). */
export function tokenMatchesAlias(token: string, alias: string): boolean {
  if (!token || !alias) return false;
  for (const p of PREFIXES_PLAIN) {
    if (token === p + alias) return true;
  }
  if (alias.startsWith('ال')) {
    // li + al- contracts to "لل": لل + rest-of-alias, optionally with و/ف.
    const rest = alias.slice(2);
    for (const p of ['لل', 'ولل', 'فلل']) {
      if (token === p + rest) return true;
    }
  } else {
    for (const p of PREFIXES_ARTICLE) {
      if (token === p + alias) return true;
    }
    for (const p of ['لل', 'ولل', 'فلل']) {
      if (token === p + alias) return true;
    }
  }
  return false;
}

/** Split a normalised ayah into word tokens (pause marks already stripped). */
export function tokenise(normAyah: string): string[] {
  return normAyah.split(/\s+/).filter((t) => t.length > 0);
}

/**
 * Count whole-token occurrences of a (possibly multi-word) normalised alias
 * in a tokenised ayah. Only the first alias token may carry a clitic prefix;
 * the remaining tokens must match exactly.
 */
export function countAliasOccurrences(tokens: string[], normAlias: string): number {
  const parts = normAlias.split(/\s+/).filter(Boolean);
  if (parts.length === 0) return 0;
  let n = 0;
  for (let i = 0; i + parts.length <= tokens.length; i++) {
    if (!tokenMatchesAlias(tokens[i], parts[0])) continue;
    let ok = true;
    for (let k = 1; k < parts.length; k++) {
      if (tokens[i + k] !== parts[k]) {
        ok = false;
        break;
      }
    }
    if (ok) n++;
  }
  return n;
}

// ---------------------------------------------------------------------------
// Ayah-scope helpers
// ---------------------------------------------------------------------------

export interface AyahScope {
  /** Accept hits only in these surahs. */
  surahs?: number[];
  /** Accept hits only inside these [surah, ayahStart, ayahEnd] ranges. */
  ranges?: Array<[number, number, number]>;
}

export function inScope(scope: AyahScope | undefined, surah: number, ayah: number): boolean {
  if (!scope) return true;
  if (scope.surahs && !scope.surahs.includes(surah)) return false;
  if (scope.ranges && !scope.ranges.some(([s, a, b]) => s === surah && ayah >= a && ayah <= b)) {
    return false;
  }
  return true;
}
