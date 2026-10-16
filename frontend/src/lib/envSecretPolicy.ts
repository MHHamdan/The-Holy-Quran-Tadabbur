/**
 * Every VITE_* variable is inlined into the client bundle, which anyone can
 * read. A name that looks like a credential (KEY, TOKEN, SECRET, PASSWORD,
 * PASSWD, PRIVATE, CREDENTIAL) therefore fails the build, unless it is listed
 * here as a value that is public by design. Server secrets (the Hugging Face
 * token, the admin API key) belong in the backend environment, never under a
 * VITE_ name.
 */
export const PUBLIC_VITE_NAMES_ALLOWLIST: ReadonlySet<string> = new Set<string>([]);

const SECRET_LOOKING = /^VITE_.*(KEY|TOKEN|SECRET|PASSWORD|PASSWD|PRIVATE|CREDENTIAL)/i;

/** Names of VITE_* variables that look secret and are not allowlisted. */
export function secretLookingViteEnv(
  env: Record<string, unknown>,
  allowlist: ReadonlySet<string> = PUBLIC_VITE_NAMES_ALLOWLIST,
): string[] {
  return Object.keys(env)
    .filter((name) => SECRET_LOOKING.test(name) && !allowlist.has(name))
    .sort();
}

export function secretEnvProblem(env: Record<string, unknown>): string | null {
  const names = secretLookingViteEnv(env);
  if (names.length === 0) return null;
  return (
    `Refusing to build: ${names.join(', ')} would be bundled into the public client. ` +
    'Remove it from frontend/.env* and the build environment (server secrets stay on the backend), ' +
    'or, if the value is public by design, add the name to PUBLIC_VITE_NAMES_ALLOWLIST in src/lib/envSecretPolicy.ts.'
  );
}
