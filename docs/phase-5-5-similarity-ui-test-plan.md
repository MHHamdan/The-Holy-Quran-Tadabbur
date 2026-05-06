# Phase 5.5 – Similarity UI Test Plan

**Date:** 2026-04-27  
**Target component:** `KGSimilaritySection` (`frontend/src/components/quran/KGSimilaritySection.tsx`)

---

## Status

The frontend does not have Vitest / React Testing Library configured.  
The recommended tests below are documented for when a test framework is set up.

---

## Recommended Vitest + React Testing Library Tests

### File: `frontend/src/components/quran/__tests__/KGSimilaritySection.test.tsx`

```tsx
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { KGSimilaritySection } from '../KGSimilaritySection';
import * as api from '../../../lib/api';

// Mock quranApi.getKGSimilarity
jest.mock('../../../lib/api', () => ({
  ...jest.requireActual('../../../lib/api'),
  quranApi: {
    getKGSimilarity: jest.fn(),
  },
}));

const mockNeedsReviewResponse = {
  data: {
    sourceAyah: { surahNumber: 12, ayahNumber: 18 },
    relatedAyahs: [
      {
        surahNumber: 12,
        ayahNumber: 19,
        score: 0.46,
        relationTypes: ['SAME_STORY_SEGMENT'],
        explanationArabic: 'آيات من نفس قصة يوسف',
        explanationEnglish: 'Verses from the same story of Yusuf',
        evidence: [
          {
            sourceId: 'stories:yusuf',
            sourceTitleArabic: 'قصة يوسف',
            sourceTitleEnglish: 'Story of Yusuf',
            storyId: 'yusuf',
            relationStatus: 'needs_review',
          },
        ],
        warnings: ['All story-based relations await scholarly review.'],
        humanReviewRequired: true,
      },
    ],
    totalRelated: 1,
    allNeedsReview: true,
    searchTimeMs: 12,
  },
};

const mockExperimentalResponse = {
  data: {
    sourceAyah: { surahNumber: 2, ayahNumber: 255 },
    relatedAyahs: [
      {
        surahNumber: 59,
        ayahNumber: 22,
        score: 0.12,
        relationTypes: ['SEMANTICALLY_SIMILAR'],
        explanationArabic: 'تشابه دلالي',
        explanationEnglish: 'Semantic similarity',
        evidence: [
          {
            sourceId: 'system:embedding',
            relationStatus: 'experimental',
          },
        ],
        warnings: ['This connection is based on embedding similarity only.'],
        humanReviewRequired: true,
      },
    ],
    totalRelated: 1,
    allNeedsReview: true,
    searchTimeMs: 8,
  },
};

const mockEmptyResponse = {
  data: {
    sourceAyah: { surahNumber: 1, ayahNumber: 1 },
    relatedAyahs: [],
    totalRelated: 0,
    allNeedsReview: true,
    searchTimeMs: 5,
  },
};

describe('KGSimilaritySection', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders loading spinner initially', () => {
    (api.quranApi.getKGSimilarity as jest.Mock).mockResolvedValue(mockNeedsReviewResponse);
    render(
      <MemoryRouter>
        <KGSimilaritySection suraNo={12} ayaNo={18} />
      </MemoryRouter>
    );
    expect(screen.getByRole('status') /* or spinner */).toBeTruthy();
  });

  test('renders related ayah cards on success', async () => {
    (api.quranApi.getKGSimilarity as jest.Mock).mockResolvedValue(mockNeedsReviewResponse);
    render(
      <MemoryRouter>
        <KGSimilaritySection suraNo={12} ayaNo={18} />
      </MemoryRouter>
    );
    await waitFor(() =>
      expect(screen.getByText('12:19')).toBeInTheDocument()
    );
  });

  test('shows needs_review badge for story-based evidence', async () => {
    (api.quranApi.getKGSimilarity as jest.Mock).mockResolvedValue(mockNeedsReviewResponse);
    render(
      <MemoryRouter>
        <KGSimilaritySection suraNo={12} ayaNo={18} />
      </MemoryRouter>
    );
    await waitFor(() =>
      expect(screen.getAllByText(/Needs Review|قيد المراجعة/).length).toBeGreaterThan(0)
    );
  });

  test('shows humanReviewRequired warning when flag is true', async () => {
    (api.quranApi.getKGSimilarity as jest.Mock).mockResolvedValue(mockNeedsReviewResponse);
    render(
      <MemoryRouter>
        <KGSimilaritySection suraNo={12} ayaNo={18} />
      </MemoryRouter>
    );
    await waitFor(() =>
      expect(screen.getByText(/Under Review|تحت المراجعة/)).toBeInTheDocument()
    );
    // Expand the card
    fireEvent.click(screen.getByText('12:19').closest('div')!);
    await waitFor(() =>
      expect(screen.getByText(/scholarly review|مراجعة علمية/)).toBeInTheDocument()
    );
  });

  test('experimental relations hidden by default', async () => {
    (api.quranApi.getKGSimilarity as jest.Mock).mockResolvedValue(mockExperimentalResponse);
    render(
      <MemoryRouter>
        <KGSimilaritySection suraNo={2} ayaNo={255} />
      </MemoryRouter>
    );
    await waitFor(() => {
      // Card should not be visible since it's experimental and toggle is OFF
      expect(screen.queryByText('59:22')).not.toBeInTheDocument();
    });
  });

  test('experimental toggle shows experimental relations with warning', async () => {
    (api.quranApi.getKGSimilarity as jest.Mock)
      .mockResolvedValueOnce(mockEmptyResponse)      // first call (toggle OFF)
      .mockResolvedValueOnce(mockExperimentalResponse); // second call (toggle ON)

    render(
      <MemoryRouter>
        <KGSimilaritySection suraNo={2} ayaNo={255} />
      </MemoryRouter>
    );

    // Toggle is OFF initially
    await waitFor(() =>
      expect(screen.queryByText('59:22')).not.toBeInTheDocument()
    );

    // Turn toggle ON
    const toggle = screen.getByRole('switch');
    fireEvent.click(toggle);

    // Warning should appear below toggle
    await waitFor(() =>
      expect(screen.getByText(/automated suggestions|مقترحات آلية/)).toBeInTheDocument()
    );

    // Experimental result now visible (after re-fetch)
    await waitFor(() =>
      expect(screen.getByText('59:22')).toBeInTheDocument()
    );
  });

  test('empty evidence shows safe empty state', async () => {
    (api.quranApi.getKGSimilarity as jest.Mock).mockResolvedValue(mockEmptyResponse);
    render(
      <MemoryRouter>
        <KGSimilaritySection suraNo={1} ayaNo={1} />
      </MemoryRouter>
    );
    await waitFor(() =>
      expect(
        screen.getByText(/No verified related ayahs|لا توجد صلات موثوقة/)
      ).toBeInTheDocument()
    );
  });

  test('Arabic UI uses Arabic warning labels', async () => {
    // Mock language store to return 'ar'
    jest.mock('../../../stores/languageStore', () => ({
      useLanguageStore: () => ({ language: 'ar' }),
    }));
    (api.quranApi.getKGSimilarity as jest.Mock).mockResolvedValue(mockNeedsReviewResponse);
    render(
      <MemoryRouter>
        <KGSimilaritySection suraNo={12} ayaNo={18} />
      </MemoryRouter>
    );
    await waitFor(() =>
      expect(screen.getByText(/الروابط المعرفية/)).toBeInTheDocument()
    );
  });

  test('English UI uses English warning labels', async () => {
    (api.quranApi.getKGSimilarity as jest.Mock).mockResolvedValue(mockNeedsReviewResponse);
    render(
      <MemoryRouter>
        <KGSimilaritySection suraNo={12} ayaNo={18} />
      </MemoryRouter>
    );
    await waitFor(() =>
      expect(screen.getByText(/Knowledge Graph Relations/)).toBeInTheDocument()
    );
  });

  test('network error shows error state', async () => {
    (api.quranApi.getKGSimilarity as jest.Mock).mockRejectedValue(
      new Error('Network Error')
    );
    render(
      <MemoryRouter>
        <KGSimilaritySection suraNo={2} ayaNo={255} />
      </MemoryRouter>
    );
    await waitFor(() =>
      expect(
        screen.getByText(/Failed to load|تعذّر تحميل/)
      ).toBeInTheDocument()
    );
  });
});
```

---

## Backend Acceptance Tests (already configured)

The following pytest tests cover the KG service and are in `backend/tests/unit/`:

| Test file | Coverage |
|---|---|
| `test_verse_similarity_kg.py` | KG similarity service: scoring, evidence, warnings, experimental flag |
| `test_verse_embedding_service.py` | Embedding service graceful fallback |

Run with:
```bash
python -m pytest backend/tests/unit/test_verse_similarity_kg.py
python -m pytest backend/tests/unit/test_verse_embedding_service.py
```

---

## Notes

- Vitest configuration file: `frontend/vite.config.ts` — add `test: { environment: 'jsdom' }` to enable.
- React Testing Library: `npm install --save-dev @testing-library/react @testing-library/user-event jsdom`.
- Language store mock may need adjustment based on Zustand version.
