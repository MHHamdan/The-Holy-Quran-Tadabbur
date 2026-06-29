/**
 * Quranic Calls Atlas — Type Definitions
 *
 * Models every call/address detected in the Quran:
 * direct vocatives (يا), supplication forms (ربنا/ربي),
 * and indirect address patterns.
 *
 * IMPORTANT: All inferred classifications default to needs_review = true
 * and humanReviewRequired = true. Only exact pattern matches may have
 * higher confidence, but never skip review for theological classification.
 */

export type CallPattern =
  | 'ya_direct'           // يا + specific name/title
  | 'ya_ayyuhal'          // يا أيها (masculine)
  | 'ya_ayatuha'          // يا أيتها (feminine)
  | 'ya_bani'             // يا بني / يا بني إسرائيل / يا بني آدم
  | 'ya_qawmi'            // يا قوم / يا قومنا
  | 'ya_ibadi'            // يا عبادي / يا عباد
  | 'ya_ahl'              // يا أهل الكتاب / يا أهل يثرب
  | 'ya_rabbi'            // يا رب (address to Allah)
  | 'ya_abati'            // يا أبت (address to father)
  | 'ya_bunayya'          // يا بني (address to son — singular)
  | 'ya_prophet_name'     // يا موسى / يا عيسى / يا مريم / etc.
  | 'ya_lament'           // يا ويلتى / يا حسرة / يا أسفى (rhetorical lament)
  | 'ya_wish'             // يا ليت / يا ليتني (rhetorical wish)
  | 'supplication'        // ربنا / ربي / رب (without يا) — address to Allah
  | 'indirect_address'    // Inferred address without explicit vocative
  | 'dialogue_address'    // Address within story dialogue context
  | 'unknown';

export type CallerType =
  | 'allah'
  | 'prophet'
  | 'angel'
  | 'believer'
  | 'disbeliever'
  | 'people_group'
  | 'family_member'
  | 'jinn'
  | 'narrative_speaker'
  | 'unknown';

export type AddresseeType =
  | 'believers'
  | 'mankind'
  | 'disbelievers'
  | 'people_of_book'
  | 'bani_israel'
  | 'prophet'
  | 'specific_person'
  | 'people_or_nation'
  | 'family_member'
  | 'soul'
  | 'jinn'
  | 'allah'
  | 'unknown';

export type CallFunction =
  | 'instruction'
  | 'warning'
  | 'reminder'
  | 'mercy'
  | 'comfort'
  | 'invitation'
  | 'rebuke'
  | 'question'
  | 'supplication'
  | 'prohibition'
  | 'command'
  | 'promise'
  | 'threat'
  | 'dialogue'
  | 'storytelling'
  | 'lament'
  | 'needs_review';

export type CallTone =
  | 'gentle'
  | 'warning'
  | 'honoring'
  | 'urgent'
  | 'rebuking'
  | 'comforting'
  | 'neutral'
  | 'needs_review';

export type ReviewStatus = 'verified' | 'needs_review' | 'rejected';

export type EvidenceType =
  | 'quran_text_pattern'
  | 'morphology_vocative'
  | 'entity_graph'
  | 'prophet_graph'
  | 'story_graph'
  | 'topic_graph'
  | 'tafsir_source'
  | 'manual_seed'
  | 'needs_review';

export interface EvidenceReference {
  surahNumber: number;
  ayahStart: number;
  ayahEnd?: number;
  sourceIds: string[];
  evidenceType: EvidenceType;
}

export interface CallerInfo {
  callerType: CallerType;
  callerEntityId?: string;
  labelArabic?: string;
  labelEnglish?: string;
  confidence: number;       // 0–1
  reviewStatus: ReviewStatus;
}

export interface AddresseeInfo {
  addresseeType: AddresseeType;
  entityId?: string;
  labelArabic: string;
  labelEnglish: string;
  confidence: number;       // 0–1
  reviewStatus: ReviewStatus;
}

