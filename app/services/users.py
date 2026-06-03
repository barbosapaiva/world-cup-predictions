from uuid import UUID

from fastapi import HTTPException, status

from app.models.users import User
from app.repositories.users import UserRepository
from app.schemas.users import UserCreate, UserUpdate


class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def create_user(self, data: UserCreate) -> User:
        email = str(data.email)

        existing = await self.repository.get_by_email(email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        user = User(
            name=data.name,
            email=email,
            password_hash=self._hash_password(data.password),
        )

        return await self.repository.create(user)

    async def get_user(self, user_id: UUID) -> User:
        user = await self.repository.get_by_id(user_id)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return user

    async def get_all_users(self) -> list[User]:
        return await self.repository.get_all()

    async def update_user(self, user_id: UUID, data: UserUpdate) -> User:
        user = await self.get_user(user_id)
        update_data = data.model_dump(exclude_unset=True)

        new_email = update_data.get("email")
        if new_email is not None:
            existing = await self.repository.get_by_email(str(new_email))
            if existing is not None and existing.id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already registered",
                )
            update_data["email"] = str(new_email)

        for field, value in update_data.items():
            setattr(user, field, value)

        return await self.repository.update(user)

    def _hash_password(self, password: str) -> str:
        # Temporary placeholder. Replace with bcrypt/passlib later.
        return f"hashed_{password}"
