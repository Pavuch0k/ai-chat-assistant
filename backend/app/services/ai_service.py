import os
import httpx
from app.core.config import settings
from app.services.knowledge_service import knowledge_service
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
        """Получить ответ от OpenAI с использованием базы знаний"""
        if conversation_history is None:
            conversation_history = []
        
        # Ищем релевантную информацию в базе знаний
        knowledge_context = ""
        search_results = knowledge_service.search(message, limit=3)
        if search_results:
            knowledge_context = "\n\nРелевантная информация из базы знаний:\n"
            for i, result in enumerate(search_results, 1):
                knowledge_context += f"{i}. {result['text']}\n"
        
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
        
        # Формируем прокси для httpx (только если прокси доступен)
        proxies = None
        if self.proxy_url:
            # Проверяем доступность прокси (опционально, можно пропустить)
            try:
                import socket
                proxy_host = self.proxy_url.replace('http://', '').replace('https://', '').split(':')[0]
                proxy_port = int(self.proxy_url.split(':')[-1]) if ':' in self.proxy_url else 8000
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((proxy_host, proxy_port))
                sock.close()
                if result != 0:
                    print(f"Прокси {proxy_host}:{proxy_port} недоступен, используется прямое подключение")
                    proxies = None
                else:
                    if self.proxy_auth:
                        username, password = self.proxy_auth
                        proxy_host_full = self.proxy_url.replace('http://', '').replace('https://', '')
                        proxy_url_with_auth = f"http://{username}:{password}@{proxy_host_full}"
                        print(f"Используется прокси с аутентификацией: http://{username}:***@{proxy_host_full}")
                    else:
                        proxy_url_with_auth = self.proxy_url
                        print(f"Используется прокси без аутентификации: {proxy_url_with_auth}")
                    proxies = {
                        "http://": proxy_url_with_auth,
                        "https://": proxy_url_with_auth
                    }
            except Exception as e:
                print(f"Ошибка проверки прокси: {e}, используется прямое подключение")
                proxies = None
        else:
            print("Прокси не настроен, используется прямое подключение")
        
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
