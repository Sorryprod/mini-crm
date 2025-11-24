from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# Operator schemas
class OperatorBase(BaseModel):
    name: str
    is_active: bool = True
    max_load: int = 10


class OperatorCreate(OperatorBase):
    pass


class OperatorUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    max_load: Optional[int] = None


class OperatorResponse(OperatorBase):
    id: int
    current_load: int = 0
    
    class Config:
        from_attributes = True


# Source schemas
class SourceBase(BaseModel):
    name: str
    description: Optional[str] = None


class SourceCreate(SourceBase):
    pass


class SourceResponse(SourceBase):
    id: int
    
    class Config:
        from_attributes = True


# Weight schemas
class WeightConfig(BaseModel):
    operator_id: int
    weight: int = Field(gt=0, description="Вес должен быть больше 0")


class SourceWeightUpdate(BaseModel):
    source_id: int
    weights: List[WeightConfig]


# Lead schemas
class LeadBase(BaseModel):
    external_id: str
    name: Optional[str] = None


class LeadCreate(LeadBase):
    pass


class LeadResponse(LeadBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Appeal schemas
class AppealCreate(BaseModel):
    lead_external_id: str
    lead_name: Optional[str] = None
    source_id: int
    message: Optional[str] = None


class AppealResponse(BaseModel):
    id: int
    lead_id: int
    source_id: int
    operator_id: Optional[int]
    operator_name: Optional[str] = None
    status: str
    message: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Statistics
class OperatorStats(BaseModel):
    operator_id: int
    operator_name: str
    is_active: bool
    current_load: int
    max_load: int
    total_appeals: int


class SourceStats(BaseModel):
    source_id: int
    source_name: str
    total_appeals: int
    operators_count: int