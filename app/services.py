from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import Optional, List
import random
from . import models, schemas


class OperatorService:
    @staticmethod
    def create(db: Session, operator: schemas.OperatorCreate) -> models.Operator:
        db_operator = models.Operator(**operator.model_dump())
        db.add(db_operator)
        db.commit()
        db.refresh(db_operator)
        return db_operator
    
    @staticmethod
    def get_all(db: Session) -> List[models.Operator]:
        return db.query(models.Operator).all()
    
    @staticmethod
    def get_by_id(db: Session, operator_id: int) -> Optional[models.Operator]:
        return db.query(models.Operator).filter(models.Operator.id == operator_id).first()
    
    @staticmethod
    def update(db: Session, operator_id: int, operator_update: schemas.OperatorUpdate) -> Optional[models.Operator]:
        db_operator = OperatorService.get_by_id(db, operator_id)
        if not db_operator:
            return None
        
        update_data = operator_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_operator, field, value)
        
        db.commit()
        db.refresh(db_operator)
        return db_operator
    
    @staticmethod
    def get_current_load(db: Session, operator_id: int) -> int:
        """Подсчет текущей нагрузки (активных обращений)"""
        return db.query(models.Appeal).filter(
            and_(
                models.Appeal.operator_id == operator_id,
                models.Appeal.status == "active"
            )
        ).count()
    
    @staticmethod
    def get_stats(db: Session) -> List[schemas.OperatorStats]:
        operators = db.query(models.Operator).all()
        stats = []
        
        for op in operators:
            current_load = OperatorService.get_current_load(db, op.id)
            total_appeals = db.query(models.Appeal).filter(models.Appeal.operator_id == op.id).count()
            
            stats.append(schemas.OperatorStats(
                operator_id=op.id,
                operator_name=op.name,
                is_active=op.is_active,
                current_load=current_load,
                max_load=op.max_load,
                total_appeals=total_appeals
            ))
        
        return stats


class SourceService:
    @staticmethod
    def create(db: Session, source: schemas.SourceCreate) -> models.Source:
        db_source = models.Source(**source.model_dump())
        db.add(db_source)
        db.commit()
        db.refresh(db_source)
        return db_source
    
    @staticmethod
    def get_all(db: Session) -> List[models.Source]:
        return db.query(models.Source).all()
    
    @staticmethod
    def get_by_id(db: Session, source_id: int) -> Optional[models.Source]:
        return db.query(models.Source).filter(models.Source.id == source_id).first()
    
    @staticmethod
    def set_weights(db: Session, config: schemas.SourceWeightUpdate) -> bool:
        """Настройка весов операторов для источника"""
        # Удаляем старые веса
        db.query(models.OperatorSourceWeight).filter(
            models.OperatorSourceWeight.source_id == config.source_id
        ).delete()
        
        # Добавляем новые
        for weight_config in config.weights:
            db_weight = models.OperatorSourceWeight(
                source_id=config.source_id,
                operator_id=weight_config.operator_id,
                weight=weight_config.weight
            )
            db.add(db_weight)
        
        db.commit()
        return True
    
    @staticmethod
    def get_weights(db: Session, source_id: int) -> List[models.OperatorSourceWeight]:
        return db.query(models.OperatorSourceWeight).filter(
            models.OperatorSourceWeight.source_id == source_id
        ).all()


class LeadService:
    @staticmethod
    def get_or_create(db: Session, external_id: str, name: Optional[str] = None) -> models.Lead:
        """Найти существующего лида или создать нового"""
        lead = db.query(models.Lead).filter(models.Lead.external_id == external_id).first()
        
        if not lead:
            lead = models.Lead(external_id=external_id, name=name)
            db.add(lead)
            db.commit()
            db.refresh(lead)
        
        return lead
    
    @staticmethod
    def get_all(db: Session) -> List[models.Lead]:
        return db.query(models.Lead).all()


class AppealService:
    @staticmethod
    def create(db: Session, appeal_data: schemas.AppealCreate) -> models.Appeal:
        """
        Создание обращения с автоматическим распределением оператора
        
        Алгоритм:
        1. Найти/создать лида
        2. Определить доступных операторов для источника
        3. Выбрать оператора по весам (weighted random)
        4. Создать обращение
        """
        # 1. Найти или создать лида
        lead = LeadService.get_or_create(db, appeal_data.lead_external_id, appeal_data.lead_name)
        
        # 2. Выбрать оператора
        operator = AppealService._select_operator(db, appeal_data.source_id)
        
        # 3. Создать обращение
        db_appeal = models.Appeal(
            lead_id=lead.id,
            source_id=appeal_data.source_id,
            operator_id=operator.id if operator else None,
            message=appeal_data.message,
            status="active"
        )
        
        db.add(db_appeal)
        db.commit()
        db.refresh(db_appeal)
        
        return db_appeal
    
    @staticmethod
    def _select_operator(db: Session, source_id: int) -> Optional[models.Operator]:
        """
        Выбор оператора по весам с учетом лимитов
        
        Алгоритм: Weighted Random Selection
        - Получаем всех операторов для источника с весами
        - Фильтруем активных и не превысивших лимит
        - Выбираем случайно с вероятностью пропорциональной весу
        """
        # Получаем веса для источника
        weights = db.query(models.OperatorSourceWeight).filter(
            models.OperatorSourceWeight.source_id == source_id
        ).all()
        
        if not weights:
            return None
        
        # Фильтруем доступных операторов
        available_operators = []
        available_weights = []
        
        for weight_config in weights:
            operator = weight_config.operator
            
            # Проверяем активность
            if not operator.is_active:
                continue
            
            # Проверяем нагрузку
            current_load = OperatorService.get_current_load(db, operator.id)
            if current_load >= operator.max_load:
                continue
            
            available_operators.append(operator)
            available_weights.append(weight_config.weight)
        
        if not available_operators:
            return None
        
        # Weighted random selection
        total_weight = sum(available_weights)
        probabilities = [w / total_weight for w in available_weights]
        
        selected_operator = random.choices(available_operators, weights=probabilities, k=1)[0]
        return selected_operator
    
    @staticmethod
    def get_all(db: Session, limit: int = 100) -> List[models.Appeal]:
        return db.query(models.Appeal).order_by(models.Appeal.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_by_lead(db: Session, lead_id: int) -> List[models.Appeal]:
        return db.query(models.Appeal).filter(models.Appeal.lead_id == lead_id).all()