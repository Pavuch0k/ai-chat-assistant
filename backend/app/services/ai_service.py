import os
import httpx
from app.core.config import settings
from app.services.knowledge_service import knowledge_service
from typing import Optional

class AIService:
    def __init__(self):
        self.api_key = settings.openai_api_key
        self.base_url = "https://api.openai.com/v1"
        # Прокси отключен - используется прямое подключение через VPN
        self.proxy_url = None
        self.proxy_auth = None
    
    async def get_response(self, message: str, conversation_history: list = None) -> str:
        """Получить ответ от OpenAI с использованием базы знаний"""
        if conversation_history is None:
            conversation_history = []
        
        # Ищем релевантную информацию в базе знаний
        knowledge_context = ""
        search_results = knowledge_service.search(message, limit=5)  # Увеличиваем лимит до 5
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

Правила работы:
1. Представление: "Здравствуйте! Я ваш ассистент. Чем могу помочь?" (НЕ используй [имя], просто говори что ты ассистент)

2. В КАЖДОМ ответе, помимо помощи, старайся собрать контакты:
   - Если клиент не назвал имя: вежливо спроси "Как к вам обращаться?" или "Как ваше имя?"
   - Если имя есть, но нет телефона: спроси "Для связи с вами, не могли бы вы оставить номер телефона?"
   - Если клиент назвал имя или телефон - подтверди: "Спасибо, [имя]! Я записал" или "Понял, ваш телефон [номер]"

3. Помни весь контекст:
   - Используй имя клиента, если он его назвал
   - Ссылайся на предыдущие сообщения
   - Помни, о чем говорили

4. Будь естественным - не навязывайся, но настойчиво собирай контакты в каждом ответе"""
        
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
        
        # Прокси отключен - используется прямое подключение
        proxies = None
        
        async with httpx.AsyncClient(proxies=proxies, timeout=30.0) as client:
            try:
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
                        "max_tokens": 500
                    }
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except Exception as e:
                import traceback
                print(f"OpenAI API Error: {e}")
                print(f"Traceback: {traceback.format_exc()}")
                return "Извините, произошла ошибка при обработке запроса. Попробуйте позже."

ai_service = AIService()
