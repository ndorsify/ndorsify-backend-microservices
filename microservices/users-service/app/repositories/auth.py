"""Data-access for auth: user lookups by email and token-table CRUD."""
from datetime import datetime
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.auth import (
    EmailVerificationToken,
    PasswordResetToken,
    RefreshToken,
)
from ..models.users import Users


async def get_user_by_email(session: AsyncSession, email: str) -> Optional[Users]:
    result = await session.execute(select(Users).where(Users.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: int) -> Optional[Users]:
    return await session.get(Users, user_id)


async def get_refresh_token(
    session: AsyncSession, token_hash: str
) -> Optional[RefreshToken]:
    result = await session.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    return result.scalar_one_or_none()


async def revoke_all_refresh_tokens(
    session: AsyncSession, user_id: int, at: datetime
) -> None:
    await session.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=at)
    )


async def get_reset_token(
    session: AsyncSession, token_hash: str
) -> Optional[PasswordResetToken]:
    result = await session.execute(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
    )
    return result.scalar_one_or_none()


async def get_verification_token(
    session: AsyncSession, token_hash: str
) -> Optional[EmailVerificationToken]:
    result = await session.execute(
        select(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == token_hash
        )
    )
    return result.scalar_one_or_none()
