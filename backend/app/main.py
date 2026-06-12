from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import UPLOAD_DIR
from .database import Base, engine
from .models.recipe import Category, Recipe
from .routers import categories, chat, images, recipes

app = FastAPI(title="菜谱网站 API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recipes.router)
app.include_router(categories.router)
app.include_router(images.router)
app.include_router(chat.router)


Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
app.mount("/api/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

    from .database import SessionLocal

    db = SessionLocal()
    try:
        if db.query(Category).count() == 0:
            defaults = [
                Category(name="家常菜", icon="🍳"),
                Category(name="汤羹", icon="🍲"),
                Category(name="快手菜", icon="⚡"),
                Category(name="甜品", icon="🍰"),
                Category(name="凉菜", icon="🥗"),
                Category(name="主食", icon="🍚"),
                Category(name="烧烤", icon="🔥"),
                Category(name="饮品", icon="🥤"),
            ]
            db.add_all(defaults)
            db.commit()
    finally:
        db.close()


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
