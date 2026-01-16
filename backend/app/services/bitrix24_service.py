import httpx
import logging
from typing import Optional, Dict
from app.core.config import settings

logger = logging.getLogger(__name__)

class Bitrix24Service:
    def __init__(self):
        self.webhook_url = settings.bitrix24_webhook_url
        self.enabled = bool(self.webhook_url)
        
        if not self.enabled:
            logger.warning("Bitrix24 webhook URL не настроен. Интеграция отключена.")
    
    def format_phone(self, phone: str) -> str:
        """Преобразование телефона в формат для Bitrix24"""
        # Убираем все нецифровые символы
        digits = ''.join(filter(str.isdigit, phone))
        
        # Если номер начинается с 8, заменяем на +7
        if digits.startswith('8') and len(digits) == 11:
            return '+7' + digits[1:]
        # Если номер начинается с 7 и 11 цифр, добавляем +
        elif digits.startswith('7') and len(digits) == 11:
            return '+' + digits
        # Если 10 цифр, добавляем +7
        elif len(digits) == 10:
            return '+7' + digits
        # Если уже есть +, возвращаем как есть
        elif phone.startswith('+'):
            return phone
        else:
            # По умолчанию добавляем +7
            return '+7' + digits[-10:] if len(digits) >= 10 else phone
    
    async def create_lead(self, name: str, phone: str, comments: Optional[str] = None) -> Dict:
        """
        Создание лида в Bitrix24
        
        Args:
            name: Имя контакта
            phone: Номер телефона
            comments: Дополнительные комментарии (опционально)
        
        Returns:
            Dict с результатом операции
        """
        if not self.enabled:
            logger.warning("Bitrix24 интеграция отключена. Лид не создан.")
            return {"success": False, "error": "Bitrix24 не настроен"}
        
        if not name or not phone:
            logger.warning(f"Недостаточно данных для создания лида: name={name}, phone={phone}")
            return {"success": False, "error": "Недостаточно данных"}
        
        # Форматируем телефон
        formatted_phone = self.format_phone(phone)
        
        # Подготавливаем данные для Bitrix24
        fields = {
            "NAME": name,
            "PHONE": [
                {
                    "VALUE": formatted_phone,
                    "VALUE_TYPE": "WORK"
                }
            ]
        }
        
        # Добавляем комментарии, если есть
        if comments:
            fields["COMMENTS"] = comments
        
        # Добавляем источник
        fields["SOURCE_ID"] = "WEB"  # Источник - веб-сайт
        
        payload = {
            "FIELDS": fields
        }
        
        try:
            # Убеждаемся, что URL заканчивается на /
            webhook_url = self.webhook_url.rstrip('/') + '/'
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{webhook_url}crm.lead.add",
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                
                if result.get("result"):
                    lead_id = result.get("result")
                    logger.info(f"Лид успешно создан в Bitrix24: ID={lead_id}, name={name}, phone={formatted_phone}")
                    return {
                        "success": True,
                        "lead_id": lead_id,
                        "name": name,
                        "phone": formatted_phone
                    }
                else:
                    error = result.get("error", "Неизвестная ошибка")
                    logger.error(f"Ошибка создания лида в Bitrix24: {error}")
                    return {
                        "success": False,
                        "error": error,
                        "response": result
                    }
                    
        except httpx.TimeoutException:
            logger.error("Таймаут при создании лида в Bitrix24")
            return {"success": False, "error": "Таймаут запроса"}
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP ошибка при создании лида в Bitrix24: {e.response.status_code} - {e.response.text}")
            return {"success": False, "error": f"HTTP {e.response.status_code}"}
        except Exception as e:
            logger.error(f"Неожиданная ошибка при создании лида в Bitrix24: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

# Создаем глобальный экземпляр сервиса
bitrix24_service = Bitrix24Service()
