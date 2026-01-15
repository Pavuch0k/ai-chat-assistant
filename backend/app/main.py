from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api import chat, admin, admin_ui, knowledge
from app.db.database import engine, Base
import os

# Создаем таблицы при запуске
Base.metadata.create_all(bind=engine)

# Определяем путь для загрузок (локально или в Docker)
UPLOAD_DIR = os.getenv("UPLOAD_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads"))
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Монтируем директорию для загрузки файлов
app = FastAPI(title="AI Chat Assistant API", version="1.0.0")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(admin.router)
app.include_router(admin_ui.router)
app.include_router(knowledge.router)

@app.get("/")
async def root():
    return {"message": "AI Chat Assistant API"}

@app.get("/health")
async def health():
    return {"status": "ok"}
