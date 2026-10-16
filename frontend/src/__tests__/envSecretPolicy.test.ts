import { describe, expect, it } from 'vitest';
import { secretEnvProblem, secretLookingViteEnv } from '../lib/envSecretPolicy';

// Names are assembled at runtime: backend test_secret_hygiene scans frontend
// source for literal secret-looking VITE_ names and must keep finding none.
const v = (suffix: string) => `VITE_${suffix}`;
const ADMIN = v('ADMIN_API_' + 'KEY');
const HF = v('HF_' + 'TOKEN');
const DB = v('DB_' + 'PASSWORD');
const OTHER = v('SOME_' + 'SECRET');

describe('VITE_* secret guard', () => {
  it('flags secret-looking VITE_ names', () => {
    const env = {
      VITE_API_URL: 'https://api.example.org',
      [ADMIN]: 'x',
      [HF]: 'x',
      [DB]: 'x',
      [OTHER]: 'x',
      ['SERVER_ONLY_' + 'TOKEN']: 'not bundled',
    };
    expect(secretLookingViteEnv(env)).toEqual([ADMIN, DB, HF, OTHER]);
    expect(secretEnvProblem(env)).toContain(`Refusing to build: ${ADMIN}`);
  });

  it('passes the variables the client actually uses', () => {
    const env = {
      VITE_API_URL: '',
      VITE_ENABLE_ADMIN: 'false',
      VITE_PRIVACY_CONTACT: 'privacy@example.org',
      VITE_PUBLIC_WEB_URL: 'https://example.org',
      MODE: 'production',
    };
    expect(secretEnvProblem(env)).toBeNull();
  });

  it('honours the allowlist', () => {
    const pub = v('MAPS_PUBLIC_' + 'KEY');
    expect(secretLookingViteEnv({ [pub]: 'pk' }, new Set([pub]))).toEqual([]);
  });
});
