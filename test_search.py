#!/usr/bin/env python3
"""Тестовый скрипт для проверки поиска в базе знаний"""

import sys
import os

# Настраиваем окружение
os.environ.setdefault('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/ai_chat')
os.environ.setdefault('QDRANT_URL', 'http://localhost:6333')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.knowledge_service import knowledge_service

def test_search(query: str):
    """Тестирует поиск по запросу"""
    print(f"\n{'='*60}")
    print(f"Запрос: {query}")
    print(f"{'='*60}")
    
    results = knowledge_service.search(query, limit=10, score_threshold=0.1)
    
    if not results:
        print("❌ Результаты не найдены!")
        return False
    
    print(f"\n✅ Найдено результатов: {len(results)}\n")
    
    found_karena = False
    for i, result in enumerate(results, 1):
        score = result.get('score', 0)
        text = result['text']
        
        # Проверяем наличие Karena Zhou
        if 'Karena' in text or 'Karena Zhou' in text:
            found_karena = True
            print(f"🎯 ФРАГМЕНТ {i} (score: {score:.3f}) - НАЙДЕН KARENA!")
        else:
            print(f"   Фрагмент {i} (score: {score:.3f})")
        
        # Показываем первые 200 символов
        preview = text[:200].replace('\n', ' ')
        print(f"   {preview}...")
        print()
    
    if found_karena:
        print("✅ УСПЕХ! Karena Zhou найден в результатах!")
        return True
    else:
        print("❌ Karena Zhou НЕ найден в результатах поиска")
        return False

if __name__ == "__main__":
    # Тестируем разные варианты запросов
    queries = [
        "Karena Zhou",
        "Karena Zhou кто такая",
        "Karena",
        "Teaching Director",
        "Who is Karena Zhou",
        "Karena Zhou кто",
    ]
    
    print("Загрузка модели эмбеддингов...")
    # Принудительно загружаем модель
    knowledge_service._get_embedding_model()
    print("Модель загружена\n")
    
    success_count = 0
    for query in queries:
        if test_search(query):
            success_count += 1
        print()
    
    print(f"\n{'='*60}")
    print(f"Итого: {success_count}/{len(queries)} запросов нашли Karena Zhou")
    print(f"{'='*60}")
