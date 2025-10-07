import secrets
from venv import logger

from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.requests import Request
from starlette.responses import Response

from core.config import settings
from core.database import get_db_session
from models import User
from schemas.user import AuthResponse, UserCreate, UserOut, UserLogin
from services.auth import AuthService

router = APIRouter()

SESSION_COOKIE_NAME = "session_id"
SESSION_MAX_AGE = 60 * 60 * 24 * 7  # 7 days

def create_session_token() -> str:
    return secrets.token_urlsafe(32)

def set_session_cookie(response: Response, session_token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        secure= not settings.DEBUG,
        samesite="lax"
    )

def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax"
    )

def create_session(user: User, response: Response) -> None:
    session_token = create_session_token()
    sessions[session_token] = {
        "user_id": user.id,
        "email": user.email
    }

    set_session_cookie(response, session_token)


sessions: dict[str, dict] = {}


@router.post(
    path="/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account with email and password"
)
async def register_user(
    user_data: UserCreate,
    response: Response,
    db: AsyncSession = Depends(get_db_session)
):
    try:
        existing_user = await AuthService.get_user_by_email(db, user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        new_user = await AuthService.create_user(db, user_data)
        if not new_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Fail to create user"
            )

        create_session(new_user, response)

        return AuthResponse(
            message="User registered successfully",
            user=UserOut.model_validate(new_user)
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during registration"
        )


@router.post(
    path="/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Login user",
    description="Authenticate user with email and password"
)
async def login_user(
        login_data: UserLogin,
        response: Response,
        db: AsyncSession = Depends(get_db_session)
):
    try:
        user = await AuthService.authenticate_user(
            db,
            login_data.email,
            login_data.password
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        create_session(user, response)

        return AuthResponse(
            message="Login successful",
            user=UserOut.model_validate(user)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed login: {e}" )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )

@router.post(
    path="/logout",
    status_code=status.HTTP_200_OK,
    summary="Logout user",
    description="Clear user session and logout"
)
async def logout_user(request: Request, response: Response):
    try:
        session_token = request.cookies.get(SESSION_COOKIE_NAME)

        if session_token and session_token in sessions:
            del sessions[session_token]

        clear_session_cookie(response)

        return {"message": "Logout successful"}

    except Exception as e:
        logger.error(f"Error while trying to logout: {e}")
        clear_session_cookie(response)
        return {"message": "Logout completed"}


@router.get(
    path="/me",
    response_model=UserOut,
    status_code=status.HTTP_200_OK,
    summary="Get current user",
    description="Get current authenticated user information"
)
async def get_current_user(
        request: Request,
        db: AsyncSession = Depends(get_db_session)
):
    try:
        session_token = request.cookies.get(SESSION_COOKIE_NAME)

        if not session_token or session_token not in sessions:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )

        session_data = sessions[session_token]
        user_id = session_data.get("user_id")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session"
            )

        user = await AuthService.get_current_user_from_session(db, user_id)

        if not user:
            del sessions[session_token]
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        return UserOut.model_validate(user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )














