import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings
from app.core.config import settings
from typing import List, Optional
import uuid

class KnowledgeService:
    def __init__(self):
        self.qdrant_url = settings.qdrant_url.replace("http://", "").replace("https://", "")
        if ":" in self.qdrant_url:
            host, port = self.qdrant_url.split(":")
            self.qdrant_client = QdrantClient(host=host, port=int(port))
        else:
            self.qdrant_client = QdrantClient(url=settings.qdrant_url)
        
        self.collection_name = "knowledge_base"
        self.embedding_model = None  # Ленивая загрузка
        self._model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        
        # Создаем коллекцию если не существует
        try:
            self.qdrant_client.get_collection(self.collection_name)
        except:
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
    
    def _get_embedding_model(self):
        """Ленивая загрузка модели эмбеддингов"""
        if self.embedding_model is None:
            print("Загрузка модели эмбеддингов...")
            self.embedding_model = HuggingFaceEmbeddings(
                model_name=self._model_name
            )
            print("Модель эмбеддингов загружена")
        return self.embedding_model
    
    def add_document(self, text: str, document_id: int, metadata: dict = None) -> bool:
        """Добавить документ в базу знаний"""
        try:
            # Разбиваем текст на чанки
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
            )
            chunks = text_splitter.split_text(text)
            
            # Создаем эмбеддинги для каждого чанка
            embedding_model = self._get_embedding_model()
            points = []
            for i, chunk in enumerate(chunks):
                embedding = embedding_model.embed_query(chunk)
                point_id = str(uuid.uuid4())
                
                point_metadata = {
                    "document_id": document_id,
                    "chunk_index": i,
                    "text": chunk,
                    **(metadata or {})
                }
                
                points.append(PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=point_metadata
                ))
            
            # Добавляем в Qdrant
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            return True
        except Exception as e:
            print(f"Error adding document to knowledge base: {e}")
            return False
    
    def search(self, query: str, limit: int = 3) -> List[dict]:
        """Поиск в базе знаний"""
        try:
            # Создаем эмбеддинг для запроса
            embedding_model = self._get_embedding_model()
            query_embedding = embedding_model.embed_query(query)
            
            # Ищем в Qdrant
            results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit
            )
            
            # Формируем результат
            search_results = []
            for result in results:
                search_results.append({
                    "text": result.payload.get("text", ""),
                    "score": result.score,
                    "metadata": {k: v for k, v in result.payload.items() if k != "text"}
                })
            
            return search_results
        except Exception as e:
            print(f"Error searching knowledge base: {e}")
            return []
    
    def delete_document(self, document_id: int) -> bool:
        """Удалить документ из базы знаний"""
        try:
            # Находим все точки с этим document_id
            scroll_result = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                scroll_filter={
                    "must": [{
                        "key": "document_id",
                        "match": {"value": document_id}
                    }]
                },
                limit=10000
            )
            
            # Удаляем точки
            if scroll_result[0]:
                point_ids = [point.id for point in scroll_result[0]]
                self.qdrant_client.delete(
                    collection_name=self.collection_name,
                    points_selector=point_ids
                )
            return True
        except Exception as e:
            print(f"Error deleting document from knowledge base: {e}")
            return False

knowledge_service = KnowledgeService()
