"""Content ORM model — port of the Java ``Content`` JPA entity.

The lookup columns are intentionally generic (a key/value lookup table):
  lookup_text1  -> the type          (e.g. "creator-onboard-questions")
  lookup_value1 -> the question text
  lookup_text2  -> the data type     (e.g. "String")
  lookup_value2 -> the options
  lookup_text3  -> the category
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base


class Content(Base):
    __tablename__ = "content"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    lookup_text1: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    lookup_value1: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    lookup_text2: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    lookup_value2: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    lookup_text3: Mapped[Optional[str]] = mapped_column(String, nullable=True)
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
