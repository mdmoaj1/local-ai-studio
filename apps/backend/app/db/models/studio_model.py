from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class StudioModel(Base):
    __tablename__ = "models"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(256), unique=True, index=True)
    hf_repo_id: Mapped[str] = mapped_column(String(512))
    local_path: Mapped[str] = mapped_column(String(2048), default="")
    size: Mapped[int] = mapped_column(BigInteger, default=0)
    status: Mapped[str] = mapped_column(String(32), default="not_installed")
    model_type: Mapped[str] = mapped_column("type", String(32), default="llm")
    runtime: Mapped[str] = mapped_column(
        String(32),
        default="transformers",
        server_default=text("'transformers'"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
