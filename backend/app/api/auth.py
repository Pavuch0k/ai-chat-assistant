from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.database import get_db
from app.models.db_models import AdminUser
from app.core.auth import (
    verify_password,
    hash_password,
    create_session,
    delete_session,
    get_current_user
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    message: str
    session_token: str = None

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, response: Response, db: Session = Depends(get_db)):
    """Вход в систему"""
    user = db.query(AdminUser).filter(AdminUser.username == request.username).first()

    if not user or not verify_password(user.hashed_password, request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Учетная запись отключена"
        )

    # Создаем сессию
    session_token = create_session(user.username)

    # Устанавливаем cookie
    response.set_cookie(
        key="admin_session",
        value=session_token,
        httponly=True,
        max_age=7 * 24 * 60 * 60,  # 7 дней
        samesite="lax"
    )

    return LoginResponse(
        success=True,
        message="Вход выполнен успешно",
        session_token=session_token
    )

@router.post("/logout")
async def logout(
    response: Response,
    current_user: AdminUser = Depends(get_current_user)
):
    """Выход из системы"""
    # Удаляем cookie
    response.delete_cookie(key="admin_session")
    return {"success": True, "message": "Выход выполнен успешно"}

@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Смена пароля"""
    # Проверяем текущий пароль
    if not verify_password(current_user.hashed_password, request.current_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный текущий пароль"
        )

    # Проверяем длину нового пароля
    if len(request.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пароль должен содержать минимум 6 символов"
        )

    # Обновляем пароль
    current_user.hashed_password = hash_password(request.new_password)
    db.commit()

    return {"success": True, "message": "Пароль успешно изменен"}

@router.get("/check")
async def check_auth(current_user: AdminUser = Depends(get_current_user)):
    """Проверка авторизации"""
    return {
        "authenticated": True,
        "username": current_user.username
    }
