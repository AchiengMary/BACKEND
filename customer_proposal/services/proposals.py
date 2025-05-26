from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from customer_proposal.database import get_db
from customer_proposal.model import Proposal
from customer_proposal.schemas import ProposalCreate, ProposalResponse, ProposalUpdate

router = APIRouter()

@router.post("/", response_model=ProposalResponse, status_code=status.HTTP_201_CREATED)
def create_proposal(proposal: ProposalCreate, db: Session = Depends(get_db)):
    """Create a new proposal"""
    # Create new proposal object from the provided data
    db_proposal = Proposal(
        customer_name=proposal.customer_name,
        email=proposal.email,
        phone=proposal.phone,
        address=proposal.address,
        system_type=proposal.system_type,
        status=proposal.status,
        submission_date=proposal.submission_date,
        estimated_cost=proposal.estimated_cost
    )
    
    # Add to database and commit
    db.add(db_proposal)
    db.commit()
    db.refresh(db_proposal)
    
    return db_proposal

@router.get("/", response_model=List[ProposalResponse])
def get_all_proposals(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """Get all proposals with pagination"""
    proposals = db.query(Proposal).offset(skip).limit(limit).all()
    return proposals

@router.get("/{proposal_id}", response_model=ProposalResponse)
def get_proposal(proposal_id: int, db: Session = Depends(get_db)):
    """Get a specific proposal by ID"""
    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
    
    if proposal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proposal with ID {proposal_id} not found"
        )
        
    return proposal

@router.put("/{proposal_id}", response_model=ProposalResponse)
def update_proposal(
    proposal_id: int, 
    proposal_update: ProposalUpdate, 
    db: Session = Depends(get_db)
):
    """Update an existing proposal"""
    db_proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
    
    if db_proposal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proposal with ID {proposal_id} not found"
        )
    
    # Update only the provided fields
    update_data = proposal_update.model_dump(exclude_unset=True)  # Updated for Pydantic v2
    for key, value in update_data.items():
        setattr(db_proposal, key, value)
    
    db.commit()
    db.refresh(db_proposal)
    
    return db_proposal

@router.delete("/{proposal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_proposal(proposal_id: int, db: Session = Depends(get_db)):
    """Delete a proposal"""
    db_proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
    
    if db_proposal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proposal with ID {proposal_id} not found"
        )
    
    db.delete(db_proposal)
    db.commit()
    
    return None
