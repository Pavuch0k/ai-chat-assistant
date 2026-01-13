from fastapi import APIRouter
from app.models.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/api", tags=["chat"])

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # Временная заглушка - позже будет интеграция с AI
    response_text = f"Спасибо за сообщение: {request.message}. Мы обработаем ваш запрос и свяжемся с вами."
    return ChatResponse(response=response_text)
