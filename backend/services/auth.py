import logging
from typing import Optional
from venv import logger

import bcrypt
from pydantic import EmailStr
from sqlalchemy import select, and_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from models import User
from schemas.user import UserCreate


class AuthService:

    @staticmethod
    def hash_password(password: str) -> str:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )

    @staticmethod
    def fake_verify() -> None:
        """Perform a dummy bcrypt verification to mitigate timing attacks."""
        dummy_password = b"fake_password"
        # Generate a temporary hash and check it — ignore the result.
        dummy_hash = bcrypt.hashpw(dummy_password, bcrypt.gensalt())
        bcrypt.checkpw(dummy_password, dummy_hash)

    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate) -> Optional[User]:
        try:
            hashed_password = AuthService.hash_password(user_data.password)

            db_user = User(
                email=user_data.email,
                hashed_password=hashed_password
            )

            db.add(db_user)
            await db.commit()
            await db.refresh(db_user)

            return db_user

        except IntegrityError:
            await db.rollback()
            return None

    @staticmethod
    async def authenticate_user(
            db: AsyncSession,
            email: EmailStr,
            password: str
    ) -> Optional[User]:
        try:
            result = await db.execute(
                select(User)
                .where(and_(User.email == email, User.is_active.is_(True)))
                .limit(1)
            )
            user = result.scalar_one_or_none()

            if not user or not AuthService.verify_password(password, user.hashed_password):
                if not user:
                    AuthService.fake_verify()
                return None

            return user

        except SQLAlchemyError as e:
            logger.error(f"Database error while authenticating {email}: {e}")
            return None

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        try:
            result = await db.execute(
                select(User)
                .where(and_(User.id == user_id, User.is_active.is_(True)))
                .limit(1)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.warning(f"Could find user with id {user_id}: {e}")
            return None

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: EmailStr) -> Optional[User]:
        try:
            result = await db.execute(
                select(User)
                .where(and_(User.email == email, User.is_active.is_(True)))
                .limit(1)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.warning(f"Could find user with email {email}: {e}")
            return None

    @staticmethod
    async def get_current_user_from_session(
            db: AsyncSession,
            user_id: Optional[int]
    ) -> Optional[User]:
        """Get current user from session user_id."""
        if not user_id:
            return None

        return await AuthService.get_user_by_id(db, user_id)
