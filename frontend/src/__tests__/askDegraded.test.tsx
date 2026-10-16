import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { askErrorCopy, classifyAskError, classifyAskErrorBody } from '../components/ask/askErrors';
import { consensusLabel } from '../components/ask/consensus';
import { ChatMessage, type ChatMessageData } from '../components/ask/ChatMessage';
import { VersesSection } from '../components/ask/VersesSection';
import type { RAGResponse, RelatedVerse } from '../lib/api';

describe('classifyAskError', () => {
  it('maps the API AI-failure envelope to its specific kind', () => {
    const down = { response: { status: 503, data: { ok: false, error: { code: 'service_unavailable' } } } };
    const quota = { response: { status: 429, data: { ok: false, error: { code: 'ai_quota_exceeded' } } } };
    expect(classifyAskError(down)).toBe('ai_unavailable');
    expect(classifyAskError(quota)).toBe('ai_quota');
  });

  it('treats a bare gateway 502/503/504 as the AI service being unavailable', () => {
    expect(classifyAskError({ response: { status: 504, data: '<html>' } })).toBe('ai_unavailable');
    expect(classifyAskError({ response: { status: 503 } })).toBe('ai_unavailable');
  });

  it('tells the rate limiter apart from the AI quota', () => {
    expect(classifyAskError({ response: { status: 429, data: { detail: { code: 'x' } } } })).toBe('rate_limited');
  });

  it('classifies a request with no response as a network failure', () => {
    expect(classifyAskError({ code: 'ERR_NETWORK', request: {} })).toBe('network');
  });

  it('leaves other failures generic', () => {
    expect(classifyAskError({ response: { status: 500, data: { ok: false } } })).toBe('generic');
    expect(classifyAskError(new Error('boom'))).toBe('generic');
    expect(classifyAskErrorBody({ ok: false, error_id: 'abc' })).toBe('generic');
  });

  it('has natural copy in both languages for every specific kind', () => {
    for (const kind of ['ai_unavailable', 'ai_quota', 'rate_limited', 'network'] as const) {
      const ar = askErrorCopy(kind, 'ar');
      const en = askErrorCopy(kind, 'en');
      expect(ar?.title).toMatch(/[؀-ۿ]/);
      expect(ar?.body).not.toMatch(/[A-Za-z]/);
      expect(en?.title).toMatch(/^[\x20-\x7E’]+$/);
    }
    expect(askErrorCopy('generic', 'en')).toBeNull();
  });
});

function renderMessage(message: ChatMessageData, language: 'ar' | 'en') {
  return renderToStaticMarkup(
    <MemoryRouter>
      <ChatMessage message={message} language={language} />
    </MemoryRouter>,
  );
}

describe('ChatMessage degraded states', () => {
  it('shows the bilingual AI-unavailable notice for a 503, not the generic error', () => {
    const msg: ChatMessageData = {
      id: 'a', role: 'assistant', content: '', timestamp: new Date(),
      error: 'An error occurred while processing your question. Please try again.',
      errorKind: 'ai_unavailable',
    };
    const ar = renderMessage(msg, 'ar');
    expect(ar).toContain('خدمة الذكاء الاصطناعي غير متاحة مؤقتاً');
    expect(ar).not.toContain('حدث خطأ');
    const en = renderMessage(msg, 'en');
    expect(en).toContain('The AI service is temporarily unavailable');
    expect(en).not.toContain('An Error Occurred');
  });

  it('keeps the generic error display for unclassified failures', () => {
    const msg: ChatMessageData = {
      id: 'b', role: 'assistant', content: '', timestamp: new Date(), error: 'Server error', errorKind: 'generic',
    };
    expect(renderMessage(msg, 'en')).toContain('An Error Occurred');
  });

  it('shows no confidence chip or "summary" mode on a direct source digest, and localizes its note', () => {
    const response = {
      answer: 'نص', citations: [], status: 'answered', answer_kind: 'source_digest',
      answer_mode: 'tafsir_summary', confidence: 0.95, intent: 'verse_meaning', warnings: [],
      scholarly_consensus: 'Direct tafsir lookup - no synthesis required', processing_time_ms: 10,
    } as unknown as RAGResponse;
    const msg: ChatMessageData = { id: 'c', role: 'assistant', content: '', timestamp: new Date(), response };
    const ar = renderMessage(msg, 'ar');
    expect(ar).not.toMatch(/95% <span[^>]*>ثقة/);
    expect(ar).not.toContain('ملخص تفسيري');
    expect(ar).not.toContain('Direct tafsir lookup');
    expect(ar).toContain('دون تلخيص');
    expect(renderMessage(msg, 'en')).not.toMatch(/95% <span[^>]*>confidence/);
  });
});

describe('consensusLabel', () => {
  it('localizes known labels and hides unknown English text in the Arabic UI', () => {
    expect(consensusLabel('Direct tafsir lookup - no synthesis required', 'en')).toMatch(/without a summary/);
    expect(consensusLabel('disputed', 'ar')).toMatch(/[؀-ۿ]/);
    expect(consensusLabel('some english note', 'ar')).toBeNull();
    expect(consensusLabel('some english note', 'en')).toBe('some english note');
    expect(consensusLabel(null, 'en')).toBeNull();
  });
});

describe('VersesSection attribution', () => {
  const verse = {
    sura_no: 2, aya_no: 153, verse_reference: '2:153', text_ar: 'x', text_en: '',
    sura_name_ar: 'البقرة', sura_name_en: 'Al-Baqarah', relevance_score: 0.5,
  } as unknown as RelatedVerse;

  it.each(['ar', 'en'] as const)('credits Tanzil with a link wherever verse text is shown (%s)', (language) => {
    const html = renderToStaticMarkup(
      <MemoryRouter>
        <VersesSection verses={[verse]} language={language} />
      </MemoryRouter>,
    );
    expect(html).toContain('href="https://tanzil.net"');
    expect(html).toContain('CC BY 3.0');
  });
});
