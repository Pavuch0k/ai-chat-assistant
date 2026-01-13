import os
import httpx
from app.core.config import settings
from typing import Optional

class AIService:
    def __init__(self):
        self.api_key = settings.openai_api_key
        self.base_url = "https://api.openai.com/v1"
        self.proxy_url = settings.openai_proxy_url
        self.proxy_auth = None
        
        if settings.openai_proxy_url and settings.openai_proxy_username:
            self.proxy_auth = (
                settings.openai_proxy_username,
                settings.openai_proxy_password or ""
            )
    
    async def get_response(self, message: str, conversation_history: list = None) -> str:
        """Получить ответ от OpenAI"""
        if conversation_history is None:
            conversation_history = []
        
        messages = [
            {
                "role": "system",
                "content": """Ты дружелюбный помощник службы поддержки. Твоя задача:
1. Помогать клиентам решать их вопросы профессионально и вежливо
2. АКТИВНО собирать контактные данные в процессе разговора:
   - В начале разговора вежливо представься и спроси имя: "Здравствуйте! Меня зовут [имя]. Как к вам обращаться?"
   - Если клиент назвал имя, запомни его и используй в дальнейшем разговоре
   - После 2-3 сообщений, если нет контактов, спроси: "Для связи с вами, не могли бы вы оставить email или телефон?"
   - Если клиент упомянул email или телефон - обязательно подтверди: "Спасибо, я записал ваш [email/телефон]"
3. ВСЕГДА помни весь контекст разговора:
   - Ссылайся на предыдущие сообщения клиента
   - Помни, о чем говорили ранее
   - Используй имя клиента, если он его назвал
4. Отвечай кратко, но информативно и дружелюбно"""
            }
        ]
        
        # Добавляем историю разговора
        messages.extend(conversation_history)
        
        # Добавляем текущее сообщение
        messages.append({
            "role": "user",
            "content": message
        })
        
        # Формируем URL прокси с аутентификацией если нужно
        proxy_url = None
        if self.proxy_url:
            if self.proxy_auth:
                username, password = self.proxy_auth
                proxy_url = f"http://{username}:{password}@{self.proxy_url.replace('http://', '')}"
            else:
                proxy_url = self.proxy_url
        
        async with httpx.AsyncClient(proxies=proxy_url, timeout=30.0) as client:
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
                print(f"OpenAI API Error: {e}")
                return "Извините, произошла ошибка при обработке запроса. Попробуйте позже."

ai_service = AIService()
