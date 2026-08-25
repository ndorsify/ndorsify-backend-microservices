"""Business logic — port of the Java ``OnBoardingCreatorService``.

Returns onboarding questions grouped by category, preserving the first-seen
order of both categories and questions (Java used LinkedHashSet/LinkedHashMap).
"""
from typing import Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import content as repo
from ..schemas.questions import Questions
from ..utils.mapping import questions_from_content_entity

_LOOKUP_TYPE = "creator-onboard-questions"


async def all_questions(session: AsyncSession) -> Dict[str, List[Questions]]:
    rows = await repo.find_all_by_lookup_text1(session, _LOOKUP_TYPE)

    grouped: Dict[str, List[Questions]] = {}
    for content in rows:
        category = content.lookup_text3
        grouped.setdefault(category, []).append(
            questions_from_content_entity(content)
        )
    return grouped
