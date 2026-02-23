from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.api import chat, admin, admin_ui, knowledge, auth, projects
from app.db.database import engine, Base, get_db
from sqlalchemy import inspect, text
import os

# Создаем таблицы при запуске
Base.metadata.create_all(bind=engine)

# Создаем админа по умолчанию и дефолтный проект
from app.core.auth import create_default_admin
from app.models.db_models import Project, WidgetSettings
db = next(get_db())
try:
    create_default_admin(db)

    # Создаем дефолтный проект если его нет
    default_project = db.query(Project).filter(Project.id == 1).first()
    if not default_project:
        default_project = Project(
            id=1,
            name="Основной проект",
            description="Главный чат-ассистент для сайта",
            is_active=True
        )
        db.add(default_project)
        db.commit()
        print("✓ Создан дефолтный проект")

        # Создаем настройки виджета для дефолтного проекта
        default_settings = WidgetSettings(project_id=1)
        db.add(default_settings)
        db.commit()
        print("✓ Созданы настройки виджета для дефолтного проекта")
finally:
    db.close()

# Функция для проверки и добавления недостающих колонок
def ensure_database_schema():
    """Проверяет и добавляет недостающие колонки во все таблицы"""
    inspector = inspect(engine)

    # Миграция для widget_settings
    if 'widget_settings' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('widget_settings')]
        with engine.connect() as conn:
            widget_columns = {
                'background_color': "VARCHAR DEFAULT '#151b2e'",
                'header_color': "VARCHAR DEFAULT '#667eea'",
                'header_text_color': "VARCHAR DEFAULT '#ffffff'",
                'user_message_color': "VARCHAR DEFAULT '#667eea'",
                'bot_message_color': "VARCHAR DEFAULT '#1e2742'",
                'text_color': "VARCHAR DEFAULT '#e0e6ed'",
                'messages_area_color': "VARCHAR DEFAULT '#0a0e27'",
                'input_background_color': "VARCHAR DEFAULT '#0a0e27'",
                'border_color': "VARCHAR DEFAULT '#1e2742'",
                'welcome_message': "TEXT DEFAULT 'Привет! Чем могу помочь?'",
                'expanded_message_text': "VARCHAR DEFAULT 'Нужна помощь?'",
                'chat_title': "VARCHAR DEFAULT 'AI Ассистент'",
                'project_id': "INTEGER REFERENCES projects(id)"
            }
            for col_name, col_def in widget_columns.items():
                if col_name not in columns:
                    conn.execute(text(f"ALTER TABLE widget_settings ADD COLUMN {col_name} {col_def}"))
                    conn.commit()
                    print(f"✓ Добавлена колонка {col_name} в widget_settings")

    # Миграция для contacts
    if 'contacts' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('contacts')]
        with engine.connect() as conn:
            if 'project_id' not in columns:
                conn.execute(text("ALTER TABLE contacts ADD COLUMN project_id INTEGER REFERENCES projects(id)"))
                conn.commit()
                print("✓ Добавлена колонка project_id в contacts")
            if 'email' not in columns:
                conn.execute(text("ALTER TABLE contacts ADD COLUMN email VARCHAR"))
                conn.commit()
                print("✓ Добавлена колонка email в contacts")

    # Миграция для messages
    if 'messages' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('messages')]
        if 'project_id' not in columns:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE messages ADD COLUMN project_id INTEGER REFERENCES projects(id)"))
                conn.commit()
                print("✓ Добавлена колонка project_id в messages")

    # Миграция для documents
    if 'documents' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('documents')]
        if 'project_id' not in columns:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE documents ADD COLUMN project_id INTEGER REFERENCES projects(id)"))
                conn.commit()
                print("✓ Добавлена колонка project_id в documents")

# Вызываем функцию при старте
try:
    ensure_database_schema()
except Exception as e:
    print(f"Предупреждение при проверке схемы БД: {e}")

