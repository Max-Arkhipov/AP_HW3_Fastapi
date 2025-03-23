import uvicorn
from fastapi import FastAPI
from src.routers.links import router as links_router
from src.routers.auth import router as auth_router
from src.database import engine, init_db
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Код, выполняемый при старте приложения
    await init_db()
    yield
    # Код, выполняемый при завершении приложения
    await engine.dispose()

app = FastAPI(title="Link Shortener API", lifespan=lifespan)

app.include_router(links_router, prefix="/links", tags=["links"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True, host="0.0.0.0", log_level="info")