export interface QuranicCall {
  callId: string;                  // e.g. "call_2_183_0"
  surahNumber: number;
  ayahNumber: number;
  ayahReference: string;           // e.g. "2:183"
  surahNameAr: string;
  surahNameEn: string;
  ayahTextUthmani: string;         // Full Uthmani text — never modified
  callText?: string;               // Matched phrase (stripped of diacritics for display)
  callTextUthmani?: string;        // Matched phrase in Uthmani text
  callPattern: CallPattern;
  caller: CallerInfo;
  addressee: AddresseeInfo;
  callFunction: CallFunction;
  tone: CallTone;
  relatedTopics: string[];
  relatedEntities: string[];
  relatedStories: string[];
  relatedProphets: string[];
  evidenceReferences: EvidenceReference[];
  confidence: number;              // 0–1 — pattern-match confidence only
  reviewStatus: ReviewStatus;
  humanReviewRequired: boolean;    // Always true for inferred classifications
  warnings: string[];
}

// ─── Atlas output ─────────────────────────────────────────────────────────────

export interface QuranicCallsAtlas {
  version: string;
  generatedAt: string;
  totalCalls: number;
  totalAyahsWithCalls: number;
  statistics: QuranicCallsStatistics;
  calls: QuranicCall[];
}

export interface QuranicCallsStatistics {
  byPattern: Record<CallPattern, number>;
  byAddresseeType: Record<AddresseeType, number>;
  byCallerType: Record<CallerType, number>;
  byCallFunction: Record<CallFunction, number>;
  bySurah: Record<number, number>;              // surahNumber → count
  topSurahs: Array<{ surahNumber: number; surahNameEn: string; count: number }>;
  directYaCalls: number;
  supplicationCalls: number;
  indirectCalls: number;
  needsReview: number;
  verified: number;
  totalWarnings: number;
}

// ─── Classified output ────────────────────────────────────────────────────────

export interface QuranicCallClassification extends QuranicCall {
  classifiedAt: string;
  classificationMethod: 'rule_based' | 'topic_signal' | 'entity_signal' | 'unclassified';
  classificationSignals: string[];
}

export interface QuranicCallsClassified {
  version: string;
  classifiedAt: string;
  totalClassified: number;
  calls: QuranicCallClassification[];
  classificationSummary: {
    byFunction: Record<CallFunction, number>;
    byTone: Record<CallTone, number>;
    unclassified: number;
    highConfidence: number;   // confidence > 0.7
    lowConfidence: number;    // confidence <= 0.4
  };
}

// ─── Relation graph ───────────────────────────────────────────────────────────

export type NodeType = 'call' | 'ayah' | 'surah' | 'caller' | 'addressee' | 'topic' | 'prophet' | 'story' | 'entity';
export type EdgeType =
  | 'CALL_IN_AYAH'
  | 'CALL_IN_SURAH'
  | 'CALLER'
  | 'ADDRESSEE'
  | 'CALL_FUNCTION'
  | 'RELATED_TOPIC'
  | 'RELATED_STORY'
  | 'RELATED_PROPHET'
  | 'SAME_ADDRESSEE'
  | 'SAME_CALL_PATTERN'
  | 'SAME_FUNCTION'
  | 'NEEDS_REVIEW';

export interface GraphNode {
  nodeId: string;
  nodeType: NodeType;
  label: string;
  labelAr?: string;
  metadata: Record<string, unknown>;
}

export interface GraphEdge {
  edgeId: string;
  edgeType: EdgeType;
  sourceId: string;
  targetId: string;
  confidence: number;
  reviewStatus: ReviewStatus;
  humanReviewRequired: boolean;
  evidenceReferences: EvidenceReference[];
  warnings: string[];
}

