from types import SimpleNamespace

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from models import User
from models.chapter import Chapter
from models.file import File, FileStatus
from services.pdf_parser import PdfParsingService


class FakePdfContext:
    def __init__(self, metadata: dict, pages: list[str]) -> None:
        self.metadata = metadata
        self.pages = [SimpleNamespace(extract_text=lambda text=text: text) for text in pages]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


@pytest.mark.asyncio
async def test_extract_document_detects_metadata_and_chapters(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_pdf = FakePdfContext(
        metadata={"Title": "Sample Book", "Author": "Jane Writer"},
        pages=[
            "Chapter 1 Introduction\nWelcome to this test document.",
            "Chapter 2 Details\nMore details are here.",
        ],
    )

    monkeypatch.setattr("services.pdf_parser.pdfplumber.open", lambda _: fake_pdf)

    parsed = PdfParsingService.extract_document(b"fake")

    assert parsed.title == "Sample Book"
    assert parsed.author == "Jane Writer"
    assert len(parsed.chapters) == 2
    assert parsed.chapters[0].title == "Chapter 1 Introduction"
    assert "Welcome to this test document." in parsed.chapters[0].content


@pytest.mark.asyncio
async def test_parse_and_store_saves_chapters(
    monkeypatch: pytest.MonkeyPatch,
    async_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    fake_pdf = FakePdfContext(
        metadata={"title": "Stored Title", "author": "Stored Author"},
        pages=[
            "Chapter 1 First\nAlpha text.",
            "Chapter 2 Second\nBeta text.",
        ],
    )

    monkeypatch.setattr("services.pdf_parser.pdfplumber.open", lambda _: fake_pdf)

    async with async_session_factory() as session:
        user = User(email="parser@example.com", hashed_password="hash", is_active=True)
        session.add(user)
        await session.commit()
        await session.refresh(user)

        file_record = File(
            user_id=user.id,
            original_filename="book.pdf",
            stored_filename="stored.pdf",
            file_size=1234,
            mime_type="application/pdf",
            bucket_name="raw-pdf-uploads",
            status=FileStatus.PENDING,
        )
        session.add(file_record)
        await session.commit()
        await session.refresh(file_record)

        chapter_count = await PdfParsingService.parse_and_store(
            db=session,
            file_record=file_record,
            pdf_bytes=b"fake",
        )

        assert chapter_count == 2

        result = await session.execute(
            select(Chapter).where(Chapter.file_id == file_record.id).order_by(Chapter.chapter_index.asc())
        )
        chapters = result.scalars().all()

        assert len(chapters) == 2
        assert chapters[0].title == "Chapter 1 First"
        assert chapters[1].title == "Chapter 2 Second"

        await session.refresh(file_record)
        assert file_record.parsed_title == "Stored Title"
        assert file_record.parsed_author == "Stored Author"


@pytest.mark.asyncio
async def test_extract_document_falls_back_when_no_headings(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_pdf = FakePdfContext(
        metadata={},
        pages=[
            "This is a plain text document.\nThere are no explicit chapter headings.",
            "Second page content continues here.",
        ],
    )

    monkeypatch.setattr("services.pdf_parser.pdfplumber.open", lambda _: fake_pdf)

    parsed = PdfParsingService.extract_document(b"fake", fallback_title="fallback.pdf")

    assert parsed.title == "This is a plain text document."
    assert parsed.author is None
    assert len(parsed.chapters) == 1
    assert parsed.chapters[0].chapter_index == 1
    assert parsed.chapters[0].start_page == 1
    assert parsed.chapters[0].end_page == 2
    assert "no explicit chapter headings" in parsed.chapters[0].content


@pytest.mark.asyncio
async def test_parse_and_store_raises_on_invalid_pdf_without_mutating(
    monkeypatch: pytest.MonkeyPatch,
    async_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    def _raise_invalid_pdf(_):
        raise ValueError("invalid pdf")

    monkeypatch.setattr("services.pdf_parser.pdfplumber.open", _raise_invalid_pdf)

    async with async_session_factory() as session:
        user = User(email="parser-fail@example.com", hashed_password="hash", is_active=True)
        session.add(user)
        await session.commit()
        await session.refresh(user)

        file_record = File(
            user_id=user.id,
            original_filename="broken.pdf",
            stored_filename="broken_stored.pdf",
            file_size=1234,
            mime_type="application/pdf",
            bucket_name="raw-pdf-uploads",
            status=FileStatus.PENDING,
            parsed_title="Existing title",
            parsed_author="Existing author",
        )
        session.add(file_record)
        await session.commit()
        await session.refresh(file_record)

        existing_chapter = Chapter(
            file_id=file_record.id,
            chapter_index=1,
            title="Existing chapter",
            content="Existing content",
            start_page=1,
            end_page=1,
        )
        session.add(existing_chapter)
        await session.commit()

        with pytest.raises(ValueError, match="invalid pdf"):
            await PdfParsingService.parse_and_store(
                db=session,
                file_record=file_record,
                pdf_bytes=b"broken",
            )

        await session.refresh(file_record)
        assert file_record.parsed_title == "Existing title"
        assert file_record.parsed_author == "Existing author"

        result = await session.execute(
            select(Chapter).where(Chapter.file_id == file_record.id)
        )
        chapters = result.scalars().all()
        assert len(chapters) == 1
        assert chapters[0].title == "Existing chapter"


@pytest.mark.asyncio
async def test_parse_and_store_rolls_back_if_db_write_fails(
    monkeypatch: pytest.MonkeyPatch,
    async_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    fake_pdf = FakePdfContext(
        metadata={"Title": "New title", "Author": "New author"},
        pages=["Chapter 1 First\nAlpha text."],
    )
    monkeypatch.setattr("services.pdf_parser.pdfplumber.open", lambda _: fake_pdf)

    async with async_session_factory() as session:
        user = User(email="parser-rollback@example.com", hashed_password="hash", is_active=True)
        session.add(user)
        await session.commit()
        await session.refresh(user)

        file_record = File(
            user_id=user.id,
            original_filename="rollback.pdf",
            stored_filename="rollback_stored.pdf",
            file_size=1234,
            mime_type="application/pdf",
            bucket_name="raw-pdf-uploads",
            status=FileStatus.PENDING,
            parsed_title="Existing title",
            parsed_author="Existing author",
        )
        session.add(file_record)
        await session.commit()
        await session.refresh(file_record)
        file_id = file_record.id

        session.add(
            Chapter(
                file_id=file_record.id,
                chapter_index=1,
                title="Existing chapter",
                content="Existing content",
                start_page=1,
                end_page=1,
            )
        )
        await session.commit()

        original_add = session.add
        failed_once = {"value": False}

        def failing_add(obj):
            if isinstance(obj, Chapter) and not failed_once["value"]:
                failed_once["value"] = True
                raise RuntimeError("insert failed")
            return original_add(obj)

        monkeypatch.setattr(session, "add", failing_add)

        with pytest.raises(RuntimeError, match="insert failed"):
            await PdfParsingService.parse_and_store(
                db=session,
                file_record=file_record,
                pdf_bytes=b"fake",
            )

    async with async_session_factory() as verify_session:
        persisted_file = await verify_session.get(File, file_id)
        assert persisted_file is not None
        assert persisted_file.parsed_title == "Existing title"
        assert persisted_file.parsed_author == "Existing author"

        result = await verify_session.execute(
            select(Chapter).where(Chapter.file_id == file_id)
        )
        chapters = result.scalars().all()
        assert len(chapters) == 1
        assert chapters[0].title == "Existing chapter"
