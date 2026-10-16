import { describe, expect, it } from 'vitest';
import { apiUrlProblem, canonicalApiMatcher, unreachableHostReason } from '../lib/buildPolicy';

describe('mobile release API-URL guard', () => {
  it.each([
    'https://10.0.2.2',
    'https://10.1.2.3:8443',
    'https://172.16.0.5',
    'https://172.31.255.1',
    'https://192.168.1.20',
    'https://169.254.10.1',
    'https://tadabbur.local',
    'https://api',
    'https://8.8.8.8',
    'https://[fd00::1]',
    'https://localhost:8000',
  ])('refuses %s for --mode mobile', (url) => {
    expect(apiUrlProblem('mobile', url)).toMatch(/cannot reach|loopback/);
  });

  it('accepts a public https domain for --mode mobile', () => {
    expect(apiUrlProblem('mobile', 'https://api.tadabbur.example.org')).toBeNull();
    // 172.32/12 is outside the private block, but a bare IP is still refused.
    expect(unreachableHostReason('172.32.0.1')).toMatch(/bare IP/);
    expect(unreachableHostReason('api.example.org')).toBeNull();
  });

  it('still allows emulator/LAN hosts in --mode mobile-dev', () => {
    expect(apiUrlProblem('mobile-dev', 'http://10.0.2.2:8000')).toBeNull();
    expect(apiUrlProblem('mobile-dev', 'http://192.168.1.20:19800')).toBeNull();
  });
});

describe('service-worker canonical API matcher', () => {
  const req = { method: 'GET' } as Request;
  const at = (href: string, sameOrigin: boolean) => ({ url: new URL(href), request: req, sameOrigin });

  it('caches canonical paths on the same origin only when no API origin is configured', () => {
    const match = canonicalApiMatcher('');
    expect(match(at('https://app.example.org/api/v1/quran/verses/2/255', true))).toBe(true);
    expect(match(at('https://evil.example.com/api/v1/quran/verses/2/255', false))).toBe(false);
  });

  it('also caches the configured API origin, and nothing else cross-origin', () => {
    const match = canonicalApiMatcher('https://api.example.org/');
    expect(match(at('https://api.example.org/api/v1/duas', false))).toBe(true);
    expect(match(at('https://other.example.org/api/v1/duas', false))).toBe(false);
  });

  it('never caches personal or AI endpoints, or non-GET requests', () => {
    const match = canonicalApiMatcher('');
    expect(match(at('https://app.example.org/api/v1/rag/ask', true))).toBe(false);
    expect(match({ url: new URL('https://app.example.org/api/v1/duas'), request: { method: 'POST' } as Request, sameOrigin: true })).toBe(false);
  });

  it('serialises without closures (workbox inlines it into sw.js)', () => {
    const src = canonicalApiMatcher('https://api.example.org').toString();
    expect(src).toContain('"https://api.example.org"');
    const revived = new Function(`return (${src})`)() as ReturnType<typeof canonicalApiMatcher>;
    expect(revived(at('https://api.example.org/api/v1/quran/metadata', false))).toBe(true);
  });
});
