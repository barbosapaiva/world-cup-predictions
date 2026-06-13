from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import COOKIE_NAME, get_current_user
from app.core.jwt import create_access_token
from app.core.security import verify_password
from app.core.settings import settings
from app.db.connection import get_db_session
from app.models.users import User
from app.repositories.users import UserRepository
from app.schemas.auth import LoginRequest
from app.schemas.users import UserCreate, UserResponse
from app.services.users import UserService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserCreate,
    session: AsyncSession = Depends(get_db_session),
):
    service = UserService(UserRepository(session))
    return await service.create_user(data)


@router.post("/login")
async def login(
    data: LoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
):
    repository = UserRepository(session)
    user = await repository.get_by_email(str(data.email))

    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token = create_access_token(user.id)

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=settings.jwt_access_token_expire_minutes * 60,
        httponly=True,
        secure=not settings.debug,
        samesite="lax",
        path="/",
    )

    return {"message": "ok"}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(
        key=COOKIE_NAME,
        httponly=True,
        secure=not settings.debug,
        samesite="lax",
        path="/",
    )
    return {"message": "ok"}


@router.get("/me", response_model=UserResponse)
async def me(
    current_user: User = Depends(get_current_user),
):
    return current_user
