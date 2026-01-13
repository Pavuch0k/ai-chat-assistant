from pydantic import BaseModel, EmailStr
from typing import Optional

class ContactData(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    contact: ContactData

class ChatResponse(BaseModel):
    response: str
