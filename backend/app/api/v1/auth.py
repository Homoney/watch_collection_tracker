from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.config import settings
from app.core.deps import get_current_user
from app.core.security import (
    decode_token,
    get_password_hash,
    issue_tokens,
    token_version_matches,
    verify_password,
)
from app.database import get_db, take_write_lock
from app.models.user import User, UserRole
from app.schemas.user import (
    TokenRefresh,
    TokenResponse,
    UserChangePassword,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
)
from app.utils.logging import log_security_event

router = APIRouter()

REFRESH_COOKIE = "refresh_token"
REFRESH_COOKIE_PATH = "/api/v1/auth"


def _cookie_secure(request: Request) -> bool:
    if settings.COOKIE_SECURE is not None:
        return settings.COOKIE_SECURE
    proto = request.headers.get("x-forwarded-proto", request.url.scheme)
    return proto.split(",")[0].strip() == "https"


def _set_refresh_cookie(response: Response, request: Request, token: str) -> None:
    response.set_cookie(
        REFRESH_COOKIE,
        token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path=REFRESH_COOKIE_PATH,
        httponly=True,
        secure=_cookie_secure(request),
        samesite="strict",
    )


def _clear_refresh_cookie(response: Response, request: Request) -> None:
    response.delete_cookie(
        REFRESH_COOKIE,
        path=REFRESH_COOKIE_PATH,
        httponly=True,
        secure=_cookie_secure(request),
        samesite="strict",
    )


def _ensure_not_locked(user: User) -> None:
    if user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed attempts. Try again later.",
        )


def _record_failure(db: Session, user: User) -> None:
    user.failed_login_count = (user.failed_login_count or 0) + 1
    if user.failed_login_count >= settings.LOGIN_MAX_FAILURES:
        user.locked_until = datetime.utcnow() + timedelta(
            minutes=settings.LOGIN_LOCKOUT_MINUTES
        )
        user.failed_login_count = 0
        log_security_event("account_locked", user_id=str(user.id), email=user.email)
    db.commit()


def _record_success(db: Session, user: User) -> None:
    if user.failed_login_count or user.locked_until:
        user.failed_login_count = 0
        user.locked_until = None
        db.commit()


@router.post(
    "/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
)
def register(
    user_data: UserCreate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Register a new user.

    Registration is closed unless ALLOW_REGISTRATION is on. On an empty
    database, the account whose email equals INITIAL_ADMIN_EMAIL may always
    register and becomes the admin. Nobody else is ever made admin here.
    """
    # Serialise registrations so the "empty database" check and the insert
    # cannot race (two simultaneous first sign-ups).
    take_write_lock(db)

    is_bootstrap_admin = (
        bool(settings.INITIAL_ADMIN_EMAIL)
        and user_data.email.lower() == settings.INITIAL_ADMIN_EMAIL.strip().lower()
        and db.query(User).count() == 0
    )

    if not is_bootstrap_admin and not settings.ALLOW_REGISTRATION:
        log_security_event(
            "registration_refused",
            email=user_data.email,
            details={"reason": "registration_closed"},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registration is closed. Ask the administrator for an account.",
        )

    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        role=UserRole.admin if is_bootstrap_admin else UserRole.user,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Log successful registration
    log_security_event(
        "user_registered", user_id=str(new_user.id), email=new_user.email
    )

    access_token, refresh_token = issue_tokens(new_user)
    _set_refresh_cookie(response, request, refresh_token)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=TokenResponse)
def login(
    user_data: UserLogin,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Login with email and password"""
    # Find user by email
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user:
        log_security_event(
            "login_failed", email=user_data.email, details={"reason": "user_not_found"}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    _ensure_not_locked(user)

    # Verify password
    if not verify_password(user_data.password, user.hashed_password):
        _record_failure(db, user)
        log_security_event(
            "login_failed",
            user_id=str(user.id),
            email=user.email,
            details={"reason": "invalid_password"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    _record_success(db, user)

    # Log successful login
    log_security_event("login_success", user_id=str(user.id), email=user.email)

    access_token, refresh_token = issue_tokens(user)
    _set_refresh_cookie(response, request, refresh_token)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    request: Request,
    response: Response,
    token_data: Optional[TokenRefresh] = None,
    refresh_cookie: Optional[str] = Cookie(default=None, alias=REFRESH_COOKIE),
    db: Session = Depends(get_db),
):
    """Issue new tokens from a refresh token (HttpOnly cookie, or JSON body)."""
    from_body = token_data is not None and bool(token_data.refresh_token)
    token = token_data.refresh_token if from_body else refresh_cookie
    invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
    )
    if not token:
        raise invalid

    payload = decode_token(token)
    if payload is None:
        raise invalid
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
        )
    user_id = payload.get("sub")
    if user_id is None:
        raise invalid

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not token_version_matches(payload, user):
        _clear_refresh_cookie(response, request)
        raise invalid

    access_token, new_refresh_token = issue_tokens(user)
    _set_refresh_cookie(response, request, new_refresh_token)
    # Only hand the refresh token back to callers that sent one in the body;
    # browser sessions keep it in the HttpOnly cookie only.
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token if from_body else None,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Log out: ends every session of this user and clears the cookie."""
    current_user.token_version = (current_user.token_version or 0) + 1
    db.commit()
    log_security_event("logout", user_id=str(current_user.id))
    _clear_refresh_cookie(response, request)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return current_user


@router.put("/me", response_model=UserResponse)
def update_me(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update current user profile"""
    if user_data.full_name is not None:
        current_user.full_name = user_data.full_name
    if user_data.default_currency is not None:
        current_user.default_currency = user_data.default_currency
    if user_data.theme is not None:
        current_user.theme = user_data.theme

    db.commit()
    db.refresh(current_user)

    return current_user


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    password_data: UserChangePassword,
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change current user password"""
    _ensure_not_locked(current_user)

    # Verify current password
    if not verify_password(
        password_data.current_password, current_user.hashed_password
    ):
        _record_failure(db, current_user)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect current password"
        )

    # Update password and end all other sessions
    current_user.hashed_password = get_password_hash(password_data.new_password)
    current_user.token_version = (current_user.token_version or 0) + 1
    db.commit()
    log_security_event("password_changed", user_id=str(current_user.id))

    # Keep this browser signed in: the next refresh uses the new cookie.
    _, refresh_token = issue_tokens(current_user)
    _set_refresh_cookie(response, request, refresh_token)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
