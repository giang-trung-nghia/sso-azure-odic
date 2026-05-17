from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.session import init_db
from app.routers import identity


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="be-2-fastapi",
    version="0.2.0",
    description="Stateless Azure Entra JWT validation (Bearer tokens).",
    lifespan=lifespan,
)

settings = get_settings()
_origins = [o.strip() for o in settings.fastapi_cors_origins.split(",") if o.strip()]
if _origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(identity.router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "be-2-fastapi",
        "azure_auth_enabled": settings.azure_auth_enabled,
    }


@app.get("/")
def root():
    return {
        "message": "be-2-fastapi — send Authorization: Bearer <Azure access token> to /me or /protected",
        "azure_auth_enabled": settings.azure_auth_enabled,
        "docs": "/docs",
    }
