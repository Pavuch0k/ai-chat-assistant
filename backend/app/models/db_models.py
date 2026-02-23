from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    # API секреты
    openai_api_key = Column(String, nullable=True)
    bitrix_webhook_url = Column(String, nullable=True)
    custom_webhook_url = Column(String, nullable=True)

    # CORS настройки (JSON строка со списком доменов)
    allowed_origins = Column(Text, default="*")

    # Docker контейнер (для будущего использования)
    container_id = Column(String, nullable=True)
    container_port = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True, index=True)  # nullable для обратной совместимости
    name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True, index=True)
    contact_id = Column(Integer, nullable=True)
    session_id = Column(String, nullable=True, index=True)  # Для связывания сообщений одного пользователя
    message = Column(Text)
    response = Column(Text)
    is_from_user = Column(Integer, default=1)  # 1 - от пользователя, 0 - от бота
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True, index=True)
    name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class WidgetSettings(Base):
    __tablename__ = "widget_settings"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True, index=True, unique=True)  # Один набор настроек на проект
    primary_color = Column(String, default="#667eea")
    secondary_color = Column(String, default="#764ba2")
    button_color = Column(String, default="#667eea")
    message_color = Column(String, default="#667eea")
    background_color = Column(String, default="#151b2e")
    header_color = Column(String, default="#667eea")
    header_text_color = Column(String, default="#ffffff")
    user_message_color = Column(String, default="#667eea")
    bot_message_color = Column(String, default="#1e2742")
    text_color = Column(String, default="#e0e6ed")
    messages_area_color = Column(String, default="#0a0e27")
    input_background_color = Column(String, default="#0a0e27")
    border_color = Column(String, default="#1e2742")
    welcome_message = Column(Text, default="Привет! Чем могу помочь?")
    expanded_message_text = Column(String, default="Нужна помощь?")
    chat_title = Column(String, default="AI Ассистент")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
