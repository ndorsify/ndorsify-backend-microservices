"""Users ORM model — port of the Java ``Users`` JPA entity."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base


class Users(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    first_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    # Unique login identity. Nullable for legacy/admin-created rows; multiple
    # NULLs stay allowed under a unique index (Postgres & SQLite).
    email: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, unique=True, index=True
    )
    image_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    role: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    # --- Auth (P0) ---
    password_hash: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    status: Mapped[str] = mapped_column(
        String, server_default="active", default="active", nullable=False
    )
    created_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    modified_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_date: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), default=func.now()
    )
    modified_date: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), default=func.now(), onupdate=func.now()
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
