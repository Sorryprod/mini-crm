from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import schemas, services
from ..database import get_db

router = APIRouter(prefix="/sources", tags=["Sources"])


@router.post("/", response_model=schemas.SourceResponse)
def create_source(source: schemas.SourceCreate, db: Session = Depends(get_db)):
    """Создать новый источник (бот)"""
    return services.SourceService.create(db, source)


@router.get("/", response_model=List[schemas.SourceResponse])
def get_sources(db: Session = Depends(get_db)):
    """Получить список всех источников"""
    return services.SourceService.get_all(db)


@router.post("/weights")
def set_source_weights(config: schemas.SourceWeightUpdate, db: Session = Depends(get_db)):
    """Настроить веса операторов для источника"""
    # Проверяем существование источника
    source = services.SourceService.get_by_id(db, config.source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    # Проверяем существование операторов
    for weight in config.weights:
        operator = services.OperatorService.get_by_id(db, weight.operator_id)
        if not operator:
            raise HTTPException(status_code=404, detail=f"Operator {weight.operator_id} not found")
    
    services.SourceService.set_weights(db, config)
    return {"status": "success", "message": "Weights updated"}


@router.get("/{source_id}/weights")
def get_source_weights(source_id: int, db: Session = Depends(get_db)):
    """Получить настройки весов для источника"""
    weights = services.SourceService.get_weights(db, source_id)
    
    result = []
    for w in weights:
        result.append({
            "operator_id": w.operator_id,
            "operator_name": w.operator.name,
            "weight": w.weight
        })
    
    return result