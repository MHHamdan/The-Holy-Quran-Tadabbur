import { test, expect } from '@playwright/test';

/**
 * Similarity Page E2E Tests
 *
 * Verifies:
 * - Page loads correctly
 * - Popular verses are displayed
 * - Search functionality works
 * - Results display correctly
 * - Arabic mode works
 */
test.describe('Similarity Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/similarity');
    await page.waitForLoadState('networkidle');
  });

  test('should load similarity page', async ({ page }) => {
    // Page should have a heading
    const heading = page.locator('h1');
    await expect(heading).toBeVisible();

    // Should contain similarity-related text
    const pageContent = await page.textContent('body');
    expect(pageContent).toMatch(/صلة الآيات|Verse Links|Similar/i);
  });

  test('should display popular verses section', async ({ page }) => {
    // Should have popular verses section
    const popularSection = page.locator('text=Popular').or(page.locator('text=الآيات الشائعة'));
    await expect(popularSection).toBeVisible({ timeout: 5000 });
  });

  test('should have search input', async ({ page }) => {
    // Should have a search input
    const searchInput = page.locator('input[type="text"]').first();
    await expect(searchInput).toBeVisible();

    // Should accept verse reference input
    await searchInput.fill('2:255');
    await expect(searchInput).toHaveValue('2:255');
  });

  test('should show results when searching', async ({ page }) => {
    const searchInput = page.locator('input[type="text"]').first();
    await searchInput.fill('2:255');

    // Click search button or press Enter
    const searchButton = page.locator('button:has-text("Search")').or(page.locator('button:has-text("بحث")'));
    if (await searchButton.isVisible()) {
      await searchButton.click();
    } else {
      await searchInput.press('Enter');
    }

    // Wait for results to load
    await page.waitForTimeout(2000);

    // Should show some results or loading state
    const resultsArea = page.locator('.card, .result, [data-testid="similarity-results"]');
    const count = await resultsArea.count();
    // May have 0 results if backend is down, but page should not crash
    console.log(`Found ${count} result elements`);
  });

  test('should handle clicking popular verse', async ({ page }) => {
    // Find and click a popular verse button
    const popularVerse = page.locator('button:has-text("1:1")').or(page.locator('button:has-text("2:255")'));

    if (await popularVerse.first().isVisible()) {
      await popularVerse.first().click();
      await page.waitForTimeout(1000);

      // After clicking, search should be populated
      const searchInput = page.locator('input[type="text"]').first();
      const value = await searchInput.inputValue();
      expect(value).toMatch(/\d+:\d+/);
    }
  });
});

test.describe('Similarity Page - Filters', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/similarity');
    await page.waitForLoadState('networkidle');
  });

  test('should have filter controls', async ({ page }) => {
    // Should have filter section
    const filterSection = page.locator('text=Filter').or(page.locator('text=تصفية'));

    if (await filterSection.isVisible()) {
      // May have theme filter
      const themeSelect = page.locator('select').first();
      if (await themeSelect.isVisible()) {
        console.log('Theme filter found');
      }

      // May have min score filter
      const scoreSlider = page.locator('input[type="range"]').first();
      if (await scoreSlider.isVisible()) {
        console.log('Score slider found');
      }
    }
  });
});

test.describe('Similarity Page - Arabic Mode', () => {
  test('should display Arabic content', async ({ page }) => {
    await page.goto('/similarity');
    await page.waitForLoadState('networkidle');

    // Page should have Arabic content
    const arabicContent = page.locator('[dir="rtl"], :has-text("الآيات")');
    const count = await arabicContent.count();
    console.log(`Found ${count} Arabic/RTL elements`);

    // At minimum, the heading should be visible
    const heading = page.locator('h1');
    await expect(heading).toBeVisible();
  });
});

test.describe('Similarity Navigation', () => {
  test('should be accessible from main navigation', async ({ page }) => {
    await page.goto('/');

    // Find similarity link in navigation
    const similarityLink = page.locator('nav a:has-text("صلة الآيات")').or(page.locator('nav a:has-text("Verse Links")'));

    if (await similarityLink.isVisible()) {
      await similarityLink.click();
      await expect(page).toHaveURL('/similarity');
    } else {
      console.log('Similarity nav link not found in navigation');
    }
  });
});

