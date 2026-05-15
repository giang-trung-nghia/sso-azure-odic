import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="be-2-fastapi", version="0.1.0")

_origins = os.environ.get("FASTAPI_CORS_ORIGINS", "")
_origins_list = [o.strip() for o in _origins.split(",") if o.strip()]

if _origins_list:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/health")
def health():
    return {"status": "ok", "service": "be-2-fastapi"}


@app.get("/")
def root():
    return {"message": "be-2-fastapi (infrastructure only — no auth yet)"}
