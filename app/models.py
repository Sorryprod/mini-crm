from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Float, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class Operator(Base):
    __tablename__ = "operators"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    max_load = Column(Integer, default=10)  # Максимум активных обращений
    
    # Связи
    weights = relationship("OperatorSourceWeight", back_populates="operator", cascade="all, delete-orphan")
    appeals = relationship("Appeal", back_populates="operator")


class Source(Base):
    __tablename__ = "sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    
    # Связи
    weights = relationship("OperatorSourceWeight", back_populates="source", cascade="all, delete-orphan")
    appeals = relationship("Appeal", back_populates="source")


class OperatorSourceWeight(Base):
    """Веса операторов для каждого источника"""
    __tablename__ = "operator_source_weights"
    
    id = Column(Integer, primary_key=True, index=True)
    operator_id = Column(Integer, ForeignKey("operators.id"), nullable=False)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False)
    weight = Column(Integer, default=1)  # Числовой вес для распределения
    
    # Связи
    operator = relationship("Operator", back_populates="weights")
    source = relationship("Source", back_populates="weights")


class Lead(Base):
    __tablename__ = "leads"
    
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, unique=True, nullable=False, index=True)  # Уникальный ID (телефон, email и т.д.)
    name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    appeals = relationship("Appeal", back_populates="lead")


class Appeal(Base):
    """Обращение лида из источника"""
    __tablename__ = "appeals"
    
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False)
    operator_id = Column(Integer, ForeignKey("operators.id"), nullable=True)  # Может быть NULL если нет доступных
    
    status = Column(String, default="active")  # active, closed
    message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    
    # Связи
    lead = relationship("Lead", back_populates="appeals")
    source = relationship("Source", back_populates="appeals")
    operator = relationship("Operator", back_populates="appeals")