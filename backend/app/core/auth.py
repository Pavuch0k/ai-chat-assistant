import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.db_models import AdminUser

# Простая сессионная система вместо JWT для упрощения
# Хранение активных сессий в памяти (в продакшене лучше использовать Redis)
active_sessions = {}

security = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    """Хеширование пароля с солью"""
    salt = os.urandom(32)
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return (salt + pwdhash).hex()

def verify_password(stored_password: str, provided_password: str) -> bool:
    """Проверка пароля"""
    stored_password_bytes = bytes.fromhex(stored_password)
    salt = stored_password_bytes[:32]
    stored_hash = stored_password_bytes[32:]
    pwdhash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
    return pwdhash == stored_hash

def create_session(username: str) -> str:
    """Создание новой сессии"""
    session_token = secrets.token_urlsafe(32)
    active_sessions[session_token] = {
        'username': username,
        'created_at': datetime.utcnow(),
        'expires_at': datetime.utcnow() + timedelta(days=7)
    }
    return session_token

def validate_session(session_token: str) -> Optional[dict]:
    """Проверка валидности сессии"""
    if session_token not in active_sessions:
        return None

    session = active_sessions[session_token]
    if datetime.utcnow() > session['expires_at']:
        del active_sessions[session_token]
        return None

    return session

def delete_session(session_token: str):
    """Удаление сессии (logout)"""
    if session_token in active_sessions:
        del active_sessions[session_token]

async def get_current_user(
    session_token: Optional[str] = Cookie(None, alias="admin_session"),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> AdminUser:
    """Получение текущего пользователя из сессии"""
    # Пытаемся получить токен из куки или заголовка Authorization
    token = session_token
    if not token and credentials:
        token = credentials.credentials

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не авторизован",
            headers={"WWW-Authenticate": "Bearer"},
        )

    session = validate_session(token)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Сессия истекла",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(AdminUser).filter(AdminUser.username == session['username']).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден или неактивен",
        )

    return user

def create_default_admin(db: Session):
    """Создание администратора по умолчанию, если нет пользователей"""
    existing_user = db.query(AdminUser).first()
    if not existing_user:
        default_user = AdminUser(
            username="admin",
            hashed_password=hash_password("admin123"),  # ИЗМЕНИТЬ при первом входе!
            is_active=True
        )
        db.add(default_user)
        db.commit()
        print("✓ Создан администратор по умолчанию: admin / admin123")
        print("⚠️  ВАЖНО: Смените пароль после первого входа!")
