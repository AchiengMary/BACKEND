from sqlalchemy import Column, Integer, String, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from datetime import date

from customer_proposal.database import Base

class Proposal(Base):
    """SQLAlchemy model for storing proposal information"""
    __tablename__ = "proposals"

    id = Column(Integer, primary_key=True, index=True)
    
    # Customer Information
    customer_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    
    # System Details
    system_type = Column(String, nullable=False)
    status = Column(String, nullable=False, default="Pending")
    submission_date = Column(Date, nullable=False, default=date.today)
    estimated_cost = Column(Float, nullable=True)
