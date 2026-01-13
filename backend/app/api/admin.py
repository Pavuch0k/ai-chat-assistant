from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.db_models import Contact, Message
from typing import List
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/api/admin", tags=["admin"])

class ContactResponse(BaseModel):
    id: int
    name: str = None
    email: str = None
    phone: str = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    id: int
    contact_id: int = None
    message: str
    response: str = None
    is_from_user: int
    created_at: datetime
    
    class Config:
        from_attributes = True

@router.get("/contacts", response_model=List[ContactResponse])
async def get_contacts(db: Session = Depends(get_db)):
    """Получить список всех контактов"""
    contacts = db.query(Contact).order_by(Contact.created_at.desc()).all()
    return contacts

@router.get("/contacts/{contact_id}/messages", response_model=List[MessageResponse])
async def get_contact_messages(contact_id: int, db: Session = Depends(get_db)):
    """Получить историю сообщений контакта"""
    messages = db.query(Message).filter(Message.contact_id == contact_id).order_by(Message.created_at).all()
    return messages

@router.get("/messages", response_model=List[MessageResponse])
async def get_all_messages(db: Session = Depends(get_db), limit: int = 100):
    """Получить все сообщения"""
    messages = db.query(Message).order_by(Message.created_at.desc()).limit(limit).all()
    return messages
