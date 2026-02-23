from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from app.db.database import get_db
from app.models.db_models import Project, WidgetSettings, AdminUser
from app.core.auth import get_current_user

router = APIRouter(prefix="/api/projects", tags=["projects"])

class ProjectCreate(BaseModel):
    name: str
    description: str = ""

class ProjectUpdate(BaseModel):
    name: str = None
    description: str = None
    is_active: bool = None
    openai_api_key: str = None
    bitrix_webhook_url: str = None
    custom_webhook_url: str = None
    allowed_origins: str = None

class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True

class ProjectStatsResponse(BaseModel):
    id: int
    name: str
    description: str
    is_active: bool
    contacts_count: int
    messages_count: int
    created_at: str

    class Config:
        from_attributes = True

@router.get("", response_model=List[ProjectStatsResponse])
async def get_projects(
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Получить список всех проектов со статистикой"""
    from app.models.db_models import Contact, Message

    projects = db.query(Project).all()

    result = []
    for project in projects:
        contacts_count = db.query(Contact).filter(Contact.project_id == project.id).count()
        messages_count = db.query(Message).filter(Message.project_id == project.id).count()

        result.append({
            "id": project.id,
            "name": project.name,
            "description": project.description or "",
            "is_active": project.is_active,
            "contacts_count": contacts_count,
            "messages_count": messages_count,
            "created_at": project.created_at.isoformat()
        })

    return result

@router.post("", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Создать новый проект"""
    new_project = Project(
        name=project_data.name,
        description=project_data.description,
        is_active=True
    )
    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    # Создаем настройки виджета для нового проекта
    widget_settings = WidgetSettings(project_id=new_project.id)
    db.add(widget_settings)
    db.commit()

    return new_project

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Получить информацию о проекте"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")
    return project

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Обновить проект"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")

    if project_data.name is not None:
        project.name = project_data.name
    if project_data.description is not None:
        project.description = project_data.description
    if project_data.is_active is not None:
        project.is_active = project_data.is_active
    if project_data.openai_api_key is not None:
        project.openai_api_key = project_data.openai_api_key
    if project_data.bitrix_webhook_url is not None:
        project.bitrix_webhook_url = project_data.bitrix_webhook_url
    if project_data.custom_webhook_url is not None:
        project.custom_webhook_url = project_data.custom_webhook_url
    if project_data.allowed_origins is not None:
        project.allowed_origins = project_data.allowed_origins

    db.commit()
    db.refresh(project)
    return project

@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Удалить проект"""
    if project_id == 1:
        raise HTTPException(status_code=400, detail="Нельзя удалить дефолтный проект")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")

    db.delete(project)
    db.commit()

    return {"success": True, "message": "Проект удален"}


class SecretsUpdate(BaseModel):
    openai_api_key: str = None
    bitrix_webhook_url: str = None
    custom_webhook_url: str = None


class SecretsResponse(BaseModel):
    has_openai_key: bool
    bitrix_webhook_url: str
    custom_webhook_url: str


class CORSUpdate(BaseModel):
    allowed_origins: str


@router.get("/{project_id}/secrets")
async def get_project_secrets(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Получить секреты проекта (ключи маскируются)"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")

    return {
        "has_openai_key": bool(project.openai_api_key),
        "openai_key_masked": ("sk-..." + project.openai_api_key[-4:]) if project.openai_api_key else "",
        "bitrix_webhook_url": project.bitrix_webhook_url or "",
        "custom_webhook_url": project.custom_webhook_url or "",
        "allowed_origins": project.allowed_origins or "*"
    }


@router.put("/{project_id}/secrets")
async def update_project_secrets(
    project_id: int,
    data: SecretsUpdate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Обновить секреты проекта"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")

    if data.openai_api_key is not None and data.openai_api_key.strip():
        project.openai_api_key = data.openai_api_key.strip()
    if data.bitrix_webhook_url is not None:
        project.bitrix_webhook_url = data.bitrix_webhook_url.strip() or None
    if data.custom_webhook_url is not None:
        project.custom_webhook_url = data.custom_webhook_url.strip() or None

    db.commit()
    return {"success": True, "message": "Секреты обновлены"}


@router.put("/{project_id}/cors")
async def update_project_cors(
    project_id: int,
    data: CORSUpdate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Обновить CORS настройки проекта"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")

    project.allowed_origins = data.allowed_origins.strip() or "*"
    db.commit()
    return {"success": True, "message": "CORS настройки обновлены"}
