from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.schemas import ChatRequest, ChatResponse
from app.services.ai_service import ai_service
from app.db.database import get_db
from app.models.db_models import Contact, Message
import re

router = APIRouter(prefix="/api", tags=["chat"])

def extract_contact_info(text: str) -> dict:
    """Извлечение контактной информации из текста"""
    contact = {}
    
    # Email
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    if emails:
        contact['email'] = emails[0]
    
    # Телефон
    phone_pattern = r'[\+]?[(]?[0-9]{1,4}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,9}'
    phones = re.findall(phone_pattern, text)
    if phones:
        contact['phone'] = phones[0].strip()
    
    # Имя (простая эвристика - слова с заглавной буквы в начале)
    name_pattern = r'\b[А-ЯЁA-Z][а-яёa-z]+\b'
    names = re.findall(name_pattern, text)
    if names and not contact.get('name'):
        # Берем первое подходящее слово как имя
        contact['name'] = names[0]
    
    return contact

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    # Извлекаем контактную информацию из сообщения
    contact_info = extract_contact_info(request.message)
    
    # Сохраняем или обновляем контакт
    contact = None
    if contact_info:
        # Ищем существующий контакт по email или телефону
        if contact_info.get('email'):
            contact = db.query(Contact).filter(Contact.email == contact_info['email']).first()
        elif contact_info.get('phone') and not contact:
            contact = db.query(Contact).filter(Contact.phone == contact_info['phone']).first()
        
        # Создаем новый контакт если не найден
        if not contact:
            contact = Contact(**contact_info)
            db.add(contact)
            db.commit()
            db.refresh(contact)
        else:
            # Обновляем существующий контакт
            for key, value in contact_info.items():
                if value and not getattr(contact, key):
                    setattr(contact, key, value)
            db.commit()
    
    # Получаем историю сообщений для контекста
    conversation_history = []
    if contact:
        messages = db.query(Message).filter(Message.contact_id == contact.id).order_by(Message.created_at).limit(10).all()
        for msg in messages:
            conversation_history.append({
                "role": "user" if msg.is_from_user else "assistant",
                "content": msg.message if msg.is_from_user else msg.response
            })
    
    # Получаем ответ от AI
    response_text = await ai_service.get_response(request.message, conversation_history)
    
    # Сохраняем сообщения в БД
    user_message = Message(
        contact_id=contact.id if contact else None,
        message=request.message,
        is_from_user=1
    )
    db.add(user_message)
    
    bot_message = Message(
        contact_id=contact.id if contact else None,
        message=request.message,
        response=response_text,
        is_from_user=0
    )
    db.add(bot_message)
    db.commit()
    
    return ChatResponse(response=response_text)
