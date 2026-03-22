import datetime

from sqlalchemy import Column, Integer, ForeignKey, Float, UniqueConstraint
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import relationship

from core.database import Base


class ReadingHistory(Base):
    """Model that tracks a user's listening progress for a file."""

    __tablename__ = "reading_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    file_id = Column(Integer, ForeignKey("files.id", ondelete="CASCADE"), nullable=False, index=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id", ondelete="CASCADE"), nullable=True, index=True)
    position_seconds = Column(Float, nullable=False)
    updated_at = Column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
        nullable=False,
    )

    user = relationship("User", back_populates="reading_history")
    file = relationship("File", back_populates="reading_history")

    __table_args__ = (
        UniqueConstraint("user_id", "file_id", name="uq_reading_history_user_file"),
    )

    def __repr__(self) -> str:
        return (
            f"<ReadingHistory(id={self.id}, user_id={self.user_id}, "
            f"file_id={self.file_id}, position={self.position_seconds})>"
        )
