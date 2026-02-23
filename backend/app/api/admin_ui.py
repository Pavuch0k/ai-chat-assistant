from fastapi import APIRouter, Depends, Response, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from app.models.db_models import AdminUser
from app.core.auth import get_current_user, validate_session
from typing import Optional

router = APIRouter(tags=["admin-ui"])

@router.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page():
    """Страница входа в админку"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Вход - Devorb AI</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            .login-container {
                background: #1a1625;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
                padding: 48px;
                width: 100%;
                max-width: 420px;
                border: 1px solid #2a2436;
            }
            h1 {
                color: #e0e6ed;
                margin-bottom: 12px;
                font-size: 32px;
                font-weight: 700;
                text-align: center;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            .subtitle {
                color: #8b95a7;
                text-align: center;
                margin-bottom: 32px;
                font-size: 14px;
            }
            .form-group {
                margin-bottom: 24px;
            }
            label {
                display: block;
                color: #8b95a7;
                margin-bottom: 8px;
                font-size: 14px;
                font-weight: 500;
            }
            input {
                width: 100%;
                padding: 14px 16px;
                background: #0f0c15;
                border: 2px solid #2a2436;
                border-radius: 12px;
                color: #e0e6ed;
                font-size: 15px;
                transition: all 0.3s;
            }
            input:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            button {
                width: 100%;
                padding: 14px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            }
            button:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
            }
            button:active {
                transform: translateY(0);
            }
            button:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }
            .error {
                background: rgba(239, 68, 68, 0.1);
                border: 1px solid rgba(239, 68, 68, 0.3);
                color: #ef4444;
                padding: 12px 16px;
                border-radius: 12px;
                margin-bottom: 24px;
                font-size: 14px;
                display: none;
            }
            .error.show {
                display: block;
            }
        </style>
    </head>
    <body>
        <div class="login-container">
            <h1>Devorb AI</h1>
            <p class="subtitle">Вход в панель управления</p>
            <div id="error" class="error"></div>
            <form id="loginForm">
                <div class="form-group">
                    <label for="username">Имя пользователя</label>
                    <input type="text" id="username" name="username" required autocomplete="username">
                </div>
                <div class="form-group">
                    <label for="password">Пароль</label>
                    <input type="password" id="password" name="password" required autocomplete="current-password">
                </div>
                <button type="submit" id="submitBtn">Войти</button>
            </form>
        </div>
        <script>
            const form = document.getElementById('loginForm');
            const errorDiv = document.getElementById('error');
            const submitBtn = document.getElementById('submitBtn');

            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                errorDiv.classList.remove('show');
                submitBtn.disabled = true;
                submitBtn.textContent = 'Вход...';

                const username = document.getElementById('username').value;
                const password = document.getElementById('password').value;

                try {
                    const response = await fetch(window.location.origin + '/api/auth/login', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        credentials: 'same-origin',
                        body: JSON.stringify({ username, password })
                    });

                    const data = await response.json();

                    if (response.ok && data.success) {
                        window.location.href = '/admin';
                    } else {
                        errorDiv.textContent = data.detail || 'Ошибка входа';
                        errorDiv.classList.add('show');
                    }
                } catch (error) {
                    errorDiv.textContent = 'Ошибка подключения к серверу';
                    errorDiv.classList.add('show');
                } finally {
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Войти';
                }
            });
        </script>
    </body>
    </html>
    """)

@router.get("/admin", response_class=HTMLResponse)
async def admin_panel(session_token: Optional[str] = Cookie(None, alias="admin_session")):
    """Админ панель с SPA архитектурой"""
    import os
    # Проверяем авторизацию
    if not session_token or not validate_session(session_token):
        return RedirectResponse(url="/admin/login", status_code=303)

    # Возвращаем SPA приложение
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
    admin_html_path = os.path.join(static_dir, "admin.html")
    return HTMLResponse(content=open(admin_html_path, 'r', encoding='utf-8').read())
