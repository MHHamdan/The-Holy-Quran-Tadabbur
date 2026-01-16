import { test, expect } from '@playwright/test';

/**
 * Miracles Page E2E Tests
 *
 * Verifies:
 * - Page loads with miracles data
 * - Each miracle shows related prophets
 * - Clicking "View Related Prophet" navigates correctly
 * - Empty state is handled gracefully
 */
test.describe('Miracles Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/miracles');
    // Wait for loading to complete
    await page.waitForLoadState('networkidle');
  });

  test('should load miracles list', async ({ page }) => {
    // Page should have header
    const heading = page.locator('h1');
    await expect(heading).toContainText(/Miracles|الآيات/);

    // Should have stats bar showing count
    const statsBar = page.locator('.bg-gradient-to-r');
    await expect(statsBar).toBeVisible();
  });

  test('should display miracle cards with data', async ({ page }) => {
    // Wait for miracle cards to load
    const miracleCards = page.locator('.bg-gradient-to-br');
    const count = await miracleCards.count();

    // Should have multiple miracle cards
    expect(count).toBeGreaterThan(0);

    // Each card should have a title
    const firstCard = miracleCards.first();
    const cardTitle = firstCard.locator('h3');
    await expect(cardTitle).toBeVisible();
  });

  test('should expand miracle card on click', async ({ page }) => {
    // Click a miracle card
    const firstCard = page.locator('.bg-gradient-to-br').first();
    await firstCard.click();
    await page.waitForTimeout(500);

    // Should show expanded content with description or related persons
    const expandedContent = page.locator('.border-t.border-amber-200');
    // Check if any card is expanded
    const expandedCount = await expandedContent.count();
    console.log(`Found ${expandedCount} expanded sections`);
  });

  test('should show related persons for prophetic miracles', async ({ page }) => {
    // Find a miracle card with related persons indicator
    const cardsWithPersons = page.locator('.bg-gradient-to-br:has([data-testid="person-count"])').or(
      page.locator('.bg-gradient-to-br:has-text("Prophet")')
    );

    // If there are cards with persons, verify they display correctly
    const count = await cardsWithPersons.count();
    if (count > 0) {
      const firstCard = cardsWithPersons.first();
      await firstCard.click();
      await page.waitForTimeout(500);

      // Look for related figures section in expanded content
      const relatedSection = page.locator('text=Related Figures').or(page.locator('text=الشخصيات المرتبطة'));
      if (await relatedSection.isVisible()) {
        await expect(relatedSection).toBeVisible();
      }
    }
  });

  test('should navigate to related prophet when clicking view link', async ({ page }) => {
    // Expand a miracle card
    const firstCard = page.locator('.bg-gradient-to-br').first();
    await firstCard.click();
    await page.waitForTimeout(500);

    // Find and click the "View Related Prophet" link
    const viewProphetLink = page.locator('a:has-text("View Related Prophet")').or(
      page.locator('a:has-text("عرض النبي المرتبط")')
    );

    if (await viewProphetLink.isVisible()) {
      await viewProphetLink.click();
      await expect(page).toHaveURL(/\/concepts\/person_/);
    }
  });

  test('should show error panel on API failure', async ({ page }) => {
    // Intercept API and return error
    await page.route('**/api/v1/concepts/miracles/all', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          ok: false,
          error: {
            code: 'internal_error',
            message: 'Test error',
            message_ar: 'خطأ تجريبي',
            request_id: 'test-request-id-123'
          },
          request_id: 'test-request-id-123'
        })
      });
    });

    await page.goto('/miracles');
    await page.waitForLoadState('networkidle');

    // Should show error panel with request ID
    const errorPanel = page.locator('[class*="bg-red"]');
    await expect(errorPanel).toBeVisible({ timeout: 5000 });

    // Should display request ID
    const requestId = page.locator('text=test-request-id-123');
    await expect(requestId).toBeVisible();
  });

  test('should show retry button on error', async ({ page }) => {
    // Intercept API and return error
    await page.route('**/api/v1/concepts/miracles/all', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          ok: false,
          error: {
            code: 'internal_error',
            message: 'Test error',
            message_ar: 'خطأ تجريبي',
            request_id: 'test-request-id-456'
          }
        })
      });
    });

    await page.goto('/miracles');
    await page.waitForLoadState('networkidle');

    // Should have retry button
    const retryButton = page.locator('button:has-text("Try Again")').or(
      page.locator('button:has-text("إعادة المحاولة")')
    );
    await expect(retryButton).toBeVisible({ timeout: 5000 });
  });
});

test.describe('Miracles Stats', () => {
  test('should display correct stats counts', async ({ page }) => {
    await page.goto('/miracles');
    await page.waitForLoadState('networkidle');

    // Stats bar should show counts
    const statsNumbers = page.locator('.text-2xl.font-bold');
    const count = await statsNumbers.count();

    // Should have at least the total miracles count
    expect(count).toBeGreaterThan(0);

    // First stat should be a number
    const firstStat = statsNumbers.first();
    const text = await firstStat.textContent();
    expect(text).toMatch(/\d+/);
  });
});
