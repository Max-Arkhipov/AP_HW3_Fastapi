import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.routers.links import router as links_router
from src.routers.auth import router as auth_router
from src.database import engine, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):

    await init_db()
    yield

    await engine.dispose()

app = FastAPI(title="Link Shortener API", lifespan=lifespan)

app.include_router(links_router, prefix="/links", tags=["links"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True, host="127.0.0.1", log_level="debug")
