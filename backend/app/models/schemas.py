from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None  # Идентификатор сессии для связывания сообщений

class ChatResponse(BaseModel):
    response: str
    session_id: Optional[str] = None  # Идентификатор сессии для следующего запроса
