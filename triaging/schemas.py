from typing import Any, Dict, List
from pydantic import BaseModel, Field
from langchain.output_parsers import ResponseSchema, StructuredOutputParser

class UserQuery(BaseModel):
    user_query: str  # The user's inquiry/question
    
# Updated Pydantic model to match the new frontend
class QuestionnaireResponse(BaseModel):
    propertyType: str = Field(..., description="Type of property")
    occupants: str = Field(..., description="Number of people typically using hot water")
    # waterUsage: str = Field(..., description="Description of hot water usage")
    # floors: str = Field(..., description="Number of floors in the property")
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

class ExpansionParameters(BaseModel):
    selected_system: str = Field(..., description="Currently installed system from dropdown")
    current_capacity: float = Field(..., description="Current system capacity in litres")
    current_users: int = Field(..., description="Current number of users")
    location: str = Field(..., description="Installation location")
    target_capacity: float = Field(..., description="Target capacity needed in litres")

class SystemComponent(BaseModel):
    model: str = Field(..., description="Model name/number")
    capacity: float = Field(..., description="Capacity in litres")
    description: str = Field(..., description="Component description")
    
class ExpansionResponse(BaseModel):
    current_system: Dict[str, Any] = Field(..., description="Details of current system")
    additional_systems: List[SystemComponent] = Field(..., description="List of additional systems to be installed")
    total_new_capacity: float = Field(..., description="Total capacity after expansion")
    capacity_breakdown: Dict[str, float] = Field(..., description="Breakdown of capacity contribution from each component")
    reasoning: str = Field(..., description="Detailed reasoning for the recommended configuration")
    installation_notes: List[str] = Field(..., description="Specific installation and integration notes")
    considerations: List[str] = Field(..., description="Important considerations for this specific expansion")