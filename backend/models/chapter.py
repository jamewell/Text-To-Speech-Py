import datetime

from sqlalchemy import Column, Integer, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import relationship

from core.database import Base


class Chapter(Base):
    """Model that stores parsed chapter content for an uploaded file."""

    __tablename__ = "chapters"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id", ondelete="CASCADE"), nullable=False, index=True)
    chapter_index = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    start_page = Column(Integer, nullable=False)
    end_page = Column(Integer, nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
        nullable=False,
    )

    file = relationship("File", back_populates="chapters")

    def __repr__(self) -> str:
        return (
            f"<Chapter(id={self.id}, file_id={self.file_id}, "
            f"index={self.chapter_index}, title={self.title!r})>"
        )
