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
    
    async def get_response(self, message: str, conversation_history: list = None, contact_status: str = "") -> str:
        """Получить ответ от OpenAI с использованием базы знаний"""
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

2. СБОР КОНТАКТОВ:
   - Если контакты УЖЕ собраны (имя и телефон есть) - НЕ проси их снова, просто помогай по вопросам
   - Если есть только имя - вежливо попроси номер телефона один раз
   - Если есть только телефон - вежливо попроси имя один раз
   - Если ничего нет - собирай постепенно, не навязывайся

3. КОНТЕКСТ:
   - Помни весь предыдущий разговор
   - Используй имя клиента, если он его назвал
   - Ссылайся на предыдущие сообщения"""
        
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
        proxies = {
            "http://": self.proxy_url,
            "https://": self.proxy_url
        } if self.proxy_url else None
        
        async with httpx.AsyncClient(proxies=proxies, timeout=60.0) as client:
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
