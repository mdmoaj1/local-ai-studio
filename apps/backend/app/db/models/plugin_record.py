from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PluginRecord(Base):
    __tablename__ = "plugins"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    path: Mapped[str] = mapped_column(String(512))
