from typing import Any, Dict, List
from pydantic import BaseModel, Field

class UserQuery(BaseModel):
    user_query: str  # The user's inquiry/question
    
# Define models
class QuestionnaireResponse(BaseModel):
    propertyType: str = Field(..., description="Type of property")
    occupants: str = Field(..., description="Number of people typically using hot water")
    currentHeating: str = Field(..., description="Current water heating system")
    waterUsage: str = Field(..., description="Description of hot water usage")
    roofSpace: str = Field(..., description="Available roof space in square meters")
    budget: str = Field(..., description="Estimated budget for the system")
    location: str = Field(..., description="Property location type (Urban, Rural, etc.)")
    sunlightHours: str = Field(..., description="Average daily sunlight hours")
    existingSystem: str = Field(..., description="Existing solar installations if any")
    timeline: str = Field(..., description="Timeline for installation")

class RecommendationResponse(BaseModel):
    recommended_systems: List[Dict[str, Any]] = Field(..., description="List of recommended solar hot water systems")
    reasoning: str = Field(..., description="Explanation for the recommendations")
    estimated_costs: Dict[str, Any] = Field(..., description="Estimated costs for each recommended system")
    estimated_savings: Dict[str, Any] = Field(..., description="Estimated annual savings and ROI")
    additional_considerations: List[str] = Field(..., description="Additional considerations for the customer")