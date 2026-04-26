module.exports = {
  root: true,
  env: { browser: true, es2020: true },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react-hooks/recommended',
  ],
  ignorePatterns: ['dist', 'e2e', '.eslintrc.cjs', 'node_modules'],
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
  },
  plugins: ['react-refresh'],
  rules: {
    // react-refresh: HMR hint — off because this codebase intentionally mixes
    // constant exports (API objects, types) with component files throughout.
    'react-refresh/only-export-components': 'off',

    // exhaustive-deps: off because all useEffect hooks that depend on async
    // "load*" functions are intentionally written with empty deps (run-once on mount).
    // Wrapping each function in useCallback would be a broad refactor, not a lint fix.
    'react-hooks/exhaustive-deps': 'off',

    // no-explicit-any: off for now — the pre-existing codebase uses `any` at
    // API boundary points (catch blocks, dynamic JSON, WebSocket data).
    // Address incrementally in Phase 2 type-safety improvements.
    '@typescript-eslint/no-explicit-any': 'off',

    // Unused variables — keep as error but allow underscore-prefixed names
    // and caught errors named _err or similar.
    '@typescript-eslint/no-unused-vars': ['error', {
      varsIgnorePattern: '^_',
      argsIgnorePattern: '^_',
      caughtErrorsIgnorePattern: '^_',
    }],
  },
};
