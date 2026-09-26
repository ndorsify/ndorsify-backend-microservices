"""Declarative base shared by all ORM models in this service.

Models are written unqualified. The service's schema is applied by the engine's
`schema_translate_map` (db/session.py), which rewrites table references when a
statement is compiled rather than relying on a connection's `search_path` —
session state a transaction pooler does not reliably carry.
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
