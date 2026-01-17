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
    # Расширенный список служебных слов, которые НЕ являются именами
    exclude_words = {
        # Приветствия и обращения
        'привет', 'здравствуйте', 'добрый', 'день', 'вечер', 'утро', 'ночь',
        # Местоимения и служебные слова
        'меня', 'зовут', 'это', 'мое', 'имя', 'я', 'как', 'вас', 'ваше', 'ваш', 'вами',
        # Глаголы и действия
        'помочь', 'помощь', 'вопрос', 'вопросы', 'скажите', 'подскажите', 'расскажите', 
        'помогите', 'помоги', 'интересует', 'интересно',
        # Предлоги и союзы (расширенный список)
        'для', 'от', 'к', 'на', 'в', 'с', 'по', 'за', 'под', 'над', 'при', 'про', 'без', 'из', 'до', 'со', 'об', 'во',
        'что', 'кто', 'где', 'когда', 'почему', 'как', 'сколько', 'какой', 'какая', 'какое',
        # Другие служебные слова
        'спасибо', 'пожалуйста', 'да', 'нет', 'хорошо', 'ок', 'окей',
        'нужно', 'нужен', 'нужна', 'хочу', 'хотел', 'хотела', 'можно',
        # Слова связанные с обучением/услугами
        'цена', 'стоимость', 'обучение', 'ребенка', 'детей', 'занятие', 'занятий',
        'формат', 'группа', 'индивидуально', 'курс', 'курсы'
    }
    
    # Паттерны для извлечения имени (приоритетные - более точные)
    name_patterns = [
        # "меня зовут Иван", "я Иван", "это Иван", "мое имя Иван"
        r'(?:меня\s+зовут|я\s+|это\s+|мое\s+имя\s+|зовут\s+)([А-ЯЁ][а-яё]{2,})',
        # "Иван - это я", "Иван это меня", "Иван, это я"
        r'([А-ЯЁ][а-яё]{2,})\s*[,\-]?\s*(?:это\s+)?(?:меня|я)',
        # "Влад 89371234378" - имя перед телефоном
        r'([А-ЯЁ][а-яё]{2,})\s+(?:\+?7|8)\d{10}',
        # "Имя: Иван" или "Имя Иван"
        r'(?:имя|зовут)[\s:]+([А-ЯЁ][а-яё]{2,})',
    ]
    
    # Сначала ищем по точным паттернам
    for pattern in name_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            for match in matches:
                name = match.strip()
                name_lower = name.lower()
                # Проверяем, что это не служебное слово и длина достаточна
                if name_lower not in exclude_words and len(name) >= 3:
                    # Капитализируем первую букву
                    contact['name'] = name.capitalize()
                    break
            if contact.get('name'):
                break
    
    # Если не нашли по паттернам, ищем имя в начале сообщения (если оно короткое и простое)
    if not contact.get('name'):
        # Ищем слова с заглавной буквы в начале строки или после точки/запятой
        # Но только если текст короткий (до 50 символов) - это может быть просто "Имя Телефон"
        if len(text.strip()) < 50:
            words = re.findall(r'\b[А-ЯЁ][а-яё]{2,}\b', text)
            for word in words:
                word_lower = word.lower()
                if word_lower not in exclude_words and len(word) >= 3:
                    # Проверяем, что это не в середине фразы типа "для ребенка"
                    # Ищем контекст - если перед словом есть предлог, пропускаем
                    word_pos = text.lower().find(word_lower)
                    if word_pos > 0:
                        # Проверяем, что перед словом нет предлога
                        before_word = text[max(0, word_pos-10):word_pos].lower().strip()
                        has_preposition_before = any(before_word.endswith(prep) for prep in ['для', 'от', 'к', 'на', 'в', 'с', 'по', 'за'])
                        if not has_preposition_before:
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
    
    # СНАЧАЛА получаем ответ от ИИ, чтобы использовать данные из него (приоритет #1)
    # Формируем историю разговора для ИИ (из previous_messages)
    conversation_history_for_ai = []
    for msg in previous_messages:
        if msg.is_from_user:
            conversation_history_for_ai.append({
                "role": "user",
                "content": msg.message
            })
        else:
            conversation_history_for_ai.append({
                "role": "assistant",
                "content": msg.response or ""
            })
    
    # Формируем информацию о собранных контактах для промпта
    contact_status_for_ai = ""
    if contact:
        has_name = bool(contact.name)
        has_phone = bool(contact.phone)
        if has_name and has_phone:
            contact_status_for_ai = f"\n\nВАЖНО: Контакты клиента УЖЕ СОБРАНЫ:\n- Имя: {contact.name}\n- Телефон: {contact.phone}\nНЕ ПРОСИ эти данные снова! Просто помогай по вопросам."
        elif has_name:
            contact_status_for_ai = f"\n\nВАЖНО: Имя клиента уже известно: {contact.name}. Нужно собрать только номер телефона."
        elif has_phone:
            contact_status_for_ai = f"\n\nВАЖНО: Телефон клиента уже известен: {contact.phone}. Нужно собрать только имя."
    
    # Получаем ответ от AI с учетом истории и статуса контактов
    # ВАЖНО: делаем это ДО создания/обновления контакта, чтобы использовать данные из ответа ИИ
    response_text, ai_extracted_name, ai_extracted_phone = await ai_service.get_response(request.message, conversation_history_for_ai, contact_status_for_ai)
    
    # Инициализируем contact_info ТОЛЬКО данными от ИИ (приоритет #1, без проверок)
    contact_info = {}
    
    # Если ИИ извлек имя из ответа, используем его БЕЗ проверок (ИИ сам решает)
    if ai_extracted_name and ai_extracted_name not in ["0", ""]:
        contact_info['name'] = ai_extracted_name.capitalize()
        logger.info(f"Имя извлечено ИИ: {contact_info['name']}")
    
    # Если ИИ извлек телефон из ответа, используем его БЕЗ проверок (ИИ сам решает)
    if ai_extracted_phone and ai_extracted_phone not in ["0", ""]:
        # Нормализуем телефон (убираем +7 или 8 в начале, оставляем 10 цифр)
        phone_digits = ''.join(filter(str.isdigit, ai_extracted_phone))
        if phone_digits.startswith('7') and len(phone_digits) == 11:
            phone_digits = phone_digits[1:]  # Убираем 7 в начале
        elif phone_digits.startswith('8') and len(phone_digits) == 11:
            phone_digits = phone_digits[1:]  # Убираем 8 в начале
        elif len(phone_digits) == 10:
            pass  # Уже правильный формат
        else:
            phone_digits = phone_digits[-10:] if len(phone_digits) >= 10 else phone_digits
        
        if len(phone_digits) == 10 and phone_digits.isdigit():
            contact_info['phone'] = phone_digits
            logger.info(f"Телефон извлечен ИИ: {contact_info['phone']}")
    
    # Если ИИ не нашел данные - ничего не делаем, он найдет позже
    
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
            # Генерируем краткое резюме диалога для CRM
            # Формируем историю из предыдущих сообщений для резюме
            summary_history = []
            for msg in previous_messages:
                if msg.is_from_user:
                    summary_history.append({
                        "role": "user",
                        "content": msg.message
                    })
                else:
                    summary_history.append({
                        "role": "assistant",
                        "content": msg.response or ""
                    })
            # Добавляем текущее сообщение
            summary_history.append({
                "role": "user",
                "content": request.message
            })
            conversation_summary = await ai_service.generate_conversation_summary(summary_history)
            
            # Формируем комментарий для Bitrix24
            if conversation_summary:
                comments = f"Краткое резюме диалога:\n{conversation_summary}\n\nSession ID: {session_id}"
            else:
                # Если резюме нет (диалог только начался), просто указываем Session ID
                comments = f"Контакт создан из AI Chat Widget. Session ID: {session_id}"
            
            result = await bitrix24_service.create_lead(
                name=contact.name,
                phone=contact.phone,
                comments=comments
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
    # ВАЖНО: это второй вызов для сохранения ответа в БД, но данные из ИИ уже использованы выше
    response_text, _, _ = await ai_service.get_response(request.message, conversation_history, contact_status)
    
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
