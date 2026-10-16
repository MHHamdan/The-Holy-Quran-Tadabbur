import { describe, expect, it } from 'vitest';
import { secretEnvProblem, secretLookingViteEnv } from '../lib/envSecretPolicy';

describe('VITE_* secret guard', () => {
  it('flags secret-looking VITE_ names', () => {
    const env = {
      VITE_API_URL: 'https://api.example.org',
      VITE_ADMIN_API_KEY: 'x',
      VITE_HF_TOKEN: 'x',
      VITE_DB_PASSWORD: 'x',
      VITE_SOME_SECRET: 'x',
      HF_TOKEN: 'server-only, not bundled',
    };
    expect(secretLookingViteEnv(env)).toEqual([
      'VITE_ADMIN_API_KEY',
      'VITE_DB_PASSWORD',
      'VITE_HF_TOKEN',
      'VITE_SOME_SECRET',
    ]);
    expect(secretEnvProblem(env)).toMatch(/Refusing to build: VITE_ADMIN_API_KEY/);
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
    expect(secretLookingViteEnv({ VITE_MAPS_PUBLIC_KEY: 'pk' }, new Set(['VITE_MAPS_PUBLIC_KEY']))).toEqual([]);
  });
});
