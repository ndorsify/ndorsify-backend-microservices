"""Seed reference content — port of the Java ``data.sql`` insert statements.

Only runs when the table is empty, so it is safe on every startup.
"""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.content import Content

# (lookup_value1 question, lookup_value2 options, lookup_text3 category)
_SEED_QUESTIONS = [
    ("What is name1", "", "category1"),
    ("What is name2", "", "category2"),
    ("What is name3", "", "category3"),
    ("What is name4", "", "category1"),
    ("What is name5", "", "category3"),
    ("What is name6", "", "cat2"),
]


async def seed_content(session: AsyncSession) -> None:
    existing = await session.execute(select(func.count()).select_from(Content))
    if int(existing.scalar_one()) > 0:
        return

    for question, options, category in _SEED_QUESTIONS:
        session.add(
            Content(
                lookup_text1="creator-onboard-questions",
                lookup_value1=question,
                lookup_text2="String",
                lookup_value2=options,
                lookup_text3=category,
                created_by="Avinash",
                modified_by="Avinash",
                is_active=True,
                is_deleted=False,
            )
        )
    await session.commit()
