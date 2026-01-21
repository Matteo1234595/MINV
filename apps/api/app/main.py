from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import get_database_url
from app.ai.router import router as ai_router
from app.routers.auth import router as auth_router
from app.routers.health import router as health_router
from app.routers.kpis import router as kpis_router
from app.routers.strategist import router as strategist_router
from app.routers.uploads import router as uploads_router

app = FastAPI(title="AION OS API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def configure_database() -> None:
    app.state.database_url = get_database_url()


app.include_router(uploads_router)
app.include_router(kpis_router)
app.include_router(health_router)
app.include_router(strategist_router)
app.include_router(auth_router)
app.include_router(ai_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
