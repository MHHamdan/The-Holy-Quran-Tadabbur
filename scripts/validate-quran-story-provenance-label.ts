#!/usr/bin/env npx tsx
/**
 * Render test for frontend/src/components/common/ProvenanceLabel.tsx
 * (the frontend has no vitest/RTL setup, so this renders to static markup).
 *
 * Asserts, for ar and en:
 *   - the label text is in the active language,
 *   - each text span carries the matching dir/lang attributes,
 *   - the explanation disclosure is present (non-compact),
 *   - tafsir_retrieved resolves the registry title instead of a raw id,
 *   - no raw kind token leaks into visible text.
 *
 * Exit 0 on success, 1 on any failure.
 */
import { createRequire } from 'module';
import { join, resolve } from 'path';

const ROOT = resolve(__dirname, '..');
const req = createRequire(join(ROOT, 'frontend', 'package.json'));
const React = req('react') as typeof import('react');
const { renderToStaticMarkup } = req('react-dom/server') as typeof import('react-dom/server');

async function main(): Promise<void> {
  // tsx compiles the .tsx with the classic JSX runtime when run from the repo
  // root (no root tsconfig), which expects a global React.
  (globalThis as unknown as { React: typeof React }).React = React;
  const mod = await import('../frontend/src/components/common/ProvenanceLabel');
  const { ProvenanceLabel, PROVENANCE_LABELS } = mod;
  const errors: string[] = [];
  const check = (cond: boolean, msg: string) => {
    if (!cond) errors.push(msg);
  };

  for (const kind of Object.keys(PROVENANCE_LABELS) as Array<keyof typeof PROVENANCE_LABELS>) {
    for (const language of ['ar', 'en'] as const) {
      const html = renderToStaticMarkup(
        React.createElement(ProvenanceLabel, { kind, language, status: 'needs_review' }),
      );
      const dir = language === 'ar' ? 'rtl' : 'ltr';
      const esc = (t: string) => t.replace(/&/g, '&amp;').replace(/'/g, '&#x27;').replace(/"/g, '&quot;');
      check(html.includes(esc(PROVENANCE_LABELS[kind].label[language])), `${kind}/${language}: label text missing`);
      check(html.includes(`dir="${dir}"`) && html.includes(`lang="${language}"`), `${kind}/${language}: dir/lang missing`);
      check(!html.includes(language === 'ar' ? 'dir="ltr"' : 'dir="rtl"'), `${kind}/${language}: wrong-direction span`);
      check(html.includes('<details') && html.includes(esc(PROVENANCE_LABELS[kind].explain[language])), `${kind}/${language}: explanation missing`);
      check(html.includes(language === 'ar' ? 'بانتظار المراجعة' : 'Awaiting review'), `${kind}/${language}: status label missing`);
      const visible = html.replace(/<[^>]+>/g, ' ');
      check(!visible.includes(kind), `${kind}/${language}: raw kind token visible`);
    }
  }

  const compact = renderToStaticMarkup(React.createElement(ProvenanceLabel, { kind: 'analytical', language: 'en', compact: true }));
  check(!compact.includes('<details'), 'compact label must not render the disclosure');

  const tafsir = renderToStaticMarkup(
    React.createElement(ProvenanceLabel, { kind: 'tafsir_retrieved', language: 'en', sourceId: 'ibn_kathir_en' }),
  );
  check(!tafsir.replace(/<[^>]+>/g, ' ').includes('ibn_kathir_en'), 'tafsir_retrieved shows a raw source id');
  check(/Ibn Kathir/i.test(tafsir), 'tafsir_retrieved does not show the registry title');

  if (errors.length) {
    console.error(`ProvenanceLabel render checks FAILED (${errors.length}):`);
    for (const e of errors) console.error('  -', e);
    process.exit(1);
  }
  console.log('ProvenanceLabel render checks passed (5 kinds x 2 languages + compact + tafsir title).');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
