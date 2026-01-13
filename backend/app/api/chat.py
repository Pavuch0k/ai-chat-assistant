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
    
    # Телефон (улучшенный паттерн)
    phone_pattern = r'[\+]?[7-8]?[\s\-\(]?[0-9]{3}[\s\-\)]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}|[\+]?[0-9]{10,15}'
    phones = re.findall(phone_pattern, text)
    if phones:
        # Очищаем телефон от лишних символов
        phone = re.sub(r'[\s\-\(\)]', '', phones[0])
        if len(phone) >= 10:
            contact['phone'] = phone
    
    # Имя - улучшенное распознавание
    # Паттерны: "меня зовут X", "я X", "это X", "X - мое имя"
    name_patterns = [
        r'(?:меня\s+зовут|я\s+|это\s+|мое\s+имя\s+)[А-ЯЁA-Z][а-яёa-z]+',
        r'[А-ЯЁA-Z][а-яёa-z]+\s+(?:это\s+)?(?:меня|я)',
        r'\b[А-ЯЁA-Z][а-яёa-z]{2,}\b'  # Просто имя с заглавной буквы
    ]
    
    for pattern in name_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            # Берем первое подходящее слово, исключая служебные
            exclude_words = ['Меня', 'Зовут', 'Это', 'Мое', 'Имя', 'Я', 'Меня']
            for match in matches:
                name = re.sub(r'^(?:меня\s+зовут|я\s+|это\s+|мое\s+имя\s+)', '', match, flags=re.IGNORECASE).strip()
                name = re.sub(r'\s+(?:это\s+)?(?:меня|я)$', '', name, flags=re.IGNORECASE).strip()
                if name and name not in exclude_words and len(name) > 2:
                    contact['name'] = name
                    break
            if contact.get('name'):
                break
    
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
    
    # Получаем историю сообщений для контекста (увеличиваем лимит для полного контекста)
    conversation_history = []
    if contact:
        # Берем последние 50 сообщений для полного контекста
        messages = db.query(Message).filter(Message.contact_id == contact.id).order_by(Message.created_at).limit(50).all()
        for msg in messages:
            conversation_history.append({
                "role": "user" if msg.is_from_user else "assistant",
                "content": msg.message if msg.is_from_user else msg.response
            })
    else:
        # Если контакта нет, ищем по последним сообщениям без контакта (для анонимных пользователей)
        recent_messages = db.query(Message).filter(Message.contact_id == None).order_by(Message.created_at.desc()).limit(50).all()
        # Переворачиваем для правильного порядка
        recent_messages.reverse()
        for msg in recent_messages:
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
