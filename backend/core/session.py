import secrets
from typing import Any

from starlette.requests import Request
from starlette.responses import Response

from core.config import settings
from models import User

SESSION_COOKIE_NAME = "session_id"
SESSION_MAX_AGE = 60 * 60 * 24 * 7  # 7 days

sessions: dict[str, dict[str, Any]] = {}


def create_session_token() -> str:
    return secrets.token_urlsafe(32)


def set_session_cookie(response: Response, session_token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        secure=not settings.DEBUG,
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


def get_session_token(request: Request) -> str | None:
    return request.cookies.get(SESSION_COOKIE_NAME)
