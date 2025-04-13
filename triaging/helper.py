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
    Budget Range: {data.budget}
    Installation Location: {data.location}
    Roof Type: {data.existingSystem}
    Installation Timeline: {data.timeline}
    Water Source: {data.waterSource}
    Electricity Source: {data.electricitySource}
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
    # Extract number of occupants
    try:
        num_occupants = int(data.occupants)
    except ValueError:
        # Default fallback if parsing fails
        num_occupants = 4
    
    # Water consumption estimation (50 liters per person per day as specified)
    daily_usage = 50  # Fixed at 50 liters per person as specified in requirements
    total_daily_hot_water = num_occupants * daily_usage
    
    # Estimate roof area based on roof type and property type
    roof_area_estimates = {
        "Flat": {
            "Residential Home": 20,
            "Apartment Building": 50,
            "Commercial Business": 80,
            "Hotel/Resort": 100,
            "Other": 30
        },
        "Tiles": {
            "Residential Home": 15,
            "Apartment Building": 40,
            "Commercial Business": 60,
            "Hotel/Resort": 80,
            "Other": 25
        },
        "Pitched(Mabati)": {
            "Residential Home": 18,
            "Apartment Building": 45,
            "Commercial Business": 70,
            "Hotel/Resort": 90,
            "Other": 28
        },
        "Other": {
            "Residential Home": 15,
            "Apartment Building": 35,
            "Commercial Business": 55,
            "Hotel/Resort": 75,
            "Other": 20
        }
    }
    
    # Get roof area estimate based on roof type and property type
    roof_type = data.existingSystem
    property_type = data.propertyType
    
    if roof_type in roof_area_estimates and property_type in roof_area_estimates[roof_type]:
        available_roof = roof_area_estimates[roof_type][property_type]
    else:
        available_roof = 15  # Default fallback
    
    # Estimate sunlight hours based on location
    location_sunlight_map = {
        "Nairobi": 5.5,
        "Mombasa": 7,
        "Kisumu": 6.5,
        "Nakuru": 6,
        "Eldoret": 5.5,
        "Nyeri": 5,
        "Malindi": 7.5,
        "Kakamega": 6,
        "Garissa": 8,
        "Lamu": 7.5
    }
    
    # Extract location
    location = data.location.split(',')[0].strip() if ',' in data.location else data.location.strip()
    sunlight_hours = location_sunlight_map.get(location, 6)  # Default to 6 hours if location not found
    
    
    # Return analysis results
    return {
        "estimated_occupants": num_occupants,
        "daily_hot_water_needed": total_daily_hot_water,
        "available_roof_space": available_roof,
        "effective_sunlight_hours": sunlight_hours,
        "roof_type_needed": roof_type,
        "system_size_recommendation": {
            "min_capacity_liters": max(100, total_daily_hot_water * 0.8),
            "ideal_capacity_liters": total_daily_hot_water * 1.2
        },
        "water_source": data.waterSource,
        "electricity_source": data.electricitySource
    }