from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import date

class ProposalBase(BaseModel):
    """Base schema for proposal data"""
    customer_name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    system_type: str
    status: str = "Pending"
    submission_date: date = Field(default_factory=date.today)
    estimated_cost: Optional[float] = 0.0
    
    @validator('email')
    def validate_email(cls, v):
        # Basic email validation
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v

class ProposalCreate(ProposalBase):
    """Schema for creating a new proposal"""
    pass

class ProposalResponse(ProposalBase):
    """Schema for proposal response"""
    id: int
    
    class Config:
        from_attributes = True  # Updated from orm_mode for Pydantic v2
        
class ProposalUpdate(BaseModel):
    """Schema for updating an existing proposal"""
    customer_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    system_type: Optional[str] = None
    status: Optional[str] = None
    estimated_cost: Optional[float] = None
