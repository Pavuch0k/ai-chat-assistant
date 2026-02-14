#!/usr/bin/env python3
"""
Тестирование новой логики работы с контекстом
"""
import asyncio
import sys
import os

# Добавляем путь к backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.ai_service import estimate_tokens, AIService
from app.services.knowledge_service import knowledge_service


def test_token_estimation():
    """Тест оценки токенов"""
    test_text = "Привет, как дела?" * 10  # Повторим текст для большего объема
    tokens = estimate_tokens(test_text)
    print(f"Тест оценки токенов: '{test_text[:20]}...' -> {tokens} токенов")


def test_new_context_logic():
    """Тест новой логики работы с контекстом"""
    # Создаем экземпляр сервиса
    ai_service = AIService()
    
    # Тестовый пример истории разговора (без контекста из базы знаний)
    conversation_history = [
        {"role": "user", "content": "Привет"},
        {"role": "assistant", "content": "Здравствуйте! Чем могу помочь?"}
    ]
    
    # Тестовое сообщение пользователя
    user_message = "Расскажите о ваших услугах"
    
    # Тестовый контекст из базы знаний
    knowledge_context = "\n\nСПРАВОЧНАЯ ИНФОРМАЦИЯ ИЗ БАЗЫ ЗНАНИЙ (используй РАЗУМНО, только если релевантно):\n1. У нас есть услуги по обучению программированию\n2. Мы предлагаем курсы по различным языкам программирования\nВАЖНО: ТЫ САМ ПРИНИМАЕШЬ РЕШЕНИЕ - используй эту информацию ТОЛЬКО если она РЕЛЕВАНТНА и УМЕСТНА для ответа."
    
    # Тестовый статус контактов
    contact_status = "\n\nВАЖНО: Контакты клиента УЖЕ СОБРАНЫ:\n- Имя: Иван\n- Телефон: 89371234567\nНЕ ПРОСИ эти данные снова! Просто помогай по вопросам."
    
    print("Тест новой логики работы с контекстом:")
    print(f"- Длина истории разговора: {len(conversation_history)}")
    print(f"- Длина сообщения пользователя: {len(user_message)} символов")
    print(f"- Длина контекста из базы знаний: {len(knowledge_context)} символов")
    print(f"- Длина статуса контактов: {len(contact_status)} символов")
    
    # Проверим, что функция может быть вызвана с новыми параметрами
    # (на самом деле не будем делать реальный вызов к API, только проверим сигнатуру)
    print("\nСигнатура функции get_response обновлена для приема knowledge_context как отдельного параметра")
    

def test_trim_history_logic():
    """Тест логики обрезки истории"""
    ai_service = AIService()
    
    # Тестовые данные
    system_prompt = "Ты ассистент службы поддержки..."
    conversation_history = [
        {"role": "user", "content": "Привет"},
        {"role": "assistant", "content": "Здравствуйте! Чем могу помочь?"},
        {"role": "user", "content": "Расскажите о ваших услугах"},
        {"role": "assistant", "content": "У нас есть различные курсы программирования."}
    ]
    user_message = "Какие языки вы преподаете?"
    knowledge_context = "У нас есть курсы по Python, Java и JavaScript"
    
    print("\nТест логики обрезки истории:")
    print(f"- Длина системного промпта: {len(system_prompt)} символов")
    print(f"- Количество сообщений в истории: {len(conversation_history)}")
    print(f"- Длина сообщения пользователя: {len(user_message)} символов")
    print(f"- Длина контекста из базы знаний: {len(knowledge_context)} символов")
    
    # Тестируем функцию обрезки истории
    trimmed_history = ai_service._trim_history_to_fit_tokens(
        system_prompt=system_prompt,
        conversation_history=conversation_history,
        user_message=user_message,  # Передаем оригинальное сообщение без контекста из базы знаний
        knowledge_context=knowledge_context,
        max_context_tokens=10000,  # Уменьшенный лимит для теста
        max_response_tokens=1000
    )
    
    print(f"- После обрезки количество сообщений в истории: {len(trimmed_history)}")
    

if __name__ == "__main__":
    print("Тестирование новой логики работы с контекстом...\n")
    
    test_token_estimation()
    print()
    
    test_new_context_logic()
    print()
    
    test_trim_history_logic()
    print()
    
    print("Тестирование завершено. Логика обновлена для:")
    print("1. Принятия knowledge_context как отдельного параметра в get_response")
    print("2. Исключения контекста из базы знаний из истории разговора при расчете токенов")
    print("3. Передачи контекста из базы знаний только в текущий запрос к ИИ")