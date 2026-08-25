"""HTTP layer — port of the Java ``OnBoardingCreatorController``."""
from typing import Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.session import get_session
from ..schemas.envelope import NDorsifyUtil
from ..schemas.questions import Questions
from ..services import onboarding as service

router = APIRouter(prefix="/onboard/creator", tags=["onboarding"])


@router.get("/questions", response_model=NDorsifyUtil[Dict[str, List[Questions]]])
async def get_questions(
    session: AsyncSession = Depends(get_session),
) -> NDorsifyUtil:
    data = await service.all_questions(session)
    return NDorsifyUtil(status="success", message="success", data=data)
