from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api.v1.router import router as api_v1_router
from app.config import get_settings
from app.config.database import check_database_connection, init_db

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    db_connected = await check_database_connection()
    if not db_connected:
        raise RuntimeError("Database connection failed. Exiting.")
    await init_db()
    yield
    from app.config.database import engine

    await engine.dispose()
    
    
app = FastAPI(
    title=settings.APP_NAME,
    description="A FastAPI account and email-verification boilerplate.",
    lifespan=lifespan
)

@app.get("/")
def read_root():
    return {
        "status": "running",
        "app_name": settings.APP_NAME,
        "docs": "/docs"
    }

app.include_router(api_v1_router)
