import os
import httpx
from app.core.config import settings
from app.services.knowledge_service import knowledge_service
from typing import Optional

class AIService:
    def __init__(self):
        self.api_key = settings.openai_api_key
        self.base_url = "https://api.openai.com/v1"
        # Настройка прокси
        if settings.openai_proxy_url and settings.openai_proxy_username and settings.openai_proxy_password:
            # Формат: http://username:password@host:port
            proxy_host = settings.openai_proxy_url.replace("http://", "").replace("https://", "")
            self.proxy_url = f"http://{settings.openai_proxy_username}:{settings.openai_proxy_password}@{proxy_host}"
        else:
            self.proxy_url = None
    
    async def get_response(self, message: str, conversation_history: list = None, contact_status: str = "") -> tuple[str, str, str]:
        """
        Получить ответ от OpenAI с использованием базы знаний
        
        Returns:
            tuple: (response_text, extracted_name, extracted_phone) где:
                - response_text - ответ ИИ
                - extracted_name - имя из ответа ИИ или пустая строка
                - extracted_phone - телефон из ответа ИИ или пустая строка
        """
        if conversation_history is None:
            conversation_history = []
        
        # Ищем релевантную информацию в базе знаний
        knowledge_context = ""
        search_results = knowledge_service.search(message, limit=10)  # Увеличиваем лимит до 10
        if search_results:
            print(f"Найдено {len(search_results)} релевантных фрагментов из базы знаний")
            knowledge_context = "\n\nВАЖНО: Используй ТОЛЬКО информацию из базы знаний ниже для ответа. Если информация есть в базе знаний, обязательно используй её:\n"
            for i, result in enumerate(search_results, 1):
                score = result.get('score', 0)
                text = result['text'][:500]  # Ограничиваем длину для логов
                print(f"  Фрагмент {i} (score: {score:.3f}): {text[:100]}...")
                knowledge_context += f"{i}. {result['text']}\n"
            knowledge_context += "\nЕсли в базе знаний есть информация по запросу пользователя, ОБЯЗАТЕЛЬНО используй её в ответе!"
        else:
            print(f"Поиск в базе знаний не вернул результатов для запроса: {message[:100]}")
        
        system_prompt = """Ты дружелюбный ассистент службы поддержки. 

Твоя главная задача - помочь клиенту И собрать его контактные данные (имя и номер телефона).

КРИТИЧЕСКИ ВАЖНЫЕ ПРАВИЛА:

1. ИСПОЛЬЗОВАНИЕ БАЗЫ ЗНАНИЙ:
   - Если в базе знаний есть информация по запросу - используй ТОЛЬКО её, дословно
   - НЕ выдумывай информацию, которой нет в базе знаний
   - НЕ смешивай информацию про разных людей - если спрашивают про "Karena Zhou", отвечай ТОЛЬКО про Karena Zhou, не упоминай других людей
   - Если в базе знаний есть несколько фрагментов про одного человека - объединяй их, но не путай с другими людьми

2. СБОР КОНТАКТОВ - КРИТИЧЕСКИ ВАЖНО (ПРИОРИТЕТ #1):
   - Если контакты УЖЕ собраны (имя и телефон есть) - НЕ проси их снова, просто помогай по вопросам
   - Если НЕТ имени ИЛИ телефона - ВСЕГДА вежливо проси недостающие данные в КАЖДОМ ответе, пока не соберешь оба
   - Если есть только имя - вежливо попроси номер телефона в КАЖДОМ ответе, пока не получишь
   - Если есть только телефон - вежливо попроси имя в КАЖДОМ ответе, пока не получишь
   - Если ничего нет - вежливо проси имя и телефон в КАЖДОМ ответе, пока не соберешь оба
   - В ПЕРВОМ ответе клиенту ОБЯЗАТЕЛЬНО спроси имя и телефон, если их еще нет
   - НЕ прекращай просить контакты, пока не получишь И имя И телефон
   - Даже отвечая на вопросы, ВСЕГДА добавляй просьбу о недостающих контактах

3. КОНТЕКСТ:
   - Помни весь предыдущий разговор
   - Используй имя клиента, если он его назвал
   - Ссылайся на предыдущие сообщения

4. ФОРМАТ ОТВЕТА - КРИТИЧЕСКИ ВАЖНО (ОБЯЗАТЕЛЬНО):
   - Ты ОБЯЗАН отвечать ТОЛЬКО в формате JSON, БЕЗ ЛЮБОГО дополнительного текста до или после JSON
   - НИКОГДА не пиши обычный текст, ВСЕГДА только JSON
   - Формат ответа:
   {
     "response": "твой ответ клиенту",
     "name": "имя клиента ИЗ ТЕКУЩЕГО СООБЩЕНИЯ или 0",
     "phone": "номер телефона ИЗ ТЕКУЩЕГО СООБЩЕНИЯ или 0"
   }
   
   ПРАВИЛА ДЛЯ ПОЛЕЙ:
   - "name": 
     * Если клиент НАПРЯМУЮ назвал свое имя в текущем сообщении (например: "меня зовут Иван", "я Влад", "Влад 89371234378") - укажи ТОЧНО это имя
     * Если имя НЕ упоминается в текущем сообщении - укажи "0"
     * НЕ выдумывай имя, НЕ используй имена из предыдущих сообщений
     * КРИТИЧЕСКИ ВАЖНО: НЕ используй части слов из вопросов как имена! Например:
       - "Какая стоимость для школьников" - НЕ имя, укажи "0"
       - "Меня интересует цена" - НЕ имя, укажи "0"
       - "Для ребенка" - НЕ имя, укажи "0"
       - Имя должно быть ОТДЕЛЬНЫМ словом, которое клиент явно назвал как свое имя
   
   - "phone":
     * Если клиент НАПРЯМУЮ указал номер телефона в текущем сообщении (например: "89371234378", "+7 937 123 43 78") - укажи номер БЕЗ пробелов и дефисов
     * Если номера НЕТ в текущем сообщении - укажи "0"
     * НЕ выдумывай номер, НЕ используй номера из предыдущих сообщений
   
   - "response": твой обычный дружелюбный ответ клиенту
   
   ПРИМЕРЫ (ВСЕГДА ТОЛЬКО JSON, БЕЗ ТЕКСТА ДО ИЛИ ПОСЛЕ):
   Сообщение: "Влад 89371234378"
   Ответ: {"response": "Спасибо, Влад! Записал ваш номер.", "name": "Влад", "phone": "89371234378"}
   
   Сообщение: "меня интересует цена"
   Ответ: {"response": "Конечно! Расскажу о ценах. Пожалуйста, назовите ваше имя и номер телефона для связи.", "name": "0", "phone": "0"}
   
   Сообщение: "меня зовут Иван"
   Ответ: {"response": "Приятно познакомиться, Иван! Пожалуйста, укажите ваш номер телефона.", "name": "Иван", "phone": "0"}
   
   Сообщение: "Привет"
   Ответ: {"response": "Привет! Как я могу помочь? Пожалуйста, назовите ваше имя и номер телефона для связи.", "name": "0", "phone": "0"}
   
   Сообщение: "Понял"
   Ответ: {"response": "Отлично! Если есть вопросы, дайте знать. Пожалуйста, назовите ваше имя и номер телефона.", "name": "0", "phone": "0"}"""
        
        # Добавляем статус контактов
        if contact_status:
            system_prompt += contact_status
        
        # Добавляем информацию из базы знаний
        if knowledge_context:
            system_prompt += knowledge_context
        
        messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]
        
        # Добавляем историю разговора
        messages.extend(conversation_history)
        
        # Добавляем текущее сообщение
        messages.append({
            "role": "user",
            "content": message
        })
        
        # Настройка прокси для httpx
        # httpx поддерживает прокси в формате: http://user:pass@host:port
        # Для словаря proxies используем тот же URL для http и https
        proxies = None
        if self.proxy_url:
            proxies = {
                "http://": self.proxy_url,
                "https://": self.proxy_url
            }
        
        # Пробуем с прокси, если не работает - пробуем без прокси
        for attempt in range(2):
            try:
                async with httpx.AsyncClient(
                    proxies=proxies if attempt == 0 else None,
                    timeout=httpx.Timeout(60.0, connect=10.0)
                ) as client:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "gpt-4o-mini",
                            "messages": messages,
                            "temperature": 0.7,
                            "max_tokens": 500,
                            "response_format": {"type": "json_object"}
                        }
                    )
                    response.raise_for_status()
                    data = response.json()
                    ai_response = data["choices"][0]["message"]["content"]
                    
                    # Парсим JSON ответ от ИИ
                    extracted_name = ""
                    extracted_phone = ""
                    try:
                        import json
                        # Пытаемся найти JSON в ответе (может быть обернут в markdown код)
                        json_text = ai_response.strip()
                        # Убираем markdown код блоки если есть
                        if json_text.startswith("```"):
                            parts = json_text.split("```")
                            for part in parts:
                                if part.strip().startswith("{"):
                                    json_text = part.strip()
                                    if json_text.startswith("json"):
                                        json_text = json_text[4:].strip()
                                    break
                        json_text = json_text.strip()
                        
                        parsed = json.loads(json_text)
                        response_text = parsed.get("response", ai_response)
                        
                        # Извлекаем имя
                        name_value = parsed.get("name", "")
                        if name_value and str(name_value).strip() not in ["0", "", None]:
                            extracted_name = str(name_value).strip()
                        
                        # Извлекаем телефон
                        phone_value = parsed.get("phone", "")
                        if phone_value and str(phone_value).strip() not in ["0", "", None]:
                            # Убираем все нецифровые символы кроме + в начале
                            phone_clean = str(phone_value).strip()
                            if phone_clean.startswith("+"):
                                phone_clean = "+" + ''.join(filter(str.isdigit, phone_clean[1:]))
                            else:
                                phone_clean = ''.join(filter(str.isdigit, phone_clean))
                            if len(phone_clean) >= 10:  # Минимум 10 цифр
                                extracted_phone = phone_clean
                    except (json.JSONDecodeError, KeyError, AttributeError) as e:
                        # Если не удалось распарсить JSON, пытаемся извлечь JSON из текста
                        print(f"Ошибка парсинга JSON от ИИ: {e}, ответ: {ai_response[:200]}")
                        # Пытаемся найти JSON в ответе (может быть обернут в текст)
                        import re
                        json_match = re.search(r'\{[^{}]*"response"[^{}]*"name"[^{}]*"phone"[^{}]*\}', ai_response, re.DOTALL)
                        if json_match:
                            try:
                                parsed = json.loads(json_match.group(0))
                                response_text = parsed.get("response", ai_response)
                                name_value = parsed.get("name", "")
                                phone_value = parsed.get("phone", "")
                                if name_value and str(name_value).strip() not in ["0", "", None]:
                                    extracted_name = str(name_value).strip()
                                if phone_value and str(phone_value).strip() not in ["0", "", None]:
                                    phone_clean = ''.join(filter(str.isdigit, str(phone_value)))
                                    if len(phone_clean) >= 10:
                                        extracted_phone = phone_clean[-10:] if len(phone_clean) > 10 else phone_clean
                            except:
                                response_text = ai_response
                                extracted_name = ""
                                extracted_phone = ""
                        else:
                            # Если JSON не найден, используем ответ как есть
                            response_text = ai_response
                            extracted_name = ""
                            extracted_phone = ""
                    
                    return (response_text, extracted_name, extracted_phone)
            except (httpx.ProxyError, httpx.RemoteProtocolError, httpx.ConnectError) as e:
                if attempt == 0 and self.proxy_url:
                    print(f"Ошибка прокси при попытке {attempt + 1}: {e}. Пробую без прокси...")
                    continue
                else:
                    raise
            except Exception as e:
                import traceback
                print(f"OpenAI API Error: {e}")
                print(f"Traceback: {traceback.format_exc()}")
                if attempt == 0 and self.proxy_url:
                    print("Пробую без прокси...")
                    continue
                return ("Извините, произошла ошибка при обработке запроса. Попробуйте позже.", "", "")
        
        return ("Извините, произошла ошибка при обработке запроса. Попробуйте позже.", "", "")
    
    async def generate_conversation_summary(self, conversation_history: list) -> str:
        """
        Генерирует краткое резюме диалога для отправки в CRM
        
        Args:
            conversation_history: История разговора в формате [{"role": "user/assistant", "content": "..."}]
        
        Returns:
            Краткое резюме проблемы/запроса пользователя или пустая строка, если информации недостаточно
        """
        if not conversation_history or len(conversation_history) < 2:
            # Если диалог только начался, резюме нет
            return ""
        
        # Формируем промпт для генерации резюме
        system_prompt = """Ты анализируешь диалог между клиентом и ассистентом. 
        
Твоя задача - составить КРАТКОЕ резюме (2-3 предложения) о том, какая у клиента проблема или запрос.

Правила:
- Резюме должно быть конкретным и информативным
- Укажи основную проблему/запрос клиента
- Если клиент только поздоровался или дал контакты, но не рассказал о проблеме - верни пустую строку
- Пиши на русском языке
- Максимум 3 предложения"""

        # Формируем сообщения для анализа
        messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]
        
        # Добавляем историю диалога
        messages.extend(conversation_history)
        
        # Добавляем запрос на резюме
        messages.append({
            "role": "user",
            "content": "Составь краткое резюме диалога. Если клиент только поздоровался или дал контакты без описания проблемы, верни пустую строку."
        })
        
        # Настройка прокси
        proxies = None
        if self.proxy_url:
            proxies = {
                "http://": self.proxy_url,
                "https://": self.proxy_url
            }
        
        # Пробуем с прокси, если не работает - пробуем без прокси
        for attempt in range(2):
            try:
                async with httpx.AsyncClient(
                    proxies=proxies if attempt == 0 else None,
                    timeout=httpx.Timeout(30.0, connect=10.0)
                ) as client:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "gpt-4o-mini",
                            "messages": messages,
                            "temperature": 0.3,  # Низкая температура для более точного резюме
                            "max_tokens": 150
                        }
                    )
                    response.raise_for_status()
                    data = response.json()
                    summary = data["choices"][0]["message"]["content"].strip()
                    
                    # Если резюме пустое или слишком короткое, возвращаем пустую строку
                    if not summary or len(summary) < 10:
                        return ""
                    
                    return summary
            except (httpx.ProxyError, httpx.RemoteProtocolError, httpx.ConnectError) as e:
                if attempt == 0 and self.proxy_url:
                    continue
                else:
                    return ""
            except Exception as e:
                if attempt == 0 and self.proxy_url:
                    continue
                return ""
        
        return ""

ai_service = AIService()
