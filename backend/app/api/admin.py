from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.db_models import Contact, Message, WidgetSettings
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/api/admin", tags=["admin"])

class ContactResponse(BaseModel):
    id: int
    name: Optional[str] = None
    phone: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    id: int
    contact_id: Optional[int] = None
    message: str
    response: Optional[str] = None
    is_from_user: int
    created_at: datetime
    
    class Config:
        from_attributes = True

@router.get("/contacts", response_model=List[ContactResponse])
async def get_contacts(db: Session = Depends(get_db)):
    """Получить список всех контактов"""
    contacts = db.query(Contact).order_by(Contact.created_at.desc()).all()
    return contacts

@router.get("/contacts/{contact_id}/messages", response_model=List[MessageResponse])
async def get_contact_messages(contact_id: int, db: Session = Depends(get_db)):
    """Получить историю сообщений контакта"""
    messages = db.query(Message).filter(Message.contact_id == contact_id).order_by(Message.created_at).all()
    return messages

@router.get("/messages", response_model=List[MessageResponse])
async def get_all_messages(db: Session = Depends(get_db), limit: int = 100):
    """Получить все сообщения"""
    messages = db.query(Message).order_by(Message.created_at.desc()).limit(limit).all()
    return messages

class WidgetSettingsRequest(BaseModel):
    primary_color: str = "#667eea"
    secondary_color: str = "#764ba2"
    button_color: str = "#667eea"
    message_color: str = "#667eea"
    background_color: str = "#151b2e"
    header_color: str = "#667eea"
    header_text_color: str = "#ffffff"
    user_message_color: str = "#667eea"
    bot_message_color: str = "#1e2742"
    text_color: str = "#e0e6ed"
    messages_area_color: str = "#0a0e27"
    input_background_color: str = "#0a0e27"
    border_color: str = "#1e2742"
    welcome_message: str = "Привет! Чем могу помочь?"
    expanded_message_text: str = "Нужна помощь?"

class WidgetSettingsResponse(BaseModel):
    primary_color: str
    secondary_color: str
    button_color: str
    message_color: str
    background_color: str
    header_color: str
    header_text_color: str
    user_message_color: str
    bot_message_color: str
    text_color: str
    messages_area_color: str
    input_background_color: str
    border_color: str
    welcome_message: str
    expanded_message_text: str
    
    class Config:
        from_attributes = True

@router.get("/widget/settings", response_model=WidgetSettingsResponse)
async def get_widget_settings(db: Session = Depends(get_db)):
    """Получить настройки виджета"""
    settings = db.query(WidgetSettings).first()
    if not settings:
        # Создаем настройки по умолчанию
        settings = WidgetSettings()
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings

@router.post("/widget/settings", response_model=WidgetSettingsResponse)
async def update_widget_settings(
    settings_data: WidgetSettingsRequest,
    db: Session = Depends(get_db)
):
    """Обновить настройки виджета"""
    settings = db.query(WidgetSettings).first()
    if not settings:
        settings = WidgetSettings()
        db.add(settings)
    
    settings.primary_color = settings_data.primary_color
    settings.secondary_color = settings_data.secondary_color
    settings.button_color = settings_data.button_color
    settings.message_color = settings_data.message_color
    settings.background_color = settings_data.background_color
    settings.header_color = settings_data.header_color
    settings.header_text_color = settings_data.header_text_color
    settings.user_message_color = settings_data.user_message_color
    settings.bot_message_color = settings_data.bot_message_color
    settings.text_color = settings_data.text_color
    settings.messages_area_color = settings_data.messages_area_color
    settings.input_background_color = settings_data.input_background_color
    settings.border_color = settings_data.border_color
    settings.welcome_message = settings_data.welcome_message
    settings.expanded_message_text = settings_data.expanded_message_text
    
    db.commit()
    db.refresh(settings)
    return settings

# Публичный endpoint для получения настроек виджета (без авторизации)
@router.get("/widget/settings/public", response_model=WidgetSettingsResponse)
async def get_widget_settings_public(db: Session = Depends(get_db)):
    """Получить настройки виджета (публичный endpoint)"""
    settings = db.query(WidgetSettings).first()
    if not settings:
        # Создаем настройки по умолчанию
        settings = WidgetSettings()
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings
