#!/usr/bin/env python3
"""
Test RAG pipeline with Ollama LLM provider.

Verifies:
1. Ollama connection and model availability
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
from app.rag.llm_provider import LLMProvider, test_ollama_connection


async def test_ollama_direct():
    """Test Ollama connection directly."""
    print("\n" + "="*60)
    print("1. TESTING OLLAMA CONNECTION")
    print("="*60)

    result = await test_ollama_connection("qwen2.5:32b")

    print(f"  Provider: {result['provider']}")
    print(f"  Model: {result['model']}")
    print(f"  Available: {result['available']}")

    if result.get('error'):
        print(f"  ERROR: {result['error']}")
        return False

    print(f"  Test Response: {result.get('response_test', 'N/A')[:100]}")
    print(f"  Latency: {result.get('latency_ms', 'N/A')}ms")
    print(f"  Tokens: {result.get('tokens_used', 'N/A')}")

    return result['available']


async def test_rag_pipeline():
    """Test the full RAG pipeline with Ollama."""
    print("\n" + "="*60)
    print("2. TESTING RAG PIPELINE WITH OLLAMA")
    print("="*60)

    # Create async database connection
    engine = create_async_engine(
        settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
        echo=False,
    )
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Initialize RAG pipeline with Ollama
        pipeline = RAGPipeline(session, llm_provider=LLMProvider.OLLAMA)

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
    print("# TADABBUR-AI: OLLAMA RAG INTEGRATION TEST")
    print(f"# LLM Provider: {settings.llm_provider}")
    print(f"# Model: {settings.ollama_model}")
    print("#"*60)

    # Test 1: Direct Ollama connection
    ollama_ok = await test_ollama_direct()

    if not ollama_ok:
        print("\n❌ Ollama connection failed. Exiting.")
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
        print("\n✅ All tests passed! Ollama RAG integration is working.")
    else:
        print("\n⚠️ Some tests failed. Check errors above.")


if __name__ == "__main__":
    asyncio.run(main())
