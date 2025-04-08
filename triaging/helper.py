import os
from typing import Any, Dict, List
from langchain_openai  import OpenAIEmbeddings
from fastapi import HTTPException
from triaging.schemas import QuestionnaireResponse
from pinecone import Pinecone
from langchain_community.vectorstores import Pinecone as LangchainPinecone
from langchain_google_genai import GoogleGenerativeAIEmbeddings

index_name = "davisandshirliff"

# Initialize Pinecone with the current SDK
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# Connect to the existing index
index = pc.Index(index_name)

# embeddings = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"))
def download_openai_embeddings():

    """Downloads and returns OpenAI embeddings."""

    embeddings = OpenAIEmbeddings()

    return embeddings



embeddings = download_openai_embeddings()
# def download_google_embeddings():
#     """Downloads and returns Google embeddings."""
    
    
#     embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
#     return embeddings


# # Initialize embeddings model
# embeddings = download_google_embeddings()

# Generate embeddings for a text
def generate_embeddings(text):
    """Generate embeddings for the input text using Google's embedding model"""
    try:
        vector = embeddings.embed_query(text)
        return vector
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating embeddings: {str(e)}")


def generate_prompt_from_questionnaire(data: QuestionnaireResponse) -> str:
    """Convert questionnaire data to a structured prompt for embedding"""
    return f"""
    Property Type: {data.propertyType}
    Number of Occupants: {data.occupants}
    Current Heating System: {data.currentHeating}
    Water Usage Pattern: {data.waterUsage}
    Available Roof Space: {data.roofSpace}
    Budget Range: {data.budget}
    Location Type: {data.location}
    Daily Sunlight Hours: {data.sunlightHours}
    Existing Solar System: {data.existingSystem}
    Installation Timeline: {data.timeline}
    """

def get_recommendations_from_pinecone(vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
    """Query Pinecone for the most similar systems based on the embedding vector"""
    try:
        
        # Query the index
        query_response = index.query(
            vector=vector,
            top_k=top_k,
            include_metadata=True
        )
        
        # Process and return results
        return [
            {
                "id": match.id,
                "score": match.score,
                "metadata": match.metadata
            } for match in query_response.matches
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying Pinecone: {str(e)}")



def analyze_requirements(data: QuestionnaireResponse) -> Dict[str, Any]:
    """Analyze the requirements based on questionnaire data"""
    # Extract numerical values from string ranges
    occupants_map = {
        "1-2": 2, "3-4": 4, "5-6": 6, "7-10": 10, "10+": 15
    }
    
    roof_space_map = {
        "<5": 4, "5-10": 7.5, "10-20": 15, "20-50": 35, "50+": 60
    }
    
    sunlight_map = {
        "<3 hours": 2, "3-5 hours": 4, "5-7 hours": 6, "7+ hours": 8
    }
    
    # Water consumption estimation (liters per person per day)
    water_usage_per_person = {
        "Light (mostly showers)": 30,
        "Moderate (showers + appliances)": 50,
        "Heavy (multiple baths daily)": 80,
        "Commercial use": 100
    }
    
    # Estimate daily hot water requirement
    num_occupants = occupants_map.get(data.occupants, 4)
    daily_usage = water_usage_per_person.get(data.waterUsage, 50)
    total_daily_hot_water = num_occupants * daily_usage
    
    # Estimate system size based on available roof space and daily requirement
    available_roof = roof_space_map.get(data.roofSpace, 15)
    sunlight_hours = sunlight_map.get(data.sunlightHours, 5)
    
    # Return analysis results
    return {
        "estimated_occupants": num_occupants,
        "daily_hot_water_needed": total_daily_hot_water,
        "available_roof_space": available_roof,
        "effective_sunlight_hours": sunlight_hours,
        "system_size_recommendation": {
            "min_capacity_liters": max(100, total_daily_hot_water * 0.8),
            "ideal_capacity_liters": total_daily_hot_water * 1.2,
            "collector_area_needed": total_daily_hot_water / (40 * sunlight_hours)  # Rough estimate
        }
    }