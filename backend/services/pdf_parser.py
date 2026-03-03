"""PDF parsing service for extracting metadata and chapter content."""

from __future__ import annotations

import io
import logging
import re
from dataclasses import dataclass

import pdfplumber
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from models.chapter import Chapter
from models.file import File

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ChapterPayload:
    chapter_index: int
    title: str
    content: str
    start_page: int
    end_page: int


@dataclass(slots=True)
class ParsedDocument:
    title: str | None
    author: str | None
    chapters: list[ChapterPayload]


class PdfParsingService:
    """Extracts PDF metadata/text and stores chapter records."""

    CHAPTER_PATTERNS = (
        re.compile(r"^\s*(chapter|hoofdstuk)\s+[0-9ivxlcdm]+\b", re.IGNORECASE),
        re.compile(r"^\s*\d+(?:\.\d+){0,2}\s+[A-Z].{2,}$"),
    )

    @staticmethod
    def _is_heading(line: str) -> bool:
        text = line.strip()
        if len(text) < 4 or len(text) > 120:
            return False
        if any(pattern.match(text) for pattern in PdfParsingService.CHAPTER_PATTERNS):
            return True
        words = text.split()
        if text.isupper() and 1 < len(words) <= 10:
            return True
        return False

    @staticmethod
    def _normalize_metadata(metadata: dict | None) -> tuple[str | None, str | None]:
        if not metadata:
            return None, None

        title = metadata.get("Title") or metadata.get("title")
        author = metadata.get("Author") or metadata.get("author")

        title = title.strip() if isinstance(title, str) and title.strip() else None
        author = author.strip() if isinstance(author, str) and author.strip() else None

        return title, author

    @staticmethod
    def extract_document(pdf_bytes: bytes, fallback_title: str | None = None) -> ParsedDocument:
        lines: list[tuple[int, str]] = []
        metadata_title: str | None = None
        metadata_author: str | None = None

        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            metadata_title, metadata_author = PdfParsingService._normalize_metadata(pdf.metadata)

            for page_idx, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                for raw_line in text.splitlines():
                    line = raw_line.strip()
                    if line:
                        lines.append((page_idx, line))

        derived_title = metadata_title
        if not derived_title and lines:
            derived_title = lines[0][1]
        if not derived_title:
            derived_title = fallback_title

        chapter_start_indices: list[int] = []
        for idx, (_, line) in enumerate(lines):
            if PdfParsingService._is_heading(line):
                chapter_start_indices.append(idx)

        chapters: list[ChapterPayload] = []
        if chapter_start_indices:
            for chapter_num, start_idx in enumerate(chapter_start_indices, start=1):
                end_idx = (
                    chapter_start_indices[chapter_num] - 1
                    if chapter_num < len(chapter_start_indices)
                    else len(lines) - 1
                )

                title = lines[start_idx][1]
                start_page = lines[start_idx][0]
                end_page = lines[end_idx][0]
                content = "\n".join(line for _, line in lines[start_idx:end_idx + 1]).strip()

                if content:
                    chapters.append(
                        ChapterPayload(
                            chapter_index=chapter_num,
                            title=title,
                            content=content,
                            start_page=start_page,
                            end_page=end_page,
                        )
                    )

        if not chapters:
            all_text = "\n".join(line for _, line in lines).strip()
            if all_text:
                start_page = lines[0][0] if lines else 1
                end_page = lines[-1][0] if lines else 1
                chapters.append(
                    ChapterPayload(
                        chapter_index=1,
                        title=derived_title or "Full document",
                        content=all_text,
                        start_page=start_page,
                        end_page=end_page,
                    )
                )

        return ParsedDocument(title=derived_title, author=metadata_author, chapters=chapters)

    @staticmethod
    async def parse_and_store(
        db: AsyncSession,
        file_record: File,
        pdf_bytes: bytes,
    ) -> int:
        """Parse a PDF and persist parsed chapter records for a file."""
        parsed = PdfParsingService.extract_document(
            pdf_bytes=pdf_bytes,
            fallback_title=file_record.original_filename,
        )

        transaction = db.begin_nested() if db.in_transaction() else db.begin()
        async with transaction:
            await db.execute(delete(Chapter).where(Chapter.file_id == file_record.id))

            for chapter in parsed.chapters:
                db.add(
                    Chapter(
                        file_id=file_record.id,
                        chapter_index=chapter.chapter_index,
                        title=chapter.title,
                        content=chapter.content,
                        start_page=chapter.start_page,
                        end_page=chapter.end_page,
                    )
                )

            file_record.parsed_title = parsed.title
            file_record.parsed_author = parsed.author

        logger.info(
            "Parsed PDF and stored chapter records",
            extra={
                "file_id": file_record.id,
                "chapter_count": len(parsed.chapters),
                "parsed_title": parsed.title,
                "parsed_author": parsed.author,
            },
        )

        return len(parsed.chapters)
