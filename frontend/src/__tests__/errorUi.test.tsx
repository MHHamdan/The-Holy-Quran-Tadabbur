import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { ErrorFallback } from '../components/ui/ErrorBoundary';
import { hasUsefulRequestId, parseAPIError } from '../components/common/ErrorPanel';
import { translations } from '../i18n/translations';

describe('ErrorFallback', () => {
  const error = new Error("Cannot read properties of undefined (reading 'storyId')");

  it('renders Arabic copy, right-to-left, without the raw error', () => {
    const html = renderToStaticMarkup(<ErrorFallback error={error} onReset={() => undefined} language="ar" showDetails={false} />);
    expect(html).toContain('dir="rtl"');
    expect(html).toContain(translations.err_boundary_title.ar);
    expect(html).toContain(translations.err_boundary_retry.ar);
    expect(html).toContain(translations.err_boundary_home.ar);
    expect(html).not.toContain('storyId');
    expect(html).not.toContain('Something went wrong');
  });

  it('renders English copy left-to-right', () => {
    const html = renderToStaticMarkup(<ErrorFallback error={error} language="en" showDetails={false} />);
    expect(html).toContain('dir="ltr"');
    expect(html).toContain(translations.err_boundary_title.en);
    expect(html).not.toContain('storyId');
  });

  it('keeps the raw error inside the collapsed details block when details are enabled', () => {
    const html = renderToStaticMarkup(<ErrorFallback error={error} language="ar" showDetails />);
    expect(html).toContain('<details');
    expect(html).toContain('storyId');
    expect(html).toContain(translations.err_boundary_details.ar);
  });

  it('has a compact panel variant', () => {
    const html = renderToStaticMarkup(<ErrorFallback error={error} variant="panel" language="ar" showDetails={false} />);
    expect(html).toContain(translations.panel_unavailable.ar);
    expect(html).not.toContain('storyId');
  });
});

describe('parseAPIError', () => {
  it('maps a network failure to bilingual copy, not the transport message', () => {
    const e = parseAPIError({ message: 'Network Error', code: 'ERR_NETWORK' });
    expect(e?.code).toBe('network_error');
    expect(e?.message).toBe(translations.err_network.en);
    expect(e?.message_ar).toBe(translations.err_network.ar);
    expect(e?.message).not.toContain('Network Error');
  });

  it('maps a timeout', () => {
    const e = parseAPIError({ message: 'timeout of 30000ms exceeded', code: 'ECONNABORTED' });
    expect(e?.code).toBe('timeout');
    expect(e?.message).not.toContain('30000');
  });

  it('turns a FastAPI 422 array detail into renderable strings', () => {
    const e = parseAPIError({
      response: { data: { detail: [{ loc: ['query', 'limit'], msg: 'Input should be a valid integer', type: 'int_parsing' }] } },
    });
    expect(typeof e?.message).toBe('string');
    expect(e?.code).toBe('validation_error');
    expect(e?.message_ar).toBe(translations.err_request_unprocessed.ar);
    expect(e?.details).toEqual([{ field: 'limit', message: 'Input should be a valid integer' }]);
  });

  it('keeps a string detail', () => {
    const e = parseAPIError({ response: { data: { detail: 'Verse 999:1 not found' } } });
    expect(e?.message).toBe('Verse 999:1 not found');
  });

  it('passes the structured envelope through', () => {
    const env = { code: 'not_found', message: 'Not found', message_ar: 'غير موجود', request_id: 'abc123' };
    expect(parseAPIError({ response: { data: { ok: false, error: env } } })).toEqual(env);
  });
});

describe('hasUsefulRequestId', () => {
  it('hides placeholder ids', () => {
    expect(hasUsefulRequestId('N/A')).toBe(false);
    expect(hasUsefulRequestId('unknown')).toBe(false);
    expect(hasUsefulRequestId('')).toBe(false);
    expect(hasUsefulRequestId('3f2a9c')).toBe(true);
  });
});
