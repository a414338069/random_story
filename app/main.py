import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import get_db, init_db
from app.routers import game
from app.routers import save


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = get_db()
    init_db(db)
    yield
    db.close()


app = FastAPI(title="修仙人生模拟器 API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 路由（优先匹配）
app.include_router(game.router)
app.include_router(save.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}


# --------------- 生产模式：静态文件服务 ---------------
STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "web", "dist")
if os.path.isdir(STATIC_DIR) and os.path.exists(os.path.join(STATIC_DIR, "index.html")):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
