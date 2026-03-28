from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class JobRecord(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), default="queued", index=True)
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    message: Mapped[str] = mapped_column(Text, default="")
    payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
