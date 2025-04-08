from typing import Any, Dict, List
from pydantic import BaseModel, Field

class UserQuery(BaseModel):
    user_query: str  # The user's inquiry/question
    
# Updated Pydantic model to match the new frontend
class QuestionnaireResponse(BaseModel):
    propertyType: str = Field(..., description="Type of property")
    occupants: str = Field(..., description="Number of people typically using hot water")
    waterUsage: str = Field(..., description="Description of hot water usage")
    floors: str = Field(..., description="Number of floors in the property")
    budget: str = Field(..., description="Estimated budget for the system")
    location: str = Field(..., description="Property location for installation")
    existingSystem: str = Field(..., description="Type of roof the property has")
    timeline: str = Field(..., description="Timeline for installation")
    waterSource: str = Field(..., description="Main source of water")
    electricitySource: str = Field(..., description="Primary source of electricity")

class RecommendationResponse(BaseModel):
    recommended_systems: List[Dict[str, Any]] = Field(..., description="List of recommended solar hot water systems")
    reasoning: str = Field(..., description="Explanation for the recommendations")
    additional_considerations: List[str] = Field(..., description="Additional considerations for the customer")