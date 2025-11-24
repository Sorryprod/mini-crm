from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import schemas, services
from ..database import get_db

router = APIRouter(prefix="/appeals", tags=["Appeals"])


@router.post("/", response_model=schemas.AppealResponse)
def create_appeal(appeal: schemas.AppealCreate, db: Session = Depends(get_db)):
    """
    Зарегистрировать новое обращение
    
    Автоматически:
    - Найдет существующего лида или создаст нового
    - Выберет оператора по весам с учетом нагрузки
    - Создаст обращение
    """
    # Проверяем существование источника
    source = services.SourceService.get_by_id(db, appeal.source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    db_appeal = services.AppealService.create(db, appeal)
    
    operator_name = None
    if db_appeal.operator:
        operator_name = db_appeal.operator.name
    
    return schemas.AppealResponse(
        id=db_appeal.id,
        lead_id=db_appeal.lead_id,
        source_id=db_appeal.source_id,
        operator_id=db_appeal.operator_id,
        operator_name=operator_name,
        status=db_appeal.status,
        message=db_appeal.message,
        created_at=db_appeal.created_at
    )


@router.get("/", response_model=List[schemas.AppealResponse])
def get_appeals(limit: int = 100, db: Session = Depends(get_db)):
    """Получить список обращений"""
    appeals = services.AppealService.get_all(db, limit)
    
    result = []
    for appeal in appeals:
        operator_name = appeal.operator.name if appeal.operator else None
        result.append(schemas.AppealResponse(
            id=appeal.id,
            lead_id=appeal.lead_id,
            source_id=appeal.source_id,
            operator_id=appeal.operator_id,
            operator_name=operator_name,
            status=appeal.status,
            message=appeal.message,
            created_at=appeal.created_at
        ))
    
    return result


@router.get("/leads", response_model=List[schemas.LeadResponse])
def get_leads(db: Session = Depends(get_db)):
    """Получить список лидов"""
    return services.LeadService.get_all(db)


@router.get("/leads/{lead_id}/appeals")
def get_lead_appeals(lead_id: int, db: Session = Depends(get_db)):
    """Получить все обращения конкретного лида"""
    appeals = services.AppealService.get_by_lead(db, lead_id)
    
    result = []
    for appeal in appeals:
        result.append({
            "id": appeal.id,
            "source_name": appeal.source.name,
            "operator_name": appeal.operator.name if appeal.operator else None,
            "status": appeal.status,
            "created_at": appeal.created_at
        })
    
    return result