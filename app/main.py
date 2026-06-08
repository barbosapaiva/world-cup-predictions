from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.api.v1.leagues import router as leagues_router
from app.api.v1.predictions import router as predictions_router
from app.api.v1.rankings import router as rankings_router
from app.api.v1.scoring import router as scoring_router
from app.api.v1.tournament import router as tournament_router
from app.api.v1.users import router as users_router
from app.core.settings import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(health_router)
api_v1.include_router(users_router)
api_v1.include_router(auth_router)
api_v1.include_router(leagues_router)
api_v1.include_router(tournament_router)
api_v1.include_router(predictions_router)
api_v1.include_router(scoring_router)
api_v1.include_router(rankings_router)

app.include_router(api_v1)


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "status": "running",
        "docs": "/docs",
    }
