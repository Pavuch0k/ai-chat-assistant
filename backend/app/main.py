from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.api import chat, admin, admin_ui, knowledge
from app.db.database import engine, Base
import os

# Создаем таблицы при запуске
Base.metadata.create_all(bind=engine)

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
app = FastAPI(
    title="AI Chat Assistant API",
    version="1.0.0",
    swagger_ui_parameters={
        "syntaxHighlight.theme": "agate",
        "persistAuthorization": True,
    }
)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Добавляем middleware для тёмной темы Swagger UI
app.add_middleware(SwaggerDarkThemeMiddleware)

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
