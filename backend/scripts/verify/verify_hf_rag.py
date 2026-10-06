#!/usr/bin/env python3
"""
Live check of the RAG pipeline against Hugging Face Inference Providers.

Spends a small amount of HF credit. Verifies:
1. The HF chat model answers a one-line prompt
2. RAG pipeline integration
3. Response quality with citations
4. Performance metrics
"""
import asyncio
import sys
import time
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.rag.pipeline import RAGPipeline
from app.rag.llm_provider import get_llm


async def test_hf_direct():
    """One short generation through the HF router."""
    print("\n" + "="*60)
    print("1. TESTING HUGGING FACE CHAT COMPLETION")
    print("="*60)

    llm = get_llm()
    print(f"  Model: {llm.model}")
    try:
        response = await llm.generate(
            system_prompt="Answer in one short sentence.",
            user_message="Say 'Bismillah' in Arabic and English.",
            max_tokens=60,
            temperature=0.0,
        )
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

    print(f"  Response: {response.content[:100]}")
    print(f"  Latency: {response.latency_ms}ms  Tokens: {response.tokens_used}")
    return True


async def test_rag_pipeline():
    """Test the full RAG pipeline with the HF model."""
    print("\n" + "="*60)
    print("2. TESTING RAG PIPELINE WITH HUGGING FACE")
    print("="*60)

    # Create async database connection
    engine = create_async_engine(
        settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
        echo=False,
    )
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Initialize RAG pipeline (Hugging Face LLM)
        pipeline = RAGPipeline(session)

        # Test queries
        test_queries = [
            {
                "question": "What is the meaning of Ayat Al-Kursi?",
                "language": "en",
                "description": "English verse meaning query",
            },
            {
                "question": "ما معنى التوكل على الله؟",
                "language": "ar",
                "description": "Arabic concept query (Tawakkul)",
            },
        ]

        results = []

        for test in test_queries:
            print(f"\n--- Test: {test['description']} ---")
            print(f"  Question: {test['question'][:50]}...")

            start_time = time.perf_counter()

            try:
                response = await pipeline.query(
                    question=test["question"],
                    language=test["language"],
                )

                elapsed_ms = int((time.perf_counter() - start_time) * 1000)

                print(f"\n  RESPONSE:")
                print(f"  Answer (first 300 chars): {response.answer[:300]}...")
                print(f"\n  METRICS:")
                print(f"    Confidence: {response.confidence:.2f} ({response.confidence_level})")
                print(f"    Citations: {len(response.citations)}")
                print(f"    LLM Latency: {response.processing_time_ms}ms")
                print(f"    Total Time: {elapsed_ms}ms")
                print(f"    Evidence Chunks: {response.evidence_chunk_count}")
                print(f"    Evidence Sources: {response.evidence_source_count}")

                if response.warnings:
                    print(f"    Warnings: {response.warnings}")

                if response.citations:
                    print(f"\n  CITATIONS:")
                    for i, c in enumerate(response.citations[:3], 1):
                        print(f"    [{i}] {c.source_name} - {c.verse_reference}")

                results.append({
                    "query": test["description"],
                    "success": True,
                    "confidence": response.confidence,
                    "citations": len(response.citations),
                    "latency_ms": response.processing_time_ms,
                })

            except Exception as e:
                print(f"  ERROR: {e}")
                results.append({
                    "query": test["description"],
                    "success": False,
                    "error": str(e),
                })

    await engine.dispose()
    return results


async def main():
    print("\n" + "#"*60)
    print("# TADABBUR-AI: HUGGING FACE RAG INTEGRATION TEST")
    print(f"# Model: {settings.hf_llm_model_id}")
    print("#"*60)

    # Test 1: Direct HF generation
    hf_ok = await test_hf_direct()

    if not hf_ok:
        print("\n❌ Hugging Face generation failed. Exiting.")
        sys.exit(1)

    # Test 2: Full RAG pipeline
    results = await test_rag_pipeline()

    # Summary
    print("\n" + "="*60)
    print("3. SUMMARY")
    print("="*60)

    successful = [r for r in results if r.get('success')]
    failed = [r for r in results if not r.get('success')]

    print(f"  Tests Passed: {len(successful)}/{len(results)}")

    if successful:
        avg_latency = sum(r['latency_ms'] for r in successful) / len(successful)
        avg_confidence = sum(r['confidence'] for r in successful) / len(successful)
        avg_citations = sum(r['citations'] for r in successful) / len(successful)

        print(f"  Avg LLM Latency: {avg_latency:.0f}ms")
        print(f"  Avg Confidence: {avg_confidence:.2f}")
        print(f"  Avg Citations: {avg_citations:.1f}")

    if failed:
        print(f"\n  Failed Tests:")
        for r in failed:
            print(f"    - {r['query']}: {r.get('error', 'Unknown error')}")

    if len(successful) == len(results):
        print("\n✅ All tests passed! Hugging Face RAG integration is working.")
    else:
        print("\n⚠️ Some tests failed. Check errors above.")


if __name__ == "__main__":
    asyncio.run(main())
