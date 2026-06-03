from uuid import UUID

from app.repositories.users import UserRepository
from app.schemas.users import UserCreate, UserResponse, UserUpdate
from app.services.users import UserService
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.connection import get_db_session

router = APIRouter(prefix="/users", tags=["Users"])


def get_user_service(
    session: AsyncSession = Depends(get_db_session),
) -> UserService:
    return UserService(UserRepository(session))


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    service: UserService = Depends(get_user_service),
):
    return await service.create_user(data)


@router.get("", response_model=list[UserResponse])
async def list_users(
    service: UserService = Depends(get_user_service),
):
    return await service.get_all_users()


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    service: UserService = Depends(get_user_service),
):
    return await service.get_user(user_id)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    data: UserUpdate,
    service: UserService = Depends(get_user_service),
):
    return await service.update_user(user_id, data)