export interface QuranicCallRelationGraph {
  version: string;
  generatedAt: string;
  totalNodes: number;
  totalEdges: number;
  nodes: GraphNode[];
  edges: GraphEdge[];
  summary: {
    nodesByType: Record<NodeType, number>;
    edgesByType: Record<EdgeType, number>;
    needsReview: number;
  };
}

// ─── UI helpers ───────────────────────────────────────────────────────────────

export interface CallFilterState {
  surah?: number;
  callPattern?: CallPattern;
  callerType?: CallerType;
  addresseeType?: AddresseeType;
  callFunction?: CallFunction;
  tone?: CallTone;
  reviewStatus?: ReviewStatus;
  directOnly?: boolean;
  search?: string;
}

export const ADDRESSEE_LABELS: Record<AddresseeType, { ar: string; en: string }> = {
  believers:       { ar: 'الذين آمنوا', en: 'Believers' },
  mankind:         { ar: 'الناس',       en: 'Mankind' },
  disbelievers:    { ar: 'الكافرون',   en: 'Disbelievers' },
  people_of_book:  { ar: 'أهل الكتاب', en: 'People of the Book' },
  bani_israel:     { ar: 'بني إسرائيل', en: 'Bani Israel' },
  prophet:         { ar: 'النبي / الرسول', en: 'Prophet / Messenger' },
  specific_person: { ar: 'شخص بعينه',  en: 'Specific Person' },
  people_or_nation:{ ar: 'قوم / أمة',  en: 'People / Nation' },
  family_member:   { ar: 'فرد من الأسرة', en: 'Family Member' },
  soul:            { ar: 'النفس',       en: 'Soul' },
  jinn:            { ar: 'الجن',        en: 'Jinn' },
  allah:           { ar: 'الله',        en: 'Allah' },
  unknown:         { ar: 'غير محدد',    en: 'Unknown' },
};

export const CALLER_LABELS: Record<CallerType, { ar: string; en: string }> = {
  allah:              { ar: 'الله',        en: 'Allah' },
  prophet:            { ar: 'نبي',         en: 'Prophet' },
  angel:              { ar: 'ملك',         en: 'Angel' },
  believer:           { ar: 'مؤمن',        en: 'Believer' },
  disbeliever:        { ar: 'كافر',        en: 'Disbeliever' },
  people_group:       { ar: 'جماعة',       en: 'People Group' },
  family_member:      { ar: 'فرد من الأسرة', en: 'Family Member' },
  jinn:               { ar: 'جني',         en: 'Jinn' },
  narrative_speaker:  { ar: 'صوت سردي',    en: 'Narrative Speaker' },
  unknown:            { ar: 'غير محدد',    en: 'Unknown' },
};

export const CALL_FUNCTION_LABELS: Record<CallFunction, { ar: string; en: string }> = {
  instruction:  { ar: 'توجيه',    en: 'Instruction' },
  warning:      { ar: 'تحذير',    en: 'Warning' },
  reminder:     { ar: 'تذكير',    en: 'Reminder' },
  mercy:        { ar: 'رحمة',     en: 'Mercy' },
  comfort:      { ar: 'تسلية',    en: 'Comfort' },
  invitation:   { ar: 'دعوة',     en: 'Invitation' },
  rebuke:       { ar: 'توبيخ',    en: 'Rebuke' },
  question:     { ar: 'سؤال',     en: 'Question' },
  supplication: { ar: 'دعاء',     en: 'Supplication' },
  prohibition:  { ar: 'نهي',      en: 'Prohibition' },
  command:      { ar: 'أمر',      en: 'Command' },
  promise:      { ar: 'وعد',      en: 'Promise' },
  threat:       { ar: 'وعيد',     en: 'Threat' },
  dialogue:     { ar: 'حوار',     en: 'Dialogue' },
  storytelling: { ar: 'سرد',      en: 'Storytelling' },
  lament:       { ar: 'نداء حزن', en: 'Lament' },
  needs_review: { ar: 'تحتاج مراجعة', en: 'Needs Review' },
};
