from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class History(Base):
    """LLM generation history (one row per completion)."""

    __tablename__ = "history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    model_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("models.id", ondelete="SET NULL"), nullable=True)
    prompt: Mapped[str] = mapped_column(Text, default="")
    response: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