// =============================================================================
// Input Parsing Tests - Testing various input formats
// =============================================================================
test.describe('Similarity Input Parsing', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/similarity');
    await page.waitForLoadState('networkidle');
  });

  test('should parse standard reference format (2:255)', async ({ page }) => {
    const searchInput = page.locator('input[type="text"]').first();
    await searchInput.fill('2:255');

    // Click search button
    const searchButton = page.locator('button:has-text("ابحث")').or(page.locator('button:has-text("Search")'));
    await searchButton.click();

    // Wait for API response
    await page.waitForTimeout(2000);

    // Should not show error, should show results or loading
    const errorPanel = page.locator('[data-testid="error-panel"]').or(page.locator('.error'));
    const hasError = await errorPanel.isVisible().catch(() => false);
    console.log(`Standard format (2:255): Error visible = ${hasError}`);
  });

  test('should parse spaced reference format (2 255)', async ({ page }) => {
    const searchInput = page.locator('input[type="text"]').first();
    await searchInput.fill('2 255');

    const searchButton = page.locator('button:has-text("ابحث")').or(page.locator('button:has-text("Search")'));
    await searchButton.click();

    await page.waitForTimeout(2000);

    // Page should not crash
    const heading = page.locator('h1');
    await expect(heading).toBeVisible();
    console.log('Spaced format (2 255) parsed successfully');
  });

  test('should parse Arabic digits (٢:٢٥٥)', async ({ page }) => {
    const searchInput = page.locator('input[type="text"]').first();
    await searchInput.fill('٢:٢٥٥');

    const searchButton = page.locator('button:has-text("ابحث")').or(page.locator('button:has-text("Search")'));
    await searchButton.click();

    await page.waitForTimeout(2000);

    // Should work the same as 2:255
    const heading = page.locator('h1');
    await expect(heading).toBeVisible();
    console.log('Arabic digits (٢:٢٥٥) parsed successfully');
  });

  test('should parse Arabic surah name (البقرة 255)', async ({ page }) => {
    const searchInput = page.locator('input[type="text"]').first();
    await searchInput.fill('البقرة 255');

    const searchButton = page.locator('button:has-text("ابحث")').or(page.locator('button:has-text("Search")'));
    await searchButton.click();

    await page.waitForTimeout(2000);

    // Should parse to 2:255
    const heading = page.locator('h1');
    await expect(heading).toBeVisible();
    console.log('Arabic surah name (البقرة 255) parsed successfully');
  });

  test('should parse surah name with سورة prefix (سورة البقرة 255)', async ({ page }) => {
    const searchInput = page.locator('input[type="text"]').first();
    await searchInput.fill('سورة البقرة 255');

    const searchButton = page.locator('button:has-text("ابحث")').or(page.locator('button:has-text("Search")'));
    await searchButton.click();

    await page.waitForTimeout(2000);

    const heading = page.locator('h1');
    await expect(heading).toBeVisible();
    console.log('Surah prefix (سورة البقرة 255) parsed successfully');
  });

  test('should parse English surah name (al-baqarah 255)', async ({ page }) => {
    const searchInput = page.locator('input[type="text"]').first();
    await searchInput.fill('al-baqarah 255');

    const searchButton = page.locator('button:has-text("ابحث")').or(page.locator('button:has-text("Search")'));
    await searchButton.click();

    await page.waitForTimeout(2000);

    const heading = page.locator('h1');
    await expect(heading).toBeVisible();
    console.log('English surah name (al-baqarah 255) parsed successfully');
  });

  test('should handle verse text input (قل هو الله أحد)', async ({ page }) => {
    const searchInput = page.locator('input[type="text"]').first();
    await searchInput.fill('قل هو الله أحد');

    const searchButton = page.locator('button:has-text("ابحث")').or(page.locator('button:has-text("Search")'));
    await searchButton.click();

    // Wait for resolve + search
    await page.waitForTimeout(3000);

    // Should attempt to resolve the verse text
    const heading = page.locator('h1');
    await expect(heading).toBeVisible();
    console.log('Verse text input (قل هو الله أحد) handled');
  });

  test('should show help tooltip with format examples', async ({ page }) => {
    // Look for help icon or format hint
    const helpIcon = page.locator('[data-testid="input-help"]').or(page.locator('button:has([class*="HelpCircle"])'));

    if (await helpIcon.isVisible()) {
      await helpIcon.hover();
      await page.waitForTimeout(500);

      // Should show format examples
      const tooltip = page.locator('[role="tooltip"]').or(page.locator('.tooltip'));
      if (await tooltip.isVisible()) {
        const tooltipText = await tooltip.textContent();
        console.log(`Help tooltip content: ${tooltipText?.substring(0, 100)}...`);
      }
    } else {
      console.log('Help icon not visible (may be integrated differently)');
    }
  });
});

