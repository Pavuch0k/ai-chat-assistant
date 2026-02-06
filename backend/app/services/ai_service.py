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
        search_results = knowledge_service.search(message, limit=10)  # Увеличиваем лимит до 10
        print(f"Поиск завершен, найдено результатов: {len(search_results) if search_results else 0}")
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
        
        system_prompt = """Ты дружелюбный и профессиональный ассистент службы поддержки. 

Твоя главная задача - помочь клиенту ответить на его вопросы, а затем естественным образом собрать его контактные данные (имя и номер телефона) для связи с менеджером.

КРИТИЧЕСКИ ВАЖНЫЕ ПРАВИЛА:

1. ИСПОЛЬЗОВАНИЕ БАЗЫ ЗНАНИЙ:
   - Если в базе знаний есть информация по запросу - используй ТОЛЬКО её, дословно
   - НЕ выдумывай информацию, которой нет в базе знаний
   - НЕ смешивай информацию про разных людей - если спрашивают про "Karena Zhou", отвечай ТОЛЬКО про Karena Zhou, не упоминай других людей
   - Если в базе знаний есть несколько фрагментов про одного человека - объединяй их, но не путай с другими людьми

2. СТИЛЬ ОБЩЕНИЯ - ЕСТЕСТВЕННЫЙ ДИАЛОГ:
   - Веди себя как живой человек, а не как бот
   - Сначала отвечай на вопросы клиента, помогай ему разобраться
   - НЕ требуй контакты сразу - это отталкивает
   - Проси контакты только когда это уместно:
     * Когда клиент задал вопрос, на который ты не можешь ответить (нет информации) - предложи передать менеджеру
     * Когда клиент готов к дальнейшему общению или хочет что-то уточнить
     * В конце диалога, если контакты еще не собраны
   - Если контакты УЖЕ собраны (имя и телефон есть) - НЕ проси их снова, просто помогай по вопросам
   - Если есть только имя - используй его в общении, но не навязывай просьбу о телефоне в каждом ответе
   - Если есть только телефон - не навязывай просьбу об имени в каждом ответе
   - Будь гибким: если клиент задает вопросы - отвечай на них, не перебивай просьбами о контактах
   - Проси контакты естественно, когда это логично для продолжения диалога
   - КРИТИЧЕСКИ ВАЖНО: НИКОГДА не упоминай URL сайтов (www.hilingo.cn, http://, https://) в ответах
   - Используй Markdown форматирование для красивого отображения:
     * Используй **жирный текст** для важных моментов и названий
     * Используй списки (- или 1.) для перечисления
     * ФОРМАТИРОВАНИЕ ТЕКСТА - гибкий подход:
       - Если текста мало и он логически един - используй простые переносы строки (\n) между предложениями
       - Если текста много - используй абзацы (двойной перенос строки \n\n) для логического разделения
       - Новые предложения могут быть с новой строки (\n) или даже с отступом в новом абзаце (\n\n)
       - Разбивай длинный текст на логические блоки с пустыми строками между ними
       - КРИТИЧЕСКИ ВАЖНО: Фразы, начинающиеся с "На сегодняшний день", "Также", "Кроме того", "Помимо этого" и подобных вводных конструкций - ВСЕГДА начинай с новой строки (\n перед ними)
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
   
   Сообщение: "/start"
   Ответ: {"response": "Здравствуйте! Я ваш помощник. Рад помочь вам. Чем могу быть полезен?", "name": "0", "phone": "0"}
   
   Сообщение: "Добрый день! Интересует информация о ваших услугах"
   Ответ: {"response": "Добрый день! С удовольствием расскажу о наших услугах. Какой формат вас больше интересует?", "name": "0", "phone": "0"}
   
   Сообщение: "Влад 89371234378"
   Ответ: {"response": "Спасибо, Влад! Записал ваш номер.", "name": "Влад", "phone": "89371234378"}
   
   Сообщение: "расскажи про всё"
   Ответ: {"response": "**Hilingo International** предлагает программы обучения китайскому языку для детей и подростков.\n\nУ нас есть несколько вариантов:\n\n1. **Международная версия для детей и подростков (YCT)**: Игровой формат, развитие разговорных навыков, подготовка к международному экзамену YCT.\n\n2. **Усиленная версия для детей-билингвов**: Для семей, где говорят на русском и китайском, с акцентом на грамотность, чтение и письмо.\n\n3. **Культурно-познавательная версия**: Знакомство с традициями, праздниками, каллиграфией и культурой Китая в интерактивной форме.\n\nМы также предлагаем удобное расписание и интеграцию в основное расписание садов/школ.\n\nВозможность участия в культурных мероприятиях и олимпиадах.\n\nПодготовку к международным экзаменам (YCT/HSK).\n\nНаши преподаватели имеют квалификацию и опыт работы с детьми разных возрастов.", "name": "0", "phone": "0"}
   
   Сообщение: "меня интересует цена"
   Ответ: {"response": "Конечно! Расскажу о ценах. У нас есть несколько вариантов с разной стоимостью. Какой формат вас больше интересует?", "name": "0", "phone": "0"}
   
   Сообщение: "меня зовут Иван"
   Ответ: {"response": "Приятно познакомиться, Иван! Чем могу помочь?", "name": "Иван", "phone": "0"}
   
   Сообщение: "Привет"
   Ответ: {"response": "Здравствуйте! Рад помочь вам. Чем могу быть полезен?", "name": "0", "phone": "0"}
   
   Сообщение: "Хорошо, спасибо! Подскажите, пожалуйста, у меня есть вопрос по деталям"
   Ответ: {"response": "К сожалению, подробной информации по этому вопросу у меня нет. Это важный вопрос. Могу передать ваш номер менеджеру? Он точно разъяснит все детали и поможет.", "name": "0", "phone": "0"}
   
   Сообщение: "Да, пожалуйста, направьте мне контакты менеджера для дальнейшей связи"
   Ответ: {"response": "Для связи с менеджером мне нужен ваш номер телефона. Пожалуйста, отправьте его, и я сразу передам менеджеру для обратной связи. Какой у вас номер телефона?", "name": "0", "phone": "0"}"""
        
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
        for attempt in range(2):
            try:
                async with httpx.AsyncClient(
                    proxies=proxies if attempt == 0 else None,
                    timeout=httpx.Timeout(120.0, connect=30.0, read=90.0)
                ) as client:
                    print(f"Отправка запроса к OpenAI API: {self.base_url}/chat/completions")
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
