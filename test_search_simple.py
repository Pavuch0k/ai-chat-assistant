#!/usr/bin/env python3
"""Простой тестовый скрипт для проверки поиска в базе знаний"""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from langchain_community.embeddings import HuggingFaceEmbeddings
import re

# Подключаемся к Qdrant
client = QdrantClient(host="localhost", port=6333)
collection_name = "knowledge_base"

# Загружаем модель эмбеддингов
print("Загрузка модели эмбеддингов...")
embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
print("Модель загружена\n")

def test_search(query: str):
    """Тестирует поиск по запросу"""
    print(f"\n{'='*60}")
    print(f"Запрос: {query}")
    print(f"{'='*60}")
    
    # Извлекаем имя если есть
    query_normalized = query.lower().strip()
    name_patterns = [
        r'(?:кто такая|кто такой|who is|tell me about)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
        r'([A-Z][a-z]+\s+[A-Z][a-z]+)',  # Просто имя и фамилия
    ]
    for pattern in name_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            query_normalized = match.group(1).lower()
            print(f"Извлечено имя: {query_normalized}")
            break
    
    # Создаем эмбеддинг
    query_embedding = embedding_model.embed_query(query_normalized)
    
    # Ищем в Qdrant
    results = client.search(
        collection_name=collection_name,
        query_vector=query_embedding,
        limit=15  # Берем больше для анализа
    )
    
    if not results:
        print("❌ Результаты не найдены!")
        return False
    
    print(f"\n✅ Найдено результатов: {len(results)}\n")
    
    found_karena = False
    karena_results = []
    
    for i, result in enumerate(results, 1):
        score = result.score
        text = result.payload.get("text", "")
        
        # Проверяем наличие Karena Zhou
        if 'Karena' in text or 'Karena Zhou' in text or 'Karena Zhou' in text:
            found_karena = True
            karena_results.append((i, score, text))
            print(f"🎯 ФРАГМЕНТ {i} (score: {score:.3f}) - НАЙДЕН KARENA!")
        else:
            print(f"   Фрагмент {i} (score: {score:.3f})")
        
        # Показываем первые 150 символов
        preview = text[:150].replace('\n', ' ').strip()
        if preview:
            print(f"   {preview}...")
        print()
    
    if found_karena:
        print("✅ УСПЕХ! Karena Zhou найден в результатах!")
        print(f"\nВсего фрагментов с Karena: {len(karena_results)}")
        for idx, score, text in karena_results:
            print(f"\n--- Фрагмент {idx} (score: {score:.3f}) ---")
            print(text[:300])
        return True
    else:
        print("❌ Karena Zhou НЕ найден в результатах поиска")
        print(f"\nТоп-3 результата:")
        for i, result in enumerate(results[:3], 1):
            print(f"\n{i}. Score: {result.score:.3f}")
            print(result.payload.get("text", "")[:200])
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
        "кто такая Karena Zhou",
    ]
    
    success_count = 0
    for query in queries:
        if test_search(query):
            success_count += 1
        print()
    
    print(f"\n{'='*60}")
    print(f"Итого: {success_count}/{len(queries)} запросов нашли Karena Zhou")
    print(f"{'='*60}")