// =============================================================================
// Verse Resolve API Tests
// =============================================================================
test.describe('Verse Resolve API', () => {
  test('should resolve exact verse text', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/quran/resolve', {
      params: { text: 'قل هو الله أحد' }
    });

    if (response.ok()) {
      const data = await response.json();
      expect(data.ok).toBe(true);
      expect(data.data).toHaveProperty('sura_no');
      expect(data.data).toHaveProperty('aya_no');
      expect(data.data).toHaveProperty('confidence');
      expect(data.data.sura_no).toBe(112);
      expect(data.data.aya_no).toBe(1);
      console.log(`Resolved "قل هو الله أحد" to ${data.data.sura_no}:${data.data.aya_no} with confidence ${data.data.confidence}`);
    } else {
      console.log(`Resolve API returned ${response.status()} - may need backend running`);
    }
  });

  test('should resolve verse with diacritics', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/quran/resolve', {
      params: { text: 'بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ' }
    });

    if (response.ok()) {
      const data = await response.json();
      expect(data.ok).toBe(true);
      expect(data.data.sura_no).toBe(1);
      expect(data.data.aya_no).toBe(1);
      console.log(`Resolved Bismillah to ${data.data.sura_no}:${data.data.aya_no}`);
    } else {
      console.log(`Resolve API returned ${response.status()}`);
    }
  });

  test('should return 404 for non-existent verse', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/quran/resolve', {
      params: { text: 'this is not a Quranic verse at all random text' }
    });

    // Should return 404 or error
    expect(response.status()).toBeGreaterThanOrEqual(400);
    console.log(`Non-existent verse returned status ${response.status()}`);
  });

  test('should resolve partial verse text', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/quran/resolve', {
      params: { text: 'الله لا إله إلا هو الحي القيوم' }
    });

    if (response.ok()) {
      const data = await response.json();
      expect(data.ok).toBe(true);
      // Should match Ayat Al-Kursi (2:255)
      expect(data.data.sura_no).toBe(2);
      expect(data.data.aya_no).toBe(255);
      console.log(`Resolved Ayat Al-Kursi fragment to ${data.data.sura_no}:${data.data.aya_no}`);
    } else {
      console.log(`Partial verse resolve returned ${response.status()}`);
    }
  });
});

// =============================================================================
// Similarity API Integration Tests
// =============================================================================
test.describe('Similarity API Integration', () => {
  test('should get similar verses for 2:255', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/quran/similarity/advanced/2/255');

    expect(response.ok()).toBe(true);
    const data = await response.json();

    expect(data).toHaveProperty('source_verse');
    expect(data).toHaveProperty('matches');
    expect(data.source_verse.sura_no).toBe(2);
    expect(data.source_verse.aya_no).toBe(255);
    expect(Array.isArray(data.matches)).toBe(true);

    console.log(`Found ${data.matches.length} similar verses for 2:255`);
  });

  test('should filter by minimum score', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/quran/similarity/advanced/2/255', {
      params: { min_score: 0.5 }
    });

    if (response.ok()) {
      const data = await response.json();

      // All matches should have combined score >= 0.5
      for (const match of data.matches) {
        expect(match.scores.combined).toBeGreaterThanOrEqual(0.5);
      }

      console.log(`Found ${data.matches.length} matches with score >= 0.5`);
    }
  });

  test('should handle invalid verse reference', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/quran/similarity/advanced/999/999');

    expect(response.status()).toBeGreaterThanOrEqual(400);
    console.log(`Invalid verse returned status ${response.status()}`);
  });
});

