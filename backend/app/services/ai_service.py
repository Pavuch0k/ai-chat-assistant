import os
import httpx
import base64
import subprocess
import atexit
import logging
from app.core.config import settings
from app.services.knowledge_service import knowledge_service
from typing import Optional

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.api_key = settings.openai_api_key
        self.base_url = "https://api.openai.com/v1"
        self.shadowsocks_process = None
        self.local_socks_port = None
        
        # Отладочный вывод
        logger.info(f"DEBUG: settings.openai_proxy_url = {settings.openai_proxy_url}")
        logger.info(f"DEBUG: settings.openai_proxy_username = {settings.openai_proxy_username}")
        logger.info(f"DEBUG: settings.openai_proxy_password = {'SET' if settings.openai_proxy_password else 'NOT SET'}")
        print(f"DEBUG: settings.openai_proxy_url = {settings.openai_proxy_url}", flush=True)
        print(f"DEBUG: settings.openai_proxy_username = {settings.openai_proxy_username}", flush=True)
        print(f"DEBUG: settings.openai_proxy_password = {'SET' if settings.openai_proxy_password else 'NOT SET'}", flush=True)
        
        # Настройка прокси
        if settings.openai_proxy_url:
            logger.info(f"Найден прокси URL: {settings.openai_proxy_url[:50]}...")
            print(f"Найден прокси URL: {settings.openai_proxy_url[:50]}...", flush=True)
            # Проверяем, является ли это Shadowsocks ссылкой
            if settings.openai_proxy_url.startswith("ss://"):
                logger.info("Обнаружен Shadowsocks прокси, настраиваю локальный клиент...")
                print("Обнаружен Shadowsocks прокси, настраиваю локальный клиент...", flush=True)
                self.proxy_url = None  # Будем использовать SOCKS5 через локальный Shadowsocks клиент
                self._setup_shadowsocks(settings.openai_proxy_url)
            elif settings.openai_proxy_username and settings.openai_proxy_password:
                # Обычный HTTP/HTTPS прокси
                proxy_host = settings.openai_proxy_url.replace("http://", "").replace("https://", "")
                proxy_protocol = "https" if settings.openai_proxy_url.startswith("https://") else "http"
                self.proxy_url = f"{proxy_protocol}://{settings.openai_proxy_username}:{settings.openai_proxy_password}@{proxy_host}"
            else:
                self.proxy_url = None
        else:
            self.proxy_url = None
        
        # Регистрируем очистку при выходе
        atexit.register(self._cleanup_shadowsocks)
        
        proxy_info = f"SOCKS5:{self.local_socks_port}" if self.local_socks_port else (self.proxy_url if self.proxy_url else "None")
        logger.info(f"AI Service initialized. API Key: {'Set' if self.api_key else 'NOT SET'}, Proxy: {proxy_info}")
        print(f"AI Service initialized. API Key: {'Set' if self.api_key else 'NOT SET'}, Proxy: {proxy_info}", flush=True)
    
    def _parse_shadowsocks_url(self, ss_url: str):
        """Парсит Shadowsocks URL"""
        ss_url = ss_url.replace("ss://", "").split("?")[0]  # Убираем параметры после ?
        parts = ss_url.split("@")
        if len(parts) != 2:
            raise ValueError("Неверный формат SS URL")
        
        encoded = parts[0]
        server_part = parts[1]
        # Убираем возможные слеши в конце
        server_part = server_part.rstrip("/")
        server, port = server_part.split(":")
        
        decoded = base64.b64decode(encoded).decode()
        method, password = decoded.split(":", 1)
        
        return {
            "method": method,
            "password": password,
            "server": server,
            "port": int(port)
        }
    
    def _setup_shadowsocks(self, ss_url: str):
        """Настраивает локальный Shadowsocks клиент для создания SOCKS5 прокси"""
        try:
            logger.info(f"Начинаю настройку Shadowsocks для URL: {ss_url[:50]}...")
            print(f"Начинаю настройку Shadowsocks для URL: {ss_url[:50]}...", flush=True)
            ss_config = self._parse_shadowsocks_url(ss_url)
            logger.info(f"Парсинг успешен: server={ss_config['server']}, port={ss_config['port']}, method={ss_config['method']}")
            print(f"Парсинг успешен: server={ss_config['server']}, port={ss_config['port']}, method={ss_config['method']}", flush=True)
            
            # Пробуем использовать shadowsocks-libev через ss-local
            try:
                # Проверяем наличие ss-local
                logger.info("Проверяю наличие ss-local...")
                print("Проверяю наличие ss-local...", flush=True)
                result = subprocess.run(["which", "ss-local"], capture_output=True, text=True)
                logger.info(f"Результат проверки ss-local: returncode={result.returncode}, stdout={result.stdout.strip()}")
                print(f"Результат проверки ss-local: returncode={result.returncode}, stdout={result.stdout.strip()}", flush=True)
                if result.returncode == 0:
                    # Используем ss-local для создания локального SOCKS5 прокси
                    # Пробуем разные порты, начиная с 1080
                    import socket
                    for port in [1080, 1081, 1082, 1083, 1084]:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        result = sock.connect_ex(('127.0.0.1', port))
                        sock.close()
                        if result != 0:  # Порт свободен
                            self.local_socks_port = port
                            break
                    else:
                        # Все порты заняты, используем 1080 и попробуем убить старый процесс
                        self.local_socks_port = 1080
                        try:
                            subprocess.run(["pkill", "-f", "ss-local"], timeout=2, capture_output=True)
                            import time
                            time.sleep(1)
                        except:
                            pass
                    
                    # Создаем конфигурационный файл для ss-local
                    config_content = f"""{{
    "server": "{ss_config['server']}",
    "server_port": {ss_config['port']},
    "local_address": "127.0.0.1",
    "local_port": {self.local_socks_port},
    "password": "{ss_config['password']}",
    "method": "{ss_config['method']}",
    "timeout": 300
}}"""
                    
                    import tempfile
                    config_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
                    config_file.write(config_content)
                    config_file.close()
                    
                    # Запускаем ss-local
                    self.shadowsocks_process = subprocess.Popen(
                        ["ss-local", "-c", config_file.name],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        start_new_session=True
                    )
                    
                    # Ждем немного для запуска и проверяем, что процесс запустился
                    import time
                    time.sleep(3)
                    
                    # Проверяем, что процесс еще работает
                    if self.shadowsocks_process.poll() is None:
                        logger.info(f"✓ Shadowsocks клиент запущен на порту {self.local_socks_port}")
                        logger.info(f"  Конфигурация: {ss_config['server']}:{ss_config['port']}, метод: {ss_config['method']}")
                        print(f"✓ Shadowsocks клиент запущен на порту {self.local_socks_port}", flush=True)
                        print(f"  Конфигурация: {ss_config['server']}:{ss_config['port']}, метод: {ss_config['method']}", flush=True)
                        return
                    else:
                        # Процесс завершился, читаем ошибку
                        stderr_output = self.shadowsocks_process.stderr.read().decode() if self.shadowsocks_process.stderr else ""
                        logger.error(f"✗ Ошибка запуска Shadowsocks клиента: {stderr_output}")
                        print(f"✗ Ошибка запуска Shadowsocks клиента: {stderr_output}", flush=True)
                        self.shadowsocks_process = None
            except FileNotFoundError as e:
                logger.warning(f"ss-local не найден: {e}. Установите shadowsocks-libev")
                print(f"ss-local не найден: {e}. Установите shadowsocks-libev", flush=True)
            except Exception as e:
                logger.error(f"Ошибка настройки Shadowsocks: {e}", exc_info=True)
                print(f"Ошибка настройки Shadowsocks: {e}", flush=True)
                import traceback
                print(traceback.format_exc(), flush=True)
                
        except Exception as e:
            print(f"Ошибка парсинга Shadowsocks URL: {e}")
    
    def _cleanup_shadowsocks(self):
        """Останавливает локальный Shadowsocks клиент"""
        if self.shadowsocks_process:
            try:
                self.shadowsocks_process.terminate()
                self.shadowsocks_process.wait(timeout=5)
            except:
                try:
                    self.shadowsocks_process.kill()
                except:
                    pass
    
    async def get_response(self, message: str, conversation_history: list = None, contact_status: str = "") -> tuple[str, str, str]:
        """
        Получить ответ от OpenAI с использованием базы знаний
        
        Returns:
            tuple: (response_text, extracted_name, extracted_phone) где:
                - response_text - ответ ИИ
                - extracted_name - имя из ответа ИИ или пустая строка
                - extracted_phone - телефон из ответа ИИ или пустая строка
        """
        print(f"=== get_response вызван: message='{message[:50]}...', history_len={len(conversation_history) if conversation_history else 0}")
        if conversation_history is None:
            conversation_history = []
        
        # Ищем релевантную информацию в базе знаний
        print(f"Начинаю поиск в базе знаний для сообщения: {message[:100]}")
        knowledge_context = ""
        search_results = knowledge_service.search(message, limit=3)  # Ограничиваем до 3 для уменьшения контекста
        print(f"Поиск завершен, найдено результатов: {len(search_results) if search_results else 0}")
        if search_results:
            print(f"Найдено {len(search_results)} релевантных фрагментов из базы знаний")
            knowledge_context = "\n\nВАЖНО: Используй ТОЛЬКО информацию из базы знаний ниже для ответа. Если информация есть в базе знаний, обязательно используй её:\n"
            for i, result in enumerate(search_results, 1):
                score = result.get('score', 0)
                text = result['text'][:500]  # Ограничиваем длину для логов
                print(f"  Фрагмент {i} (score: {score:.3f}): {text[:100]}...")
                # Ограничиваем длину каждого фрагмента до 200 символов для уменьшения контекста
                fragment_text = result['text'][:200]
                knowledge_context += f"{i}. {fragment_text}\n"
            knowledge_context += "\nЕсли в базе знаний есть информация по запросу пользователя, ОБЯЗАТЕЛЬНО используй её в ответе!"
        else:
            print(f"Поиск в базе знаний не вернул результатов для запроса: {message[:100]}")
        
        system_prompt = """Ты дружелюбный и профессиональный ассистент службы поддержки. 

Твоя главная задача - помочь клиенту ответить на его вопросы, а затем естественным образом собрать его контактные данные (имя и номер телефона) для связи с менеджером.

КРИТИЧЕСКИ ВАЖНЫЕ ПРАВИЛА:

1. ИСПОЛЬЗОВАНИЕ БАЗЫ ЗНАНИЙ:
   - Если в базе знаний есть информация по запросу - используй ТОЛЬКО её
   - НЕ выдумывай информацию, которой нет в базе знаний
   

2. СТИЛЬ ОБЩЕНИЯ - ЕСТЕСТВЕННЫЙ ДИАЛОГ:
   - Веди себя как живой человек, а не как бот
   - Сначала отвечай на вопросы клиента, помогай ему разобраться
   - КРИТИЧЕСКИ ВАЖНО: КАЖДОЕ твое сообщение ОБЯЗАТЕЛЬНО должно заканчиваться вопросом - БЕЗ ИСКЛЮЧЕНИЙ!
   - Вопрос в конце сообщения должен быть либо:
     * Наводящим вопросом по теме разговора (уточняющим, развивающим диалог)
     * Просьбой о контактах (когда это логично для продолжения)
   - СТРАТЕГИЯ СБОРА КОНТАКТОВ:
     * НЕ требуй контакты сразу - это отталкивает
     * Начинай с наводящих вопросов по теме, которые естественно ведут к сбору контактов
     * КРИТИЧЕСКИ ВАЖНО: После того, как ты ответил на вопрос клиента (например, рассказал о тарифах, услугах и т.д.), ОБЯЗАТЕЛЬНО либо:
       - Спроси контакты для связи с менеджером (если контакты еще не собраны)
       - Задай наводящий вопрос по теме, который естественно ведет к сбору контактов
     * Когда клиент задал вопрос, на который ты не можешь ответить (нет информации) - предложи передать менеджеру и попроси контакты
     * Когда клиент готов к дальнейшему общению или хочет что-то уточнить - естественно подведи к просьбе о контактах
     * КРИТИЧЕСКИ ВАЖНО: ВСЕГДА сначала запрашивай ИМЯ, только потом номер телефона
     * Если контакты УЖЕ собраны (имя и телефон есть) - НЕ проси их снова, просто помогай по вопросам, заканчивай наводящими вопросами по теме
     * Если есть только имя - используй его в общении, постепенно подводи к просьбе о телефоне через наводящие вопросы
     * Если есть только телефон - постепенно подводи к просьбе об имени через наводящие вопросы
     * Если нет ни имени, ни телефона - после ответа на вопрос клиента естественно подведи к просьбе об имени
   - Примеры правильных вопросов в конце сообщения:
     * "Какой формат вас больше интересует?"
     * "Что именно вас интересует в этом направлении?"
     * "Могу передать ваш номер менеджеру? Он точно разъяснит все детали."
     * "Для связи с менеджером мне нужен ваш номер телефона. Какой у вас номер?"
   - КРИТИЧЕСКИ ВАЖНО: НИКОГДА не упоминай URL сайтов (www.hilingo.cn, http://, https://) в ответах
   - Используй Markdown форматирование для красивого отображения:
     * Используй **жирный текст** для важных моментов и названий
     * Используй списки (- или 1.) для перечисления
     * ФОРМАТИРОВАНИЕ ТЕКСТА - КРИТИЧЕСКИ ВАЖНО:
       - КАЖДОЕ НОВОЕ ПРЕДЛОЖЕНИЕ должно быть с новой строки (одиночный перенос строки \n перед каждым предложением)
       - НИКОГДА не используй двойные пустые строки (\n\n\n - три переноса подряд) - это создает слишком большие отступы
       - Можно использовать одиночные пустые строки (\n\n - два переноса подряд) ТОЛЬКО для логического разделения больших блоков текста, но не между каждыми предложениями
       - Обычно между предложениями используй ТОЛЬКО один перенос строки (\n)
       - Фразы, начинающиеся с "На сегодняшний день", "Также", "Кроме того", "Помимо этого" и подобных вводных конструкций - ВСЕГДА начинай с новой строки (\n перед ними)
     * НЕ используй заголовки (##) - они создают разный размер шрифта
     * Делай ответы визуально приятными и логически структурированными
     * Все предложения должны быть одного размера и цвета

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
   
   ПРИМЕРЫ ЕСТЕСТВЕННОГО ОБЩЕНИЯ (ВСЕГДА ТОЛЬКО JSON, БЕЗ ТЕКСТА ДО ИЛИ ПОСЛЕ):
   
   Сообщение: "Привет"
   Ответ: {"response": "Здравствуйте! Рад помочь вам. Чем могу быть полезен?", "name": "0", "phone": "0"}
   
   Сообщение: "Влад 89371234378"
   Ответ: {"response": "Спасибо, Влад! Записал ваш номер. Чем еще могу помочь?", "name": "Влад", "phone": "89371234378"}
   
   Сообщение: "Да, пожалуйста, направьте мне контакты менеджера для дальнейшей связи"
   Ответ: {"response": "Конечно! Для связи с менеджером мне нужны ваши контактные данные. Как вас зовут?", "name": "0", "phone": "0"}
   
   Сообщение: "Иван"
   Ответ: {"response": "Приятно познакомиться, Иван! Теперь мне нужен ваш номер телефона, чтобы менеджер мог с вами связаться. Какой у вас номер?", "name": "Иван", "phone": "0"} """
        
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
        
        # Ограничиваем историю разговора последними 30 сообщениями, чтобы не превышать лимит токенов
        # Берем последние 30 сообщений (15 пар вопрос-ответ)
        limited_history = conversation_history[-30:] if len(conversation_history) > 30 else conversation_history
        messages.extend(limited_history)
        
        # Добавляем текущее сообщение
        messages.append({
            "role": "user",
            "content": message
        })
        
        # Настройка прокси для httpx
        proxies = None
        if self.local_socks_port:
            # Используем локальный SOCKS5 прокси от Shadowsocks клиента
            try:
                import httpx_socks
                proxies = {
                    "http://": f"socks5://127.0.0.1:{self.local_socks_port}",
                    "https://": f"socks5://127.0.0.1:{self.local_socks_port}"
                }
            except ImportError:
                print("httpx-socks не установлен. Установите: pip install httpx-socks")
                # Пробуем без прокси
                proxies = None
        elif self.proxy_url:
            # Обычный HTTP/HTTPS прокси
            proxies = {
                "http://": self.proxy_url,
                "https://": self.proxy_url
            }
        
        # Пробуем с прокси, если не работает - пробуем без прокси
        for proxy_attempt in range(2):
            try:
                # Повторные попытки при ошибках парсинга или пустом ответе
                for parse_attempt in range(3):  # Максимум 3 попытки
                    async with httpx.AsyncClient(
                        proxies=proxies if proxy_attempt == 0 else None,
                        timeout=httpx.Timeout(120.0, connect=30.0, read=90.0)
                    ) as client:
                        print(f"Отправка запроса к OpenAI API (попытка {parse_attempt + 1}): {self.base_url}/chat/completions")
                        print(f"API Key присутствует: {bool(self.api_key)}")
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
                                "max_tokens": 2000,  # Увеличиваем лимит токенов для ответа
                                "response_format": {"type": "json_object"}
                            }
                        )
                        response.raise_for_status()
                        data = response.json()
                        ai_response = data["choices"][0]["message"]["content"]
                        
                        # Логируем ответ для отладки
                        if not ai_response or not ai_response.strip():
                            print(f"Получен пустой ответ от ИИ, попытка {parse_attempt + 1}/3")
                            print(f"Полный ответ API: {data}")
                            print(f"Choices: {data.get('choices', [])}")
                            if parse_attempt < 2:  # Если не последняя попытка
                                continue  # Повторяем запрос
                            else:
                                # Последняя попытка - возвращаем ошибку
                                return ("Извините, произошла ошибка при обработке запроса. Попробуйте переформулировать вопрос.", "", "")
                        else:
                            print(f"Получен ответ от ИИ (длина: {len(ai_response)}): {ai_response[:200]}")
                        
                        # Парсим JSON ответ от ИИ
                        extracted_name = ""
                        extracted_phone = ""
                        parse_success = False
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
                            
                            # Проверяем, что response_text не пустой
                            if not response_text or not response_text.strip():
                                print(f"Пустое поле response в JSON, попытка {parse_attempt + 1}/3")
                                if parse_attempt < 2:
                                    continue  # Повторяем запрос
                                else:
                                    response_text = "Извините, произошла ошибка при обработке запроса. Попробуйте переформулировать вопрос."
                            
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
                            
                            parse_success = True
                            
                        except (json.JSONDecodeError, KeyError, AttributeError) as e:
                            # Если не удалось распарсить JSON, пытаемся извлечь JSON из текста
                            print(f"Ошибка парсинга JSON от ИИ (попытка {parse_attempt + 1}/3): {e}, ответ: {ai_response[:200]}")
                            
                            # Если не последняя попытка - повторяем запрос
                            if parse_attempt < 2:
                                continue
                            
                            # Последняя попытка - пытаемся извлечь JSON из текста
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
                                    parse_success = True
                                except:
                                    pass
                            
                            if not parse_success:
                                # Если JSON не найден, используем ответ как есть
                                response_text = ai_response.strip() if ai_response else ""
                                # Если ответ пустой, возвращаем сообщение об ошибке
                                if not response_text:
                                    response_text = "Извините, произошла ошибка при обработке запроса. Попробуйте переформулировать вопрос."
                                extracted_name = ""
                                extracted_phone = ""
                        
                        # Если парсинг успешен, возвращаем результат
                        if parse_success:
                            # Финальная проверка: если response_text пустой, возвращаем сообщение об ошибке
                            if not response_text or not response_text.strip():
                                response_text = "Извините, произошла ошибка при обработке запроса. Попробуйте переформулировать вопрос."
                            return (response_text, extracted_name, extracted_phone)
                        
                        # Если дошли сюда и parse_success = False, значит это была последняя попытка
                        # и мы уже обработали ошибку выше - возвращаем ошибку
                        if not parse_success:
                            return ("Извините, произошла ошибка при обработке запроса. Попробуйте переформулировать вопрос.", "", "")
                        break
            except (httpx.ProxyError, httpx.RemoteProtocolError, httpx.ConnectError) as e:
                if proxy_attempt == 0 and self.proxy_url:
                    print(f"Ошибка прокси при попытке {proxy_attempt + 1}: {e}. Пробую без прокси...")
                    continue  # Пробуем без прокси
                else:
                    raise
            except Exception as e:
                import traceback
                print(f"OpenAI API Error: {e}")
                print(f"Traceback: {traceback.format_exc()}")
                if proxy_attempt == 0 and self.proxy_url:
                    print("Пробую без прокси...")
                    continue  # Пробуем без прокси
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
        if self.local_socks_port:
            # Используем локальный SOCKS5 прокси от Shadowsocks клиента
            try:
                import httpx_socks
                proxies = {
                    "http://": f"socks5://127.0.0.1:{self.local_socks_port}",
                    "https://": f"socks5://127.0.0.1:{self.local_socks_port}"
                }
            except ImportError:
                proxies = None
        elif self.proxy_url:
            proxies = {
                "http://": self.proxy_url,
                "https://": self.proxy_url
            }
        
        # Пробуем с прокси, если не работает - пробуем без прокси
        for attempt in range(2):
            try:
                async with httpx.AsyncClient(
                    proxies=proxies if attempt == 0 else None,
                    timeout=httpx.Timeout(120.0, connect=30.0, read=90.0)
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
