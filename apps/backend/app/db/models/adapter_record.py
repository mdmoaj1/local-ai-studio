from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AdapterRecord(Base):
    __tablename__ = "adapters"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(256), unique=True, index=True)
    path: Mapped[str] = mapped_column(String(2048))
    base_model: Mapped[str] = mapped_column(String(512), default="")
    size: Mapped[int] = mapped_column(BigInteger, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