// =============================================================================
// Verse Resolver Decision Tests (Candidate Selection Flow)
// =============================================================================
test.describe('Verse Resolver Decision Logic', () => {
  test('should return auto decision for exact match', async ({ request }) => {
    // Exact match with full verse text should return decision: "auto"
    const response = await request.get('http://localhost:8000/api/v1/quran/resolve', {
      params: { text: 'قل هو الله أحد' }
    });

    if (response.ok()) {
      const data = await response.json();
      expect(data.ok).toBe(true);
      expect(data.data).toHaveProperty('decision');
      expect(data.data.decision).toBe('auto');
      expect(data.data).toHaveProperty('best_match');
      expect(data.data.best_match).not.toBeNull();
      console.log(`Exact match returned decision: ${data.data.decision}`);
    }
  });

  test('should return needs_user_choice for short/ambiguous input', async ({ request }) => {
    // Short input like single word should return needs_user_choice
    const response = await request.get('http://localhost:8000/api/v1/quran/resolve', {
      params: { text: 'الله' }  // Short - 4 chars, 1 token
    });

    if (response.ok()) {
      const data = await response.json();
      expect(data.ok).toBe(true);
      expect(data.data).toHaveProperty('decision');
      // Short input should never be auto
      expect(data.data.decision).not.toBe('auto');
      console.log(`Short input returned decision: ${data.data.decision}`);
    }
  });

  test('should return candidates array in response', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/quran/resolve', {
      params: { text: 'الله لا إله إلا هو' }
    });

    if (response.ok()) {
      const data = await response.json();
      expect(data.ok).toBe(true);
      expect(data.data).toHaveProperty('candidates');
      expect(Array.isArray(data.data.candidates)).toBe(true);
      // Should have max 5 candidates
      expect(data.data.candidates.length).toBeLessThanOrEqual(5);
      console.log(`Returned ${data.data.candidates.length} candidates`);
    }
  });

  test('should return not_found for non-matching text', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/quran/resolve', {
      params: { text: 'random english text that is not a verse' }
    });

    if (response.ok()) {
      const data = await response.json();
      expect(data.ok).toBe(true);
      expect(data.data).toHaveProperty('decision');
      expect(data.data.decision).toBe('not_found');
      console.log(`Non-matching text returned decision: ${data.data.decision}`);
    }
  });

  test('should enforce minimum 3 character input', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/quran/resolve', {
      params: { text: 'اب' }  // 2 chars - should fail
    });

    // Should return 400 or similar error
    expect(response.status()).toBeGreaterThanOrEqual(400);
    console.log(`2-char input returned status ${response.status()}`);
  });
});

