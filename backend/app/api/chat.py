from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.schemas import ChatRequest, ChatResponse
from app.services.ai_service import ai_service
from app.services.bitrix24_service import bitrix24_service
from app.db.database import get_db
from app.models.db_models import Contact, Message
import re
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])

def extract_contact_info(text: str) -> dict:
    """Извлечение контактной информации из текста"""
    contact = {}
    
    # Телефон - строгая валидация
    # Российские номера: +7, 8, или начинается с 7/8, затем 10 цифр
    phone_pattern = r'(?:\+?7|8)?[\s\-\(]?(\d{3})[\s\-\)]?(\d{3})[\s\-]?(\d{2})[\s\-]?(\d{2})'
    phones = re.findall(phone_pattern, text)
    if phones:
        # Собираем номер из групп
        phone_digits = ''.join(phones[0])
        # Валидация: должно быть 10 цифр (без кода страны)
        if len(phone_digits) == 10 and phone_digits.isdigit():
            # Проверяем, что это не случайные цифры (например, не все одинаковые)
            if len(set(phone_digits)) > 2:  # Хотя бы 3 разные цифры
                contact['phone'] = phone_digits
    
    # Имя - улучшенное распознавание с исключением служебных слов
    # Список служебных слов, которые НЕ являются именами
    exclude_words = {
        'привет', 'здравствуйте', 'добрый', 'день', 'вечер', 'утро', 'ночь',
        'меня', 'зовут', 'это', 'мое', 'имя', 'я', 'меня', 'как', 'вас',
        'ваше', 'ваш', 'вами', 'помочь', 'помощь', 'вопрос', 'вопросы',
        'спасибо', 'пожалуйста', 'да', 'нет', 'хорошо', 'ок', 'окей',
        'нужно', 'нужен', 'нужна', 'хочу', 'хотел', 'хотела', 'можно',
        'скажите', 'подскажите', 'расскажите', 'помогите', 'помоги',
        'интересует', 'интересует', 'интересно', 'что', 'кто', 'где',
        'когда', 'почему', 'как', 'сколько', 'какой', 'какая', 'какое'
    }
    
    # Паттерны для извлечения имени
    name_patterns = [
        # "меня зовут Иван", "я Иван", "это Иван"
        r'(?:меня\s+зовут|я\s+|это\s+|мое\s+имя\s+)([А-ЯЁ][а-яё]{2,})',
        # "Иван - это я", "Иван это меня"
        r'([А-ЯЁ][а-яё]{2,})\s+(?:это\s+)?(?:меня|я)',
    ]
    
    for pattern in name_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            for match in matches:
                name = match.strip().lower()
                # Проверяем, что это не служебное слово
                if name not in exclude_words and len(name) >= 3:
                    # Капитализируем первую букву
                    contact['name'] = name.capitalize()
                    break
            if contact.get('name'):
                break
    
    # Если не нашли по паттернам, ищем просто имя с заглавной (но только если это не служебное слово)
    if not contact.get('name'):
        # Ищем слова с заглавной буквы, но исключаем начало предложения
        words = re.findall(r'\b[А-ЯЁ][а-яё]{2,}\b', text)
        for word in words:
            word_lower = word.lower()
            if word_lower not in exclude_words and len(word) >= 3:
                # Дополнительная проверка: не должно быть в начале предложения как приветствие
                word_pos = text.lower().find(word_lower)
                if word_pos > 0:  # Не в начале текста
                    contact['name'] = word
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
    contact_was_updated = False
    should_send_to_bitrix = False
    
    if contact:
        if contact_info:
            # Проверяем, были ли у контакта имя и телефон до обновления
            had_both_before = bool(contact.name and contact.phone)
            
            for key, value in contact_info.items():
                if value and not getattr(contact, key):
                    setattr(contact, key, value)
                    contact_was_updated = True
            
            if contact_was_updated:
                db.commit()
                db.refresh(contact)
                # Отправляем в Bitrix24 только если теперь есть оба поля, а раньше не было
                if not had_both_before and contact.name and contact.phone:
                    should_send_to_bitrix = True
    elif contact_info:
        # Ищем существующий контакт по телефону
        if contact_info.get('phone'):
            contact = db.query(Contact).filter(Contact.phone == contact_info['phone']).first()
        
        # Создаем новый контакт если не найден
        if not contact:
            contact = Contact(**contact_info)
            db.add(contact)
            db.commit()
            db.refresh(contact)
            contact_was_updated = True
            # Отправляем в Bitrix24 если есть оба поля
            if contact.name and contact.phone:
                should_send_to_bitrix = True
        else:
            # Проверяем, были ли у контакта имя и телефон до обновления
            had_both_before = bool(contact.name and contact.phone)
            
            # Обновляем существующий контакт
            for key, value in contact_info.items():
                if value and not getattr(contact, key):
                    setattr(contact, key, value)
                    contact_was_updated = True
            
            if contact_was_updated:
                db.commit()
                db.refresh(contact)
                # Отправляем в Bitrix24 только если теперь есть оба поля, а раньше не было
                if not had_both_before and contact.name and contact.phone:
                    should_send_to_bitrix = True
    
    # Отправляем контакт в Bitrix24, если нужно
    if should_send_to_bitrix and contact and contact.name and contact.phone:
        try:
            result = await bitrix24_service.create_lead(
                name=contact.name,
                phone=contact.phone,
                comments=f"Контакт создан из AI Chat Widget. Session ID: {session_id}"
            )
            if result.get("success"):
                logger.info(f"Контакт {contact.name} ({contact.phone}) успешно отправлен в Bitrix24 (Lead ID: {result.get('lead_id')})")
            else:
                logger.warning(f"Не удалось отправить контакт в Bitrix24: {result.get('error')}")
        except Exception as e:
            logger.error(f"Ошибка при отправке контакта в Bitrix24: {str(e)}", exc_info=True)
    
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
    
    # Формируем информацию о собранных контактах для промпта
    contact_status = ""
    if contact:
        has_name = bool(contact.name)
        has_phone = bool(contact.phone)
        if has_name and has_phone:
            contact_status = f"\n\nВАЖНО: Контакты клиента УЖЕ СОБРАНЫ:\n- Имя: {contact.name}\n- Телефон: {contact.phone}\nНЕ ПРОСИ эти данные снова! Просто помогай по вопросам."
        elif has_name:
            contact_status = f"\n\nВАЖНО: Имя клиента уже известно: {contact.name}. Нужно собрать только номер телефона."
        elif has_phone:
            contact_status = f"\n\nВАЖНО: Телефон клиента уже известен: {contact.phone}. Нужно собрать только имя."
    
    # Получаем ответ от AI с учетом истории и статуса контактов
    response_text = await ai_service.get_response(request.message, conversation_history, contact_status)
    
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