# Определяем путь для загрузок (локально или в Docker)
UPLOAD_DIR = os.getenv("UPLOAD_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads"))
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Кастомные стили для Swagger UI (тёмная тема)
SWAGGER_DARK_THEME = """
<style>
    body { background: #0a0e27 !important; }
    .swagger-ui { background: #0a0e27 !important; }
    .swagger-ui .topbar { display: none !important; }
    .swagger-ui .info { background: #151b2e !important; color: #e0e6ed !important; border: 1px solid #1e2742 !important; }
    .swagger-ui .info .title { color: #667eea !important; }
    .swagger-ui .scheme-container { background: #151b2e !important; border: 1px solid #1e2742 !important; }
    .swagger-ui .opblock { background: #151b2e !important; border: 1px solid #1e2742 !important; }
    .swagger-ui .opblock.opblock-post { border-left: 4px solid #667eea !important; }
    .swagger-ui .opblock.opblock-get { border-left: 4px solid #10b981 !important; }
    .swagger-ui .opblock.opblock-delete { border-left: 4px solid #ef4444 !important; }
    .swagger-ui .opblock.opblock-put { border-left: 4px solid #f59e0b !important; }
    .swagger-ui .opblock-tag { color: #e0e6ed !important; }
    .swagger-ui .opblock-summary { color: #e0e6ed !important; }
    .swagger-ui .opblock-description-wrapper { color: #8b95a7 !important; }
    .swagger-ui .parameter__name { color: #e0e6ed !important; }
    .swagger-ui .parameter__type { color: #667eea !important; }
    .swagger-ui .parameter__in { color: #8b95a7 !important; }
    .swagger-ui .response-col_status { color: #e0e6ed !important; }
    .swagger-ui .response-col_description { color: #8b95a7 !important; }
    .swagger-ui .model-box { background: #151b2e !important; border: 1px solid #1e2742 !important; }
    .swagger-ui .model-title { color: #667eea !important; }
    .swagger-ui .prop-name { color: #e0e6ed !important; }
    .swagger-ui .prop-type { color: #667eea !important; }
    .swagger-ui input[type=text], .swagger-ui input[type=password], .swagger-ui textarea { 
        background: #0a0e27 !important; 
        border: 1px solid #1e2742 !important; 
        color: #e0e6ed !important; 
    }
    .swagger-ui .btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important; color: white !important; border: none !important; }
    .swagger-ui .btn:hover { opacity: 0.9 !important; transform: translateY(-1px) !important; }
    .swagger-ui .response-content-type { color: #667eea !important; }
    .swagger-ui .highlight-code { background: #0a0e27 !important; }
    .swagger-ui .microlight { color: #e0e6ed !important; }
    .swagger-ui .renderedMarkdown p { color: #8b95a7 !important; }
    .swagger-ui .opblock-body { background: #0a0e27 !important; }
    .swagger-ui .opblock-section { background: #151b2e !important; border: 1px solid #1e2742 !important; }
    .swagger-ui .tab { background: #151b2e !important; color: #8b95a7 !important; border: 1px solid #1e2742 !important; }
    .swagger-ui .tab.active { background: #1e2742 !important; color: #667eea !important; border-color: #667eea !important; }
    .swagger-ui .btn.execute { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important; }
    .swagger-ui .response { background: #151b2e !important; border: 1px solid #1e2742 !important; }
    .swagger-ui .response .curl { background: #0a0e27 !important; color: #e0e6ed !important; }
    
    /* Мобильная адаптация */
    @media (max-width: 768px) {
        .swagger-ui .wrapper { padding: 10px !important; }
        .swagger-ui .info { margin: 10px 0 !important; padding: 15px !important; }
        .swagger-ui .opblock { margin: 10px 0 !important; }
        .swagger-ui .opblock-summary { padding: 10px !important; }
        .swagger-ui .opblock-body { padding: 15px !important; }
        .swagger-ui .parameter__name { font-size: 13px !important; }
        .swagger-ui .parameter__type { font-size: 12px !important; }
        .swagger-ui .btn { padding: 8px 16px !important; font-size: 13px !important; }
        .swagger-ui .scheme-container { padding: 10px !important; }
        .swagger-ui .opblock-tag { font-size: 18px !important; padding: 10px 0 !important; }
        .swagger-ui .opblock-description-wrapper { font-size: 13px !important; }
        .swagger-ui table { font-size: 12px !important; }
        .swagger-ui .model-title { font-size: 16px !important; }
        .swagger-ui .prop-name { font-size: 13px !important; }
        .swagger-ui .prop-type { font-size: 12px !important; }
    }
    
    @media (max-width: 480px) {
        .swagger-ui .wrapper { padding: 8px !important; }
        .swagger-ui .info { margin: 8px 0 !important; padding: 12px !important; }
        .swagger-ui .info .title { font-size: 20px !important; }
        .swagger-ui .opblock { margin: 8px 0 !important; }
        .swagger-ui .opblock-summary { padding: 8px !important; font-size: 13px !important; }
        .swagger-ui .opblock-body { padding: 12px !important; }
        .swagger-ui .parameter__name { font-size: 12px !important; }
        .swagger-ui .parameter__type { font-size: 11px !important; }
        .swagger-ui .btn { padding: 6px 12px !important; font-size: 12px !important; }
        .swagger-ui .scheme-container { padding: 8px !important; }
        .swagger-ui .opblock-tag { font-size: 16px !important; padding: 8px 0 !important; }
        .swagger-ui .opblock-description-wrapper { font-size: 12px !important; }
        .swagger-ui table { font-size: 11px !important; }
        .swagger-ui .model-title { font-size: 14px !important; }
        .swagger-ui .prop-name { font-size: 12px !important; }
        .swagger-ui .prop-type { font-size: 11px !important; }
        .swagger-ui input[type=text], .swagger-ui input[type=password], .swagger-ui textarea { 
            font-size: 14px !important; 
            padding: 8px !important; 
        }
        .swagger-ui .response-col_status { font-size: 12px !important; }
        .swagger-ui .response-col_description { font-size: 11px !important; }
    }
</style>
"""

class SwaggerDarkThemeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Пропускаем OPTIONS запросы без изменений (для CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)
        
        response = await call_next(request)
        if request.url.path == "/docs" and isinstance(response, HTMLResponse):
            body = await response.body()
            html = body.decode()
            # Вставляем стили перед закрывающим тегом </head>
            if "</head>" in html:
                html = html.replace("</head>", SWAGGER_DARK_THEME + "</head>")
                return HTMLResponse(content=html, status_code=response.status_code)
        return response

# Монтируем директорию для загрузки файлов
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)

app = FastAPI(
    title="Devorb AI API",
    version="1.0.0",
    swagger_ui_parameters={
        "syntaxHighlight.theme": "agate",
        "persistAuthorization": True,
    }
)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ВАЖНО: CORS middleware должен быть ПЕРВЫМ, чтобы обрабатывать preflight OPTIONS запросы
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Добавляем middleware для тёмной темы Swagger UI ПОСЛЕ CORS
app.add_middleware(SwaggerDarkThemeMiddleware)

app.include_router(chat.router)
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(admin_ui.router)
app.include_router(knowledge.router)
app.include_router(projects.router)

@app.get("/")
async def root():
    return {"message": "Devorb AI API"}

@app.get("/health")
async def health():
    return {"status": "ok"}
