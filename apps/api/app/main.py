from fastapi import FastAPI

from app.db import get_database_url

app = FastAPI(title="AION OS API", version="0.1.0")


@app.on_event("startup")
def configure_database() -> None:
    app.state.database_url = get_database_url()


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
