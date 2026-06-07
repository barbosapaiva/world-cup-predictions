from fastapi import APIRouter, FastAPI

from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.api.v1.leagues import router as leagues_router
from app.api.v1.tournament import router as tournament_router
from app.api.v1.users import router as users_router
from app.core.settings import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(health_router)
api_v1.include_router(users_router)
api_v1.include_router(auth_router)
api_v1.include_router(leagues_router)
api_v1.include_router(tournament_router)

app.include_router(api_v1)


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "status": "running",
        "docs": "/docs",
    }
