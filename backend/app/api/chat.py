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
    import uuid
    
    # Генерируем session_id если не передан
    session_id = request.session_id or str(uuid.uuid4())
    
    # СНАЧАЛА получаем историю сообщений для извлечения контактов из всего разговора
    previous_messages = db.query(Message).filter(Message.session_id == session_id).order_by(Message.created_at).all()
    
    # Ищем существующий контакт по session_id из предыдущих сообщений
    contact = None
    if previous_messages:
        # Ищем контакт из предыдущих сообщений этой сессии
        for msg in previous_messages:
            if msg.contact_id:
                contact = db.query(Contact).filter(Contact.id == msg.contact_id).first()
                if contact:
                    break
    
    # Извлекаем контактную информацию из текущего сообщения И из истории
    contact_info = extract_contact_info(request.message)
    
    # Также извлекаем из истории разговора
    full_conversation_text = request.message
    for msg in previous_messages:
        if msg.is_from_user and msg.message:
            full_conversation_text += " " + msg.message
    
    history_contact_info = extract_contact_info(full_conversation_text)
    
    # Объединяем информацию (приоритет текущему сообщению)
    if history_contact_info:
        for key, value in history_contact_info.items():
            if value and not contact_info.get(key):
                contact_info[key] = value
    
    # Если нашли контакт из сессии, обновляем его данными
    if contact:
        if contact_info:
            for key, value in contact_info.items():
                if value and not getattr(contact, key):
                    setattr(contact, key, value)
            db.commit()
            db.refresh(contact)
    elif contact_info:
        # Ищем существующий контакт по email или телефону
        if contact_info.get('email'):
            contact = db.query(Contact).filter(Contact.email == contact_info['email']).first()
        elif contact_info.get('phone'):
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
            db.refresh(contact)
    
    # Если есть контакт, обновляем все сообщения этой сессии на этот контакт
    if contact:
        db.query(Message).filter(Message.session_id == session_id, Message.contact_id == None).update(
            {"contact_id": contact.id}
        )
        db.commit()
    
    # Получаем историю сообщений для контекста
    conversation_history = []
    if contact:
        # Берем последние 50 сообщений этого контакта
        messages = db.query(Message).filter(Message.contact_id == contact.id).order_by(Message.created_at).limit(50).all()
    else:
        # Если контакта нет, берем сообщения по session_id
        messages = db.query(Message).filter(Message.session_id == session_id).order_by(Message.created_at).limit(50).all()
    
    # Формируем историю разговора (ВАЖНО: исключаем текущее сообщение, оно еще не сохранено)
    for msg in messages:
        if msg.is_from_user:
            conversation_history.append({
                "role": "user",
                "content": msg.message
            })
        else:
            conversation_history.append({
                "role": "assistant",
                "content": msg.response or ""
            })
    
    # Получаем ответ от AI с учетом истории
    response_text = await ai_service.get_response(request.message, conversation_history)
    
    # Сохраняем сообщения в БД с session_id
    user_message = Message(
        contact_id=contact.id if contact else None,
        session_id=session_id,
        message=request.message,
        is_from_user=1
    )
    db.add(user_message)
    
    bot_message = Message(
        contact_id=contact.id if contact else None,
        session_id=session_id,
        message=request.message,
        response=response_text,
        is_from_user=0
    )
    db.add(bot_message)
    db.commit()
    
    return ChatResponse(response=response_text, session_id=session_id)
