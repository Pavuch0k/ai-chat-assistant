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

def estimate_tokens(text: str) -> int:
    """
    Приблизительный подсчет токенов.
    ДЛЯ РУССКОГО ЯЗЫКА: ~1 токен = 2.5 символа (консервативная оценка)
    Для английского: ~1 токен = 4 символа
    Используем консервативную оценку для безопасности
    """
    if not text:
        return 0
    # Консервативная оценка для русского текста: 1 токен = 2.5 символа
    # Это даёт запас и предотвращает переполнение
    return int(len(text) / 2.5) + 10  # +10 для overhead (JSON, форматирование)

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
    
    def _trim_history_to_fit_tokens(self, system_prompt: str, conversation_history: list, user_message: str, knowledge_context: str, max_context_tokens: int = 50000, max_response_tokens: int = 2000) -> list:
        """
        Обрезает историю разговора, чтобы уместиться в лимит токенов.
        
        Args:
            system_prompt: Системный промпт
            conversation_history: История разговора
            user_message: Текущее сообщение пользователя
            knowledge_context: Контекст из базы знаний
            max_context_tokens: Максимальное количество токенов для контекста (по умолчанию 50k)
            max_response_tokens: Максимальное количество токенов для ответа (по умолчанию 2k)
        
        Returns:
            Обрезанная история разговора
        """
        # Подсчитываем токены для системного промпта и текущего сообщения
        system_tokens = estimate_tokens(system_prompt)
        user_message_tokens = estimate_tokens(user_message)
        knowledge_tokens = estimate_tokens(knowledge_context)

        # Логируем использование токенов
        logger.info(f"Токены: system={system_tokens}, message={user_message_tokens}, knowledge={knowledge_tokens}")
        
        # Токены, которые всегда будут в запросе
        fixed_tokens = system_tokens + user_message_tokens + knowledge_tokens
        
        # Overhead для форматирования JSON и других служебных токенов
        overhead_tokens = 500  # Overhead для безопасности
        
        # Оставляем запас для ответа (max_response_tokens + небольшой буфер)
        response_reserve = max_response_tokens + 1000  # Запас для ответа и буфер
        
        # Доступные токены для истории
        # Общий лимит модели GPT-4o-mini: 128k токенов
        # Оставляем место для ответа, overhead и запаса
        available_tokens = max_context_tokens - fixed_tokens - overhead_tokens - response_reserve
        
        # Если не хватает места даже без истории, возвращаем пустую историю
        if available_tokens < 100:  # Минимум 100 токенов для истории
            logger.warning(f"Контекст слишком большой: system={system_tokens}, message={user_message_tokens}, knowledge={knowledge_tokens}. Обрезаем историю полностью.")
            logger.info(f"Доступные токены для истории: {available_tokens}, фиксированные токены: {fixed_tokens}, лимит контекста: {max_context_tokens}, резерв ответа: {response_reserve}")
            return []
        
        # Подсчитываем токены для каждого сообщения в истории
        history_tokens = []
        total_history_tokens = 0
        
        for msg in conversation_history:
            content = msg.get("content", "")
            msg_tokens = estimate_tokens(content)
            history_tokens.append((msg, msg_tokens))
            total_history_tokens += msg_tokens
        
        # Ограничиваем историю максимум 6 последними сообщениями для оптимизации
        # Это предотвращает переполнение при очень длинных диалогах
        max_history_messages = 6
        if len(conversation_history) > max_history_messages:
            conversation_history = conversation_history[-max_history_messages:]
            # Пересчитываем токены для ограниченной истории
            history_tokens = []
            total_history_tokens = 0
            for msg in conversation_history:
                content = msg.get("content", "")
                msg_tokens = estimate_tokens(content)
                history_tokens.append((msg, msg_tokens))
                total_history_tokens += msg_tokens
        
        # Если история помещается, возвращаем её полностью
        if total_history_tokens <= available_tokens:
            return conversation_history
        
        # Обрезаем историю с конца (удаляем самые старые сообщения)
        trimmed_history = []
        current_tokens = 0
        
        # Идем с конца истории (новые сообщения важнее старых)
        # Используем 90% от available_tokens для эффективного использования места
        safe_available_tokens = int(available_tokens * 0.9)
        
        for msg, msg_tokens in reversed(history_tokens):
            if current_tokens + msg_tokens <= safe_available_tokens:
                trimmed_history.insert(0, msg)  # Вставляем в начало, чтобы сохранить порядок
                current_tokens += msg_tokens
            else:
                # Если не помещается, останавливаемся
                break
        
        logger.info(f"История обрезана: было {len(conversation_history)} сообщений ({total_history_tokens} токенов), стало {len(trimmed_history)} сообщений ({current_tokens} токенов)")
        logger.info(f"Токены: system={system_tokens}, message={user_message_tokens}, knowledge={knowledge_tokens}, fixed={fixed_tokens}, available={available_tokens}, used={current_tokens}")
        
        # Добавим дополнительное логирование для отладки
        total_request_tokens = system_tokens + current_tokens + user_message_tokens + knowledge_tokens + response_reserve
        logger.info(f"ИТОГО токенов в запросе (без ответа): {total_request_tokens}, лимит модели: {max_context_tokens}, использовано на историю: {current_tokens}")
        
        return trimmed_history
    
    async def get_response(self, message: str, conversation_history: list = None, contact_status: str = "", knowledge_context: str = "") -> tuple[str, str, str]:
        """
        Получить ответ от OpenAI с использованием базы знаний

        Args:
            message: Сообщение пользователя
            conversation_history: История разговора (без контекста из базы знаний)
            contact_status: Статус контактов пользователя
            knowledge_context: Контекст из базы знаний только для текущего запроса

        Returns:
            tuple: (response_text, extracted_name, extracted_phone) где:
                - response_text - ответ ИИ
                - extracted_name - имя из ответа ИИ или пустая строка
                - extracted_phone - телефон из ответа ИИ или пустая строка
        """
        print(f"=== get_response вызван: message='{message[:50]}...', history_len={len(conversation_history) if conversation_history else 0}")
        if conversation_history is None:
            conversation_history = []
        
        system_prompt = """Ты ассистент поддержки. Помогаешь клиентам и естественно собираешь контакты (имя и телефон).

🚨🚨🚨 ПРАВИЛО #1 - АБСОЛЮТНО ОБЯЗАТЕЛЬНОЕ 🚨🚨🚨
▶▶▶ КАЖДОЕ твоё сообщение ОБЯЗАТЕЛЬНО заканчивается ВОПРОСОМ "?"
▶▶▶ Последнее предложение ВСЕГДА должно быть ВОПРОСОМ со знаком "?"

КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО заканчивать сообщения фразами:
❌❌❌ "дайте знать"
❌❌❌ "если интересует, сообщите"
❌❌❌ "обращайтесь"
❌❌❌ "напишите"
❌❌❌ "буду рад помочь"
❌❌❌ любые утверждения БЕЗ "?"

ОБЯЗАТЕЛЬНО используй вопросы:
✅✅✅ "Что именно вас интересует?"
✅✅✅ "Какой формат обучения рассматриваете?"
✅✅✅ "Хотите узнать о наших курсах?"
✅✅✅ "Для какого возраста нужна программа?"

ПРОВЕРЬ: Твой ответ ОБЯЗАТЕЛЬНО должен заканчиваться знаком "?" - иначе это ОШИБКА!

ИСПОЛЬЗОВАНИЕ БАЗЫ ЗНАНИЙ:
- Используй информацию из БЗ ТОЛЬКО если она РЕЛЕВАНТНА вопросу
- НЕ используй БЗ для простых приветствий - отвечай естественно
- НЕ выдумывай информацию, которой нет в БЗ

СБОР КОНТАКТОВ - КОНСУЛЬТАТИВНАЯ СТРАТЕГИЯ:
1. СНАЧАЛА помоги клиенту - задавай 2-4 уточняющих вопроса:
   - "Для какого возраста/уровня?"
   - "Какие цели обучения?"
   - "Какой график удобен?"
   - "Интересует онлайн или офлайн?"
2. ТОЛЬКО ПОСЛЕ консультации и понимания потребностей → собирай контакты
3. ЕСТЕСТВЕННЫЙ переход: "Отлично! Чтобы подобрать программу, как вас зовут?"
4. Сначала ИМЯ, потом ТЕЛЕФОН
5. Если контакты УЖЕ собраны - НЕ проси снова
6. ЗАПРЕЩЕНО: "затрудняюсь ответить" → вместо этого задай уточняющий вопрос или "Менеджер расскажет. Как вас зовут?"

ФОРМАТИРОВАНИЕ:
- Каждое предложение с новой строки (\n)
- Один перенос между предложениями (НЕ \n\n)
- **Жирный текст** для важного
- Списки (- или 1.) для перечисления
- БЕЗ URL (www., http://, https://)

ФОРМАТ ОТВЕТА - JSON ТОЛЬКО:
{
  "response": "твой ответ клиенту",
  "name": "имя ИЗ ТЕКУЩЕГО сообщения или 0",
  "phone": "телефон ИЗ ТЕКУЩЕГО сообщения или 0"
}

ПРАВИЛА ПОЛЕЙ:
- "name": Если клиент назвал имя ("меня зовут Иван", "я Влад") → укажи имя, иначе "0"
- "phone": Если клиент указал номер → укажи БЕЗ пробелов/дефисов, иначе "0"
- НЕ используй данные из предыдущих сообщений, НЕ выдумывай

ПРИМЕРЫ:
"Привет" → {"response": "Здравствуйте!\nРад помочь.\nЧем могу быть полезен?", "name": "0", "phone": "0"}
"Влад 89371234378" → {"response": "Спасибо, Влад!\nЗаписал номер.\nЧем еще помочь?", "name": "Влад", "phone": "89371234378"}
"нет" → {"response": "Понятно!\nЧтобы менеджер связался с вами, как вас зовут?", "name": "0", "phone": "0"}

🚨 ПОВТОР: КАЖДЫЙ ответ ОБЯЗАТЕЛЬНО заканчивается вопросом со знаком "?"
Никаких "дайте знать", "сообщите", "обращайтесь" - ТОЛЬКО ВОПРОС! """
        
        # Добавляем статус контактов
        if contact_status:
            system_prompt += contact_status

        # Формируем текущее сообщение пользователя с контекстом из базы знаний
        user_message_content = message
        if knowledge_context:
            # Добавляем контекст из базы знаний к сообщению пользователя
            # Этот контекст используется только для текущего запроса и не сохраняется в историю
            user_message_content = message + knowledge_context

        # Динамически обрезаем историю, чтобы уместиться в лимит токенов
        # Лимит GPT-4o-mini: 128k токенов (контекст + ответ)
        # ОПТИМИЗАЦИЯ: Используем КОНСЕРВАТИВНЫЕ лимиты для предотвращения переполнения
        # ВАЖНО: передаем в _trim_history_to_fit_tokens только оригинальное сообщение без контекста из базы знаний
        trimmed_history = self._trim_history_to_fit_tokens(
            system_prompt=system_prompt,
            conversation_history=conversation_history if conversation_history else [],
            user_message=message,  # Передаем оригинальное сообщение без контекста из базы знаний
            knowledge_context=knowledge_context if knowledge_context else "",
            max_context_tokens=12000,  # 12k токенов для контекста (ОЧЕНЬ строгий лимит)
            max_response_tokens=1000  # 300 токенов для ответа (КОРОТКИЕ ответы)
        )

        messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]

        # Добавляем обрезанную историю (без контекста из базы знаний)
        messages.extend(trimmed_history)

        # Добавляем текущее сообщение с контекстом из базы знаний
        messages.append({
            "role": "user",
            "content": user_message_content  # Сообщение + контекст из базы знаний для текущего запроса
        })

        # ============================================================
        # ПРЕДВАРИТЕЛЬНЫЙ РАСЧЁТ ТОКЕНОВ ПЕРЕД ОТПРАВКОЙ ЗАПРОСА
        # ============================================================
        system_tokens_calc = estimate_tokens(system_prompt)
        history_tokens_calc = sum(estimate_tokens(msg.get("content", "")) for msg in trimmed_history)
        current_message_tokens_calc = estimate_tokens(user_message_content)

        # Общее количество токенов в запросе (контекст)
        total_input_tokens = system_tokens_calc + history_tokens_calc + current_message_tokens_calc

        # Ожидаемое количество токенов в ответе (макс)
        max_output_tokens = 300  # Наш лимит

        # Общее количество токенов (контекст + ответ)
        total_tokens_expected = total_input_tokens + max_output_tokens

        # Лимиты модели GPT-4o-mini
        model_context_limit = 128000  # 128k токенов
        our_context_limit = 12000     # Наш лимит контекста
        our_output_limit = 300        # Наш лимит ответа

        # Логирование детального расчёта
        logger.info("=" * 70)
        logger.info("📊 ПРЕДВАРИТЕЛЬНЫЙ РАСЧЁТ ТОКЕНОВ:")
        logger.info("-" * 70)
        logger.info(f"  Системный промпт:     {system_tokens_calc:>6} токенов")
        logger.info(f"  История ({len(trimmed_history)} сообщений): {history_tokens_calc:>6} токенов")
        logger.info(f"  Текущее сообщение:    {current_message_tokens_calc:>6} токенов")
        logger.info("-" * 70)
        logger.info(f"  ИТОГО КОНТЕКСТ:       {total_input_tokens:>6} токенов")
        logger.info(f"  Макс ответ:           {max_output_tokens:>6} токенов")
        logger.info(f"  ВСЕГО ОЖИДАЕТСЯ:      {total_tokens_expected:>6} токенов")
        logger.info("-" * 70)
        logger.info(f"  Лимит модели:         {model_context_limit:>6} токенов")
        logger.info(f"  Наш лимит контекста:  {our_context_limit:>6} токенов")
        logger.info(f"  Наш лимит ответа:     {our_output_limit:>6} токенов")
        logger.info("-" * 70)

        # Проверка соответствия лимитам
        context_usage_percent = (total_input_tokens / our_context_limit) * 100
        model_usage_percent = (total_tokens_expected / model_context_limit) * 100

        logger.info(f"  Использование контекста: {context_usage_percent:.1f}% от нашего лимита")
        logger.info(f"  Использование модели:    {model_usage_percent:.1f}% от лимита модели")

        # Предупреждения
        if total_input_tokens > our_context_limit:
            logger.error(f"❌ ПРЕВЫШЕН НАШ ЛИМИТ КОНТЕКСТА! {total_input_tokens} > {our_context_limit}")
            logger.error("   Требуется более агрессивная обрезка истории!")
        elif context_usage_percent > 80:
            logger.warning(f"⚠️  Близко к лимиту контекста ({context_usage_percent:.1f}%)")
        elif context_usage_percent > 60:
            logger.info(f"ℹ️  Умеренное использование контекста ({context_usage_percent:.1f}%)")
        else:
            logger.info(f"✅ Оптимальное использование контекста ({context_usage_percent:.1f}%)")

        if total_tokens_expected > model_context_limit:
            logger.error(f"❌ ПРЕВЫШЕН ЛИМИТ МОДЕЛИ! {total_tokens_expected} > {model_context_limit}")
        elif model_usage_percent > 50:
            logger.warning(f"⚠️  Использовано более 50% лимита модели ({model_usage_percent:.1f}%)")
        else:
            logger.info(f"✅ Безопасное использование модели ({model_usage_percent:.1f}%)")

        logger.info("=" * 70)

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
                                "max_tokens": 300,  # Лимит токенов для ответа (КОРОТКИЕ ответы чат-бота)
                                "response_format": {"type": "json_object"}
                            }
                        )
                        response.raise_for_status()
                        data = response.json()

                        # ============================================================
                        # РЕАЛЬНЫЕ ТОКЕНЫ ОТ OPENAI API
                        # ============================================================
                        usage = data.get("usage", {})
                        actual_prompt_tokens = usage.get("prompt_tokens", 0)
                        actual_completion_tokens = usage.get("completion_tokens", 0)
                        actual_total_tokens = usage.get("total_tokens", 0)

                        # Логирование реальных токенов
                        logger.info("=" * 70)
                        logger.info("📈 РЕАЛЬНЫЕ ТОКЕНЫ ОТ OPENAI API:")
                        logger.info("-" * 70)
                        logger.info(f"  Prompt (контекст):    {actual_prompt_tokens:>6} токенов")
                        logger.info(f"  Completion (ответ):   {actual_completion_tokens:>6} токенов")
                        logger.info(f"  ИТОГО:                {actual_total_tokens:>6} токенов")
                        logger.info("-" * 70)

                        # Сравнение с предварительным расчётом
                        prompt_diff = actual_prompt_tokens - total_input_tokens
                        prompt_diff_percent = (prompt_diff / total_input_tokens * 100) if total_input_tokens > 0 else 0

                        logger.info(f"  Расчёт vs Реальность (промпт): {total_input_tokens} → {actual_prompt_tokens}")
                        if abs(prompt_diff_percent) > 10:
                            logger.warning(f"  ⚠️  Разница: {prompt_diff:+d} токенов ({prompt_diff_percent:+.1f}%)")
                        else:
                            logger.info(f"  ✅ Точность: {prompt_diff:+d} токенов ({prompt_diff_percent:+.1f}%)")

                        # Проверка эффективности ответа
                        if actual_completion_tokens >= max_output_tokens * 0.9:
                            logger.warning(f"  ⚠️  Ответ близок к лимиту ({actual_completion_tokens}/{max_output_tokens})")
                        else:
                            logger.info(f"  ✅ Ответ в пределах лимита ({actual_completion_tokens}/{max_output_tokens})")

                        logger.info("=" * 70)

                        # Проверяем finish_reason
                        finish_reason = data["choices"][0].get("finish_reason", "")
                        ai_response = data["choices"][0]["message"]["content"]
                        
                        # Если ответ обрезан, сразу обрезаем историю более агрессивно и повторяем запрос
                        if finish_reason == "length" and parse_attempt < 2:
                            logger.warning(f"Ответ обрезан из-за лимита токенов (finish_reason=length), попытка {parse_attempt + 1}/3. Обрезаю историю более агрессивно.")
                            # Обрезаем историю до последних 2 сообщений
                            trimmed_history_aggressive = self._trim_history_to_fit_tokens(
                                system_prompt=system_prompt,
                                conversation_history=conversation_history if conversation_history else [],
                                user_message=user_message_content,
                                knowledge_context=knowledge_context if knowledge_context else "",
                                max_context_tokens=5000,  # ЭКСТРЕМАЛЬНО строгий лимит
                                max_response_tokens=300  # Место для ответа
                            )
                            # Убираем всю историю при переполнении
                            trimmed_history_aggressive = []
                            
                            messages = [
                                {"role": "system", "content": system_prompt}
                            ]
                            messages.extend(trimmed_history_aggressive)
                            messages.append({
                                "role": "user",
                                "content": user_message_content
                            })
                            continue  # Повторяем запрос с обрезанной историей
                        
                        # Проверяем, что ответ содержит реальный контент (не только пробелы/табуляции)
                        ai_response_clean = ai_response.strip() if ai_response else ""
                        # Проверяем, есть ли в ответе хотя бы один символ, который не пробел/табуляция/перенос строки
                        has_real_content = bool(ai_response_clean and any(c not in ' \t\n\r' for c in ai_response_clean))
                        
                        # Логируем ответ для отладки
                        if not has_real_content:
                            print(f"Получен пустой/некорректный ответ от ИИ (только пробелы/табуляции), попытка {parse_attempt + 1}/3")
                            print(f"Полный ответ API: {data}")
                            print(f"Choices: {data.get('choices', [])}")
                            if parse_attempt < 2:  # Если не последняя попытка
                                continue  # Повторяем запрос
                            else:
                                # Последняя попытка - возвращаем ошибку
                                return ("Извините, произошла ошибка при обработке запроса. Попробуйте переформулировать вопрос.", "", "")
                        else:
                            print(f"Получен ответ от ИИ (длина: {len(ai_response)}, finish_reason: {finish_reason}): {ai_response[:200]}")
                        
                        # Парсим JSON ответ от ИИ
                        extracted_name = ""
                        extracted_phone = ""
                        response_text = ""  # Инициализируем перед парсингом
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

                            # ============================================================
                            # ИТОГОВОЕ РЕЗЮМЕ ЗАПРОСА
                            # ============================================================
                            response_length = len(response_text)
                            logger.info("=" * 70)
                            logger.info("✅ ЗАПРОС УСПЕШНО ЗАВЕРШЁН")
                            logger.info("-" * 70)
                            logger.info(f"  Длина ответа: {response_length} символов")
                            logger.info(f"  Извлечено имя: {'Да (' + extracted_name + ')' if extracted_name else 'Нет'}")
                            logger.info(f"  Извлечён телефон: {'Да (' + extracted_phone + ')' if extracted_phone else 'Нет'}")
                            logger.info(f"  Finish reason: {finish_reason}")
                            logger.info(f"  Попыток парсинга: {parse_attempt + 1}")
                            logger.info("-" * 70)
                            logger.info(f"  💰 Стоимость запроса:")
                            input_cost = (actual_prompt_tokens / 1_000_000) * 0.150  # $0.150 за 1M токенов
                            output_cost = (actual_completion_tokens / 1_000_000) * 0.600  # $0.600 за 1M токенов
                            total_cost = input_cost + output_cost
                            logger.info(f"     Input:  {actual_prompt_tokens} токенов × $0.150/1M = ${input_cost:.6f}")
                            logger.info(f"     Output: {actual_completion_tokens} токенов × $0.600/1M = ${output_cost:.6f}")
                            logger.info(f"     ИТОГО: ${total_cost:.6f}")
                            logger.info("=" * 70)

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
            except httpx.TimeoutException as e:
                logger.error(f"Таймаут при запросе к OpenAI API: {e}")
                if proxy_attempt == 0 and self.proxy_url:
                    print("Таймаут с прокси, пробую без прокси...")
                    continue  # Пробуем без прокси
                return ("Извините, запрос занял слишком много времени. Попробуйте позже.", "", "")
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP ошибка при запросе к OpenAI API: {e.response.status_code} - {e.response.text}")
                if e.response.status_code == 429:  # Rate limit
                    return ("Извините, слишком много запросов. Пожалуйста, подождите немного и попробуйте снова.", "", "")
                elif e.response.status_code >= 500:  # Server error
                    return ("Извините, сервер временно недоступен. Попробуйте позже.", "", "")
                else:
                    return ("Извините, произошла ошибка при обработке запроса. Попробуйте позже.", "", "")
            except Exception as e:
                import traceback
                logger.error(f"Неожиданная ошибка при запросе к OpenAI API: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
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
