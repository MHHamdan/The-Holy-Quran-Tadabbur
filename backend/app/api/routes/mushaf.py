"""
Mushaf layout API — line-by-line word positions for King Fahd Madinah Mushaf.

GET /api/v1/mushaf/page/{page_no}/lines
    Returns words grouped by line for accurate Mushaf rendering.
"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_async_session

router = APIRouter()


class MushafWord(BaseModel):
    sura_no: int
    aya_no: int
    word_pos: int
    text: str
    char_type: str


class MushafLine(BaseModel):
    line_no: int
    words: List[MushafWord]


class MushafPageLines(BaseModel):
    page_no: int
    lines: List[MushafLine]


@router.get(
    "/page/{page_no}/lines",
    response_model=MushafPageLines,
    summary="Word-level line layout for a Mushaf page",
)
async def get_mushaf_page_lines(
    page_no: int,
    http_response: Response,
    session: AsyncSession = Depends(get_async_session),
) -> MushafPageLines:
    """
    Return all words on a Mushaf page grouped by physical line number.

    This enables pixel-faithful rendering of the King Fahd Madinah Mushaf
    with exact line breaks matching the 604-page printed edition.
    """
    if page_no < 1 or page_no > 604:
        raise HTTPException(status_code=400, detail="Page number must be between 1 and 604")

    result = await session.execute(
        text(
            """
            SELECT line_no, word_order, sura_no, aya_no, word_pos,
                   text_uthmani, char_type
              FROM mushaf_words
             WHERE page_no = :page
          ORDER BY word_order
            """
        ),
        {"page": page_no},
    )
    rows = result.fetchall()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No layout data for page {page_no}. Run: python backend/scripts/ingest/seed_mushaf_words.py",
        )

    # Group by line_no preserving order
    lines_map: dict[int, list[MushafWord]] = {}
    for row in rows:
        ln = row.line_no
        if ln not in lines_map:
            lines_map[ln] = []
        lines_map[ln].append(
            MushafWord(
                sura_no=row.sura_no,
                aya_no=row.aya_no,
                word_pos=row.word_pos,
                text=row.text_uthmani,
                char_type=row.char_type,
            )
        )

    lines = [MushafLine(line_no=ln, words=words) for ln, words in sorted(lines_map.items())]

    http_response.headers["Cache-Control"] = "public, max-age=86400"
    return MushafPageLines(page_no=page_no, lines=lines)
