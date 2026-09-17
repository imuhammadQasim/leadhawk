from datetime import datetime, timedelta, timezone
import logging
import smtplib

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import DataError, IntegrityError

from app.models.user import User
from app.schemas.user import (
    TokenResponse,
    UserCreate,
    UserCreateResponse,
    UserLogin,
    UserResponse,
    UserUpdate,
    UserVerify,
)
from app.config.database import get_db
from app.utils.auth import create_access_token, get_current_active_user
from app.utils.helpers import _generate_email_code, _hash_password, _hash_secret, _verify_password, _verify_secret
from app.services.smtp_email import send_email as smtp_email_sender

router = APIRouter(prefix="/user", tags=["user"])
logger = logging.getLogger(__name__)


@router.post("/login", response_model=TokenResponse)
async def login_user(user_data: UserLogin, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    user = await db.scalar(select(User).where(User.email == user_data.email))
    if user is None or not _verify_password(user_data.password, user.password_hash) or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    return TokenResponse(access_token=create_access_token(user.id), user=user)


@router.get("/me", response_model=UserResponse)
async def get_user(user: User = Depends(get_current_active_user)) -> User:
    return user


@router.patch("/me", response_model=UserResponse)
async def update_user(
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
) -> User:
    user.name = user_data.name
    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)) -> None:
    await db.delete(user)
    await db.commit()

@router.post("/create", response_model=UserCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)) -> UserCreateResponse:
    existing_user = await db.scalar(select(User).where(User.email == user_data.email))
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )
    
    otpcode = _generate_email_code()
    db_user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=_hash_password(user_data.password),
        verification_code_hash=_hash_secret(otpcode),
        verification_code_expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
        is_active=False,
        created_at=datetime.now(timezone.utc),
    )
    db.add(db_user)
    
    try:
        await db.commit()
        await db.refresh(db_user)
        try:
            await smtp_email_sender(
                user_data.email,
                "Verify your account",
                f"<p>Your verification code is <strong>{otpcode}</strong>. It expires in 15 minutes.</p>",
            )
        except (OSError, smtplib.SMTPException):
            # The account was committed already. Keep the response successful
            # so client retries do not turn into misleading duplicate errors.
            logger.exception("Verification email could not be sent for the newly created account")
    except (IntegrityError, DataError) as exc:
        await db.rollback()
        message = str(exc).lower()
        if "users_email_key" in message or "duplicate" in message or "already exists" in message:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists.",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database validation error while creating user.",
        ) from exc

    return {
        "code": 201,
        "success": True,
        "message": "User created successfully",
        "user": db_user,
    }


@router.post("/verify", response_model=UserResponse)
async def verify_user(user_data: UserVerify, db: AsyncSession = Depends(get_db)) -> User:
    user = await db.scalar(select(User).where(User.email == user_data.email))
    now = datetime.now(timezone.utc)
    if (
        user is None
        or user.verification_code_hash is None
        or user.verification_code_expires_at is None
        or user.verification_code_expires_at < now
        or not _verify_secret(user_data.code, user.verification_code_hash)
    ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification code.")

    user.is_active = True
    user.verification_code_hash = None
    user.verification_code_expires_at = None
    await db.commit()
    await db.refresh(user)
    return user
