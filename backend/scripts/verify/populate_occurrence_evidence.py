#!/usr/bin/env python3
"""
Populate tafsir evidence for concept occurrences in the database.

Links occurrences to relevant tafseer chunks from the four Sunni madhabs.
"""
import asyncio
import sys
sys.path.insert(0, '/home/mhamdan/tadabbur/backend')

from sqlalchemy import text
from app.db.database import AsyncSessionLocal


# Priority tafseer sources by madhab (these exist in tafseer_chunks)
AVAILABLE_SOURCES = ['ibn_kathir_ar', 'qurtubi_ar', 'tabari_ar', 'muyassar_ar']


async def populate_evidence():
    """Link occurrences to tafseer chunks based on verse references."""

    async with AsyncSessionLocal() as session:
        # Get all occurrences with verse references
        result = await session.execute(text("""
            SELECT id, concept_id, sura_no, ayah_start, ayah_end
            FROM occurrences
            WHERE sura_no IS NOT NULL AND ayah_start IS NOT NULL
        """))
        occurrences = result.fetchall()

        print(f"Processing {len(occurrences)} occurrences...")

        updated = 0
        for occ in occurrences:
            occ_id, concept_id, sura_no, ayah_start, ayah_end = occ

            # Find matching tafseer chunks from available sources
            # Use aya_start to match single verse occurrences
            chunk_result = await session.execute(text("""
                SELECT id::text
                FROM tafseer_chunks
                WHERE sura_no = :sura_no
                  AND aya_start = :aya_start
                  AND source_id = ANY(:source_ids)
                ORDER BY source_id
            """), {
                'sura_no': sura_no,
                'aya_start': ayah_start,
                'source_ids': AVAILABLE_SOURCES
            })
            chunk_ids = [row[0] for row in chunk_result.fetchall()]

            if chunk_ids:
                # Update occurrence with evidence chunk IDs
                await session.execute(text("""
                    UPDATE occurrences
                    SET evidence_chunk_ids = :chunk_ids
                    WHERE id = :occ_id
                """), {
                    'chunk_ids': chunk_ids,
                    'occ_id': occ_id
                })
                updated += 1

        await session.commit()
        print(f"Updated {updated} occurrences with evidence links")

        # Show sample results
        sample = await session.execute(text("""
            SELECT o.id, c.label_en, o.sura_no, o.ayah_start,
                   array_length(o.evidence_chunk_ids, 1) as evidence_count
            FROM occurrences o
            JOIN concepts c ON o.concept_id = c.id
            WHERE o.evidence_chunk_ids IS NOT NULL
            LIMIT 10
        """))

        print("\nSample occurrences with evidence:")
        for row in sample:
            print(f"  {row[1]} ({row[2]}:{row[3]}) - {row[4]} sources")


async def get_evidence_stats():
    """Get statistics on evidence coverage."""

    async with AsyncSessionLocal() as session:
        # Total occurrences
        total_result = await session.execute(text(
            "SELECT COUNT(*) FROM occurrences WHERE sura_no IS NOT NULL"
        ))
        total = total_result.scalar()

        # Occurrences with evidence
        with_evidence = await session.execute(text(
            "SELECT COUNT(*) FROM occurrences WHERE evidence_chunk_ids IS NOT NULL AND array_length(evidence_chunk_ids, 1) > 0"
        ))
        evidence_count = with_evidence.scalar()

        print(f"\n=== Evidence Statistics ===")
        print(f"Total verse-linked occurrences: {total}")
        print(f"Occurrences with evidence: {evidence_count} ({100*evidence_count/total:.1f}% coverage)")

        # Get tafsir sources with madhab info
        sources = await session.execute(text("""
            SELECT id, name_en, madhab FROM tafseer_sources WHERE id = ANY(:ids)
        """), {'ids': AVAILABLE_SOURCES})
        
        print(f"\nEvidence sources used:")
        for row in sources:
            print(f"  {row[0]}: {row[1]} (madhab: {row[2]})")


if __name__ == "__main__":
    print("Populating tafsir evidence for concept occurrences...")
    asyncio.run(populate_evidence())
    asyncio.run(get_evidence_stats())
