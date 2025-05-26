from fastapi import APIRouter
from customer_proposal.services.proposals import router as proposals_router

# Initialize the main API router
api_router = APIRouter()

# Include routers from different endpoints
api_router.include_router(
    proposals_router,
    prefix="/proposals",
    tags=["proposals"]
)
