import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { activeTabFor, allNavPaths, isReaderRoute, TABS } from '../components/layout/navConfig';
import { translations } from '../i18n/translations';

const appSource = readFileSync(resolve(__dirname, '../App.tsx'), 'utf8');

/** Route patterns declared in App.tsx (path="..."). */
const routePaths = [...appSource.matchAll(/path="([^"]+)"/g)].map((m) => m[1]);

function hasRoute(path: string): boolean {
  return routePaths.some((r) => {
    if (r === '*') return false;
    const re = new RegExp(`^${r.replace(/:[^/]+/g, '[^/]+')}$`);
    return re.test(path);
  });
}

describe('navigation config', () => {
  it('has exactly five tabs with bilingual labels', () => {
    expect(TABS.map((t) => t.id)).toEqual(['read', 'explore', 'tadabbur', 'memorise', 'more']);
    for (const tab of TABS) {
      expect(translations[tab.labelKey]?.ar).toBeTruthy();
      expect(translations[tab.labelKey]?.en).toBeTruthy();
    }
  });

  it('only links to routes that exist', () => {
    for (const path of allNavPaths()) {
      expect(hasRoute(path), `missing route for ${path}`).toBe(true);
    }
  });

  it('keeps developer and admin pages out of user navigation', () => {
    const paths = allNavPaths();
    expect(paths).not.toContain('/status');
    expect(paths.some((p) => p.startsWith('/admin'))).toBe(false);
    expect(paths).not.toContain('/themes/admin');
    expect(paths).not.toContain('/tools/news');
  });

  it('lists every path once', () => {
    const paths = allNavPaths();
    expect(new Set(paths).size).toBe(paths.length);
  });

  it('reaches the previously top-level pages', () => {
    const paths = new Set(allNavPaths());
    for (const p of [
      '/mushaf', '/bookmarks', '/challenge', '/reading-plan', '/duas', '/learn', '/stories', '/surah-atlas',
      '/prophets', '/memorization', '/concepts', '/themes', '/miracles', '/asma-allah', '/tafsir/compare',
      '/search', '/ask', '/tasmee', '/stats', '/journal', '/names', '/dhikr', '/asbab', '/timeline', '/quiz',
      '/quranic-calls', '/guidance', '/compare', '/flashcards', '/roots', '/therapy', '/sources', '/tools',
    ]) {
      expect(paths.has(p), `${p} not reachable from the shell`).toBe(true);
    }
  });

  it('maps paths to the right tab (longest prefix wins)', () => {
    expect(activeTabFor('/mushaf')).toBe('read');
    expect(activeTabFor('/quran/2')).toBe('read');
    expect(activeTabFor('/stories/yusuf')).toBe('explore');
    expect(activeTabFor('/tools/vocabulary')).toBe('explore');
    expect(activeTabFor('/tools/prayer-times')).toBe('more');
    expect(activeTabFor('/ask')).toBe('tadabbur');
    expect(activeTabFor('/flashcards')).toBe('memorise');
    expect(activeTabFor('/')).toBeNull();
  });

  it('hides the floating feedback button on reading surfaces only', () => {
    expect(isReaderRoute('/mushaf')).toBe(true);
    expect(isReaderRoute('/quran/18')).toBe(true);
    expect(isReaderRoute('/ask')).toBe(true);
    expect(isReaderRoute('/stories')).toBe(false);
    expect(isReaderRoute('/quranic-calls')).toBe(false);
  });

  it('registers a catch-all not-found route and gates admin routes', () => {
    expect(routePaths).toContain('*');
    expect(appSource).toMatch(/ADMIN_ENABLED\s*=\s*import\.meta\.env\.DEV \|\| import\.meta\.env\.VITE_ENABLE_ADMIN === 'true'/);
    expect(appSource).toMatch(/\{StatusDashboardPage && <Route path="\/status"/);
  });
});
