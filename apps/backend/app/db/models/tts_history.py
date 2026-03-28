from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, Text, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TtsHistory(Base):
    """One row per TTS generation request."""

    __tablename__ = "tts_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    text: Mapped[str] = mapped_column(Text, default="")
    voice_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("voices.id", ondelete="SET NULL"),
        nullable=True,
    )
    model_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("models.id", ondelete="SET NULL"),
        nullable=True,
    )
    audio_path: Mapped[str] = mapped_column(String(2048), default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
