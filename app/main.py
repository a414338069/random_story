from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import get_db, init_db
from app.routers import game


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = get_db()
    init_db(db)
    yield
    db.close()


app = FastAPI(title="重生模拟器 Backend API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(game.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