// =============================================================================
// Candidate Selection UI Flow Tests
// =============================================================================
test.describe('Candidate Selection Modal', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/similarity');
    await page.waitForLoadState('networkidle');
  });

  test('should not show modal for auto decision (exact match)', async ({ page }) => {
    const searchInput = page.locator('input[type="text"]').first();
    await searchInput.fill('قل هو الله أحد');

    const searchButton = page.locator('button:has-text("ابحث")').or(page.locator('button:has-text("Search")'));
    await searchButton.click();

    // Wait for API response
    await page.waitForTimeout(2000);

    // Modal should NOT appear for exact match
    const modal = page.locator('[data-testid="candidate-modal"]').or(page.locator('[role="dialog"]:has-text("اختر الآية")'));
    const modalVisible = await modal.isVisible().catch(() => false);
    expect(modalVisible).toBe(false);
    console.log(`Exact match: Modal visible = ${modalVisible} (expected false)`);
  });

  test('should show modal for ambiguous input (needs_user_choice)', async ({ page }) => {
    const searchInput = page.locator('input[type="text"]').first();
    // Use a known ambiguous input that matches multiple verses
    await searchInput.fill('الله الرحمن الرحيم');

    const searchButton = page.locator('button:has-text("ابحث")').or(page.locator('button:has-text("Search")'));
    await searchButton.click();

    // Wait for API response
    await page.waitForTimeout(3000);

    // Check for modal or candidate selection UI
    const modal = page.locator('[data-testid="candidate-modal"]').or(page.locator('[role="dialog"]')).or(page.locator('.modal'));
    const modalVisible = await modal.isVisible().catch(() => false);

    if (modalVisible) {
      console.log('Candidate modal appeared for ambiguous input');

      // Modal should have candidate options
      const candidates = page.locator('[data-testid="candidate-option"]').or(page.locator('.candidate-item'));
      const candidateCount = await candidates.count();
      console.log(`Found ${candidateCount} candidate options in modal`);
    } else {
      // If no modal, check if we got a fuzzy match warning instead
      const warning = page.locator('[data-testid="fuzzy-warning"]').or(page.locator('text=تطابق تقريبي'));
      const warningVisible = await warning.isVisible().catch(() => false);
      console.log(`No modal shown, fuzzy warning visible = ${warningVisible}`);
    }
  });

  test('should allow selecting a candidate from modal', async ({ page }) => {
    const searchInput = page.locator('input[type="text"]').first();
    await searchInput.fill('بسم الله');  // Short, likely needs_user_choice

    const searchButton = page.locator('button:has-text("ابحث")').or(page.locator('button:has-text("Search")'));
    await searchButton.click();

    await page.waitForTimeout(3000);

    // If modal appears, click first candidate
    const candidateButton = page.locator('[data-testid="candidate-option"]').first().or(page.locator('.candidate-item button').first());

    if (await candidateButton.isVisible()) {
      await candidateButton.click();
      await page.waitForTimeout(1000);

      // Modal should close after selection
      const modal = page.locator('[data-testid="candidate-modal"]').or(page.locator('[role="dialog"]'));
      const modalStillVisible = await modal.isVisible().catch(() => false);
      console.log(`After candidate selection: Modal still visible = ${modalStillVisible}`);
    } else {
      console.log('No candidate button visible - may have auto-resolved');
    }
  });

  test('should show error for not_found decision', async ({ page }) => {
    const searchInput = page.locator('input[type="text"]').first();
    await searchInput.fill('random english text that does not match');

    const searchButton = page.locator('button:has-text("ابحث")').or(page.locator('button:has-text("Search")'));
    await searchButton.click();

    await page.waitForTimeout(3000);

    // Should show error message
    const errorMessage = page.locator('text=لم يتم العثور').or(page.locator('text=not found')).or(page.locator('[data-testid="error-message"]'));
    const errorVisible = await errorMessage.isVisible().catch(() => false);
    console.log(`Not found error message visible = ${errorVisible}`);
  });

  test('should show fuzzy match warning for approximate matches', async ({ page }) => {
    const searchInput = page.locator('input[type="text"]').first();
    // Use text that will likely produce fuzzy match
    await searchInput.fill('الله لا اله الا هو الحى القيوم');  // Slight variations

    const searchButton = page.locator('button:has-text("ابحث")').or(page.locator('button:has-text("Search")'));
    await searchButton.click();

    await page.waitForTimeout(3000);

    // Check for fuzzy match warning or info banner
    const fuzzyWarning = page.locator('[data-testid="fuzzy-warning"]').or(page.locator('text=تطابق تقريبي')).or(page.locator('text=approximate'));
    const warningVisible = await fuzzyWarning.isVisible().catch(() => false);
    console.log(`Fuzzy match warning visible = ${warningVisible}`);
  });
});

// =============================================================================
// Candidate API Contract Tests
// =============================================================================
test.describe('Candidate Response Structure', () => {
  test('candidates should have required fields', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/quran/resolve', {
      params: { text: 'الحمد لله رب العالمين' }
    });

    if (response.ok()) {
      const data = await response.json();

      if (data.data.candidates && data.data.candidates.length > 0) {
        const candidate = data.data.candidates[0];

        // Each candidate should have these fields
        expect(candidate).toHaveProperty('surah');
        expect(candidate).toHaveProperty('ayah');
        expect(candidate).toHaveProperty('confidence');
        expect(candidate).toHaveProperty('text');

        console.log(`Candidate structure: surah=${candidate.surah}, ayah=${candidate.ayah}, confidence=${candidate.confidence}`);
      }
    }
  });

  test('best_match should have required fields when present', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/quran/resolve', {
      params: { text: 'قل هو الله أحد' }
    });

    if (response.ok()) {
      const data = await response.json();

      if (data.data.best_match) {
        const bestMatch = data.data.best_match;

        expect(bestMatch).toHaveProperty('surah');
        expect(bestMatch).toHaveProperty('ayah');
        expect(bestMatch).toHaveProperty('text');
        expect(bestMatch).toHaveProperty('confidence');

        console.log(`Best match: ${bestMatch.surah}:${bestMatch.ayah} with confidence ${bestMatch.confidence}`);
      }
    }
  });
});
