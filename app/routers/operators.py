from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import schemas, services
from ..database import get_db

router = APIRouter(prefix="/operators", tags=["Operators"])


@router.post("/", response_model=schemas.OperatorResponse)
def create_operator(operator: schemas.OperatorCreate, db: Session = Depends(get_db)):
    """Создать нового оператора"""
    return services.OperatorService.create(db, operator)


@router.get("/", response_model=List[schemas.OperatorResponse])
def get_operators(db: Session = Depends(get_db)):
    """Получить список всех операторов"""
    operators = services.OperatorService.get_all(db)
    
    result = []
    for op in operators:
        current_load = services.OperatorService.get_current_load(db, op.id)
        result.append(schemas.OperatorResponse(
            id=op.id,
            name=op.name,
            is_active=op.is_active,
            max_load=op.max_load,
            current_load=current_load
        ))
    
    return result


@router.patch("/{operator_id}", response_model=schemas.OperatorResponse)
def update_operator(
    operator_id: int, 
    operator_update: schemas.OperatorUpdate, 
    db: Session = Depends(get_db)
):
    """Обновить оператора (активность, лимит)"""
    operator = services.OperatorService.update(db, operator_id, operator_update)
    if not operator:
        raise HTTPException(status_code=404, detail="Operator not found")
    
    current_load = services.OperatorService.get_current_load(db, operator.id)
    return schemas.OperatorResponse(
        id=operator.id,
        name=operator.name,
        is_active=operator.is_active,
        max_load=operator.max_load,
        current_load=current_load
    )


@router.get("/stats", response_model=List[schemas.OperatorStats])
def get_operator_stats(db: Session = Depends(get_db)):
    """Получить статистику по операторам"""
    return services.OperatorService.get_stats(db)