from fastapi import APIRouter
from sqlalchemy import text

from app.db.connection import AsyncSessionLocal

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
async def health_check():
    return {"status": "ok"}


@router.get("/db")
async def database_health_check():
    async with AsyncSessionLocal() as session:
        await session.execute(text("SELECT 1"))

    return {"database": "ok"}
