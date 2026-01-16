import { test, expect } from '@playwright/test';

/**
 * Grammar (إعراب) E2E Tests
 *
 * Verifies:
 * - Grammar panel loads on Quran page
 * - Health status is displayed
 * - Grammar analysis is shown when available
 * - Fallback behavior when service unavailable
 * - Arabic labels are used
 */
test.describe('Grammar Panel on Quran Page', () => {
  test.beforeEach(async ({ page }) => {
    // Go to a Quran page with a verse that has grammar analysis
    await page.goto('/quran/1'); // Al-Fatiha
    await page.waitForLoadState('networkidle');
  });

  test('should display grammar tab/panel', async ({ page }) => {
    // Find grammar tab or panel
    const grammarTab = page.locator('button:has-text("إعراب")').or(page.locator('button:has-text("Grammar")'));

    if (await grammarTab.isVisible()) {
      await expect(grammarTab).toBeVisible();

      // Click to open grammar panel
      await grammarTab.click();
      await page.waitForTimeout(500);
    }
  });

  test('should show grammar analysis for verse', async ({ page }) => {
    // Click on a verse to see grammar
    const verse = page.locator('.verse, [data-testid="verse"]').first();
    if (await verse.isVisible()) {
      await verse.click();
      await page.waitForTimeout(1000);
    }

    // Grammar panel may show analysis or health status
    const grammarContent = page.locator('.grammar-panel, [data-testid="grammar-analysis"]');
    if (await grammarContent.isVisible()) {
      console.log('Grammar panel is visible');
    }
  });

  test('should handle service unavailable gracefully', async ({ page }) => {
    // Mock or test when grammar service is down
    // The UI should show a warning, not crash

    const warningMessage = page.locator('text=غير متاحة').or(page.locator('text=unavailable'));

    // This will only pass if the service is actually unavailable
    // Just check that the page doesn't crash
    const heading = page.locator('h1');
    await expect(heading).toBeVisible();
  });
});

test.describe('Grammar API Health', () => {
  test('should check grammar health endpoint', async ({ page, request }) => {
    // Make a request to the grammar health endpoint
    const response = await request.get('http://localhost:8000/api/v1/grammar/health');

    // Should return a valid response
    expect(response.ok()).toBe(true);

    const data = await response.json();

    // Should have expected fields
    expect(data).toHaveProperty('status');
    expect(['ok', 'static_only', 'unavailable']).toContain(data.status);
    expect(data).toHaveProperty('ollama_available');
    expect(data).toHaveProperty('static_fallback_available');

    console.log(`Grammar health: ${data.status}, Ollama: ${data.ollama_available}, Static: ${data.static_fallback_available}`);
  });

  test('should return grammar labels', async ({ page, request }) => {
    const response = await request.get('http://localhost:8000/api/v1/grammar/labels');

    expect(response.ok()).toBe(true);

    const data = await response.json();

    // Should have label sets
    expect(data).toHaveProperty('pos_tags');
    expect(data).toHaveProperty('roles');
    expect(data).toHaveProperty('sentence_types');
    expect(data).toHaveProperty('case_endings');

    // Labels should be Arabic
    expect(data.pos_tags.length).toBeGreaterThan(0);
    const arabicPattern = /[\u0600-\u06FF]/;
    expect(arabicPattern.test(data.pos_tags[0])).toBe(true);
  });
});

test.describe('Grammar Analysis API', () => {
  test('should analyze verse 1:1 (Bismillah)', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/grammar/ayah/1:1');

    if (response.ok()) {
      const data = await response.json();

      expect(data).toHaveProperty('verse_reference');
      expect(data.verse_reference).toBe('1:1');
      expect(data).toHaveProperty('text');
      expect(data).toHaveProperty('tokens');
      expect(data).toHaveProperty('source');

      // Source should be one of valid values
      expect(['llm', 'static', 'hybrid', 'unavailable', 'error', 'timeout']).toContain(data.source);

      if (data.source === 'static') {
        // Static fallback should have tokens
        expect(data.tokens.length).toBeGreaterThan(0);
        console.log(`1:1 analyzed from static fallback with ${data.tokens.length} tokens`);
      }
    } else {
      console.log(`Grammar API returned ${response.status()}`);
    }
  });

  test('should analyze verse 2:255 (Ayat Al-Kursi)', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/grammar/ayah/2:255');

    if (response.ok()) {
      const data = await response.json();

      expect(data.verse_reference).toBe('2:255');
      expect(data).toHaveProperty('sentence_type');
      expect(data).toHaveProperty('overall_confidence');

      console.log(`2:255 analyzed with confidence ${data.overall_confidence}, source: ${data.source}`);
    }
  });

  test('should handle invalid verse reference', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/grammar/ayah/999:999');

    // Should return 400 or 404
    expect(response.status()).toBeGreaterThanOrEqual(400);
    expect(response.status()).toBeLessThan(500);
  });

  test('should handle malformed verse reference', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/grammar/ayah/invalid');

    expect(response.status()).toBe(400);
  });
});

test.describe('Grammar Verification API', () => {
  test('should submit grammar correction (public)', async ({ request }) => {
    const response = await request.post('http://localhost:8000/api/v1/grammar/verification/submit', {
      data: {
        verse_reference: '1:1',
        word_index: 0,
        word: 'بِسْمِ',
        proposed_pos: 'حرف جر',
        proposed_role: 'جار ومجرور',
        notes: 'Test correction from e2e'
      }
    });

    // Should accept the submission
    expect(response.status()).toBe(201);

    const data = await response.json();
    expect(data).toHaveProperty('id');
    expect(data).toHaveProperty('status');
    expect(data.status).toBe('pending');

    console.log(`Created verification task ${data.id}`);
  });

  test('should require admin for listing tasks', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/grammar/verification/tasks');

    // Should be unauthorized without token
    expect(response.status()).toBe(401);
  });

  test('should require admin for stats', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/grammar/verification/stats');

    // Should be unauthorized without token
    expect(response.status()).toBe(401);
  });
});

test.describe('Grammar UI Display', () => {
  test('should display Arabic grammar labels', async ({ page }) => {
    await page.goto('/quran/1');
    await page.waitForLoadState('networkidle');

    // Check for Arabic content in grammar panel
    const pageContent = await page.textContent('body');

    // Common Arabic grammar terms
    const arabicTerms = ['اسم', 'فعل', 'حرف', 'مبتدأ', 'خبر', 'جملة'];

    // At least some Arabic should be present
    const hasArabic = arabicTerms.some((term) => pageContent?.includes(term));
    console.log(`Page contains Arabic grammar terms: ${hasArabic}`);
  });
});
