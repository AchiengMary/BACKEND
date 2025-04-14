import os
import re
from typing import Any, Dict, List
from langchain_openai  import OpenAIEmbeddings
from fastapi import HTTPException
from triaging.schemas import QuestionnaireResponse
from pinecone import Pinecone
from langchain_community.vectorstores import Pinecone as LangchainPinecone
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

index_name = "davisandshirliff"

# Initialize Pinecone with the current SDK
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# Connect to the existing index
index = pc.Index(index_name)

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro-latest",
    temperature=0.7,
    convert_system_message_to_human=True
)

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
    
async def extract_questionnaire_data_with_ai(data: Dict[str, str]) -> QuestionnaireResponse:
    """Use AI to extract structured information from questionnaire data"""
    try:
        # Convert questionnaire data to formatted text
        questionnaire_text = ""
        for question, answer in data.items():
            questionnaire_text += f"Question: {question}\nAnswer: {answer}\n\n"
        
        # Define the output schema for structured extraction
        response_schemas = [
            ResponseSchema(name="propertyType", 
                           description="Type of property (Residential Home, Apartment Building, Commercial Business, Hotel/Resort, or Other)"),
            ResponseSchema(name="occupants", 
                           description="Number of people typically using hot water (as a string)"),
            ResponseSchema(name="budget", 
                           description="Estimated budget for the system (as a string)"),
            ResponseSchema(name="location", 
                           description="Property location for installation (city name)"),
            ResponseSchema(name="existingSystem", 
                           description="Type of roof the property has (Flat, Tiles, Pitched(Mabati), or Other)"),
            ResponseSchema(name="timeline", 
                           description="Timeline for installation"),
            ResponseSchema(name="waterSource", 
                           description="Main source of water (Municipal, Borehole, Rainwater, or Surface water)"),
            ResponseSchema(name="electricitySource", 
                           description="Primary source of electricity (Grid, Solar, Generator, or None)")
        ]
        
        # Create output parser
        output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
        format_instructions = output_parser.get_format_instructions()
        
        # Create prompt template
        template = """
        You are an expert system that extracts structured information from questionnaire responses about solar water heating systems.
        
        Please analyze the following questions and answers, and extract the required information for a solar water heating system recommendation.
        
        {questionnaire}
        
        Based on these questions and answers, please extract the following information:
        
        {format_instructions}
        
        If any information is missing, make reasonable assumptions based on the available data:
        - For property type, assume "Residential Home" if not specified
        - For occupants, infer from water usage (50L per person) or assume 4 if not specified
        - For location, assume "Nairobi" if not specified
        - For water source, assume "Municipal" if not specified
        - For electricity source, assume "Grid" if not specified
        
        When inferring roof type:
        - "tiled" or "tiles" maps to "Tiles"
        - "corrugated iron", "mabati", or "iron sheets" maps to "Pitched(Mabati)"
        - "flat", "concrete", or "flat concrete" maps to "Flat"
        - Any other roof type maps to "Other"
        
        OUTPUT:
        """
        
        # Create the prompt with the questionnaire data
        prompt = PromptTemplate(
            template=template,
            input_variables=["questionnaire"],
            partial_variables={"format_instructions": format_instructions}
        )
        
        # Generate the structured extraction
        _input = prompt.format(questionnaire=questionnaire_text)
        response = llm.invoke(_input)
        
        # Parse the response
        extracted_data = output_parser.parse(response)
        
        # Convert to QuestionnaireResponse
        return QuestionnaireResponse(
            propertyType=extracted_data["propertyType"],
            occupants=extracted_data["occupants"],
            budget=extracted_data["budget"],
            location=extracted_data["location"],
            existingSystem=extracted_data["existingSystem"],
            timeline=extracted_data["timeline"],
            waterSource=extracted_data["waterSource"],
            electricitySource=extracted_data["electricitySource"]
        )
        
    except Exception as e:
        # If AI extraction fails, fall back to a simpler method
        print(f"AI extraction failed: {str(e)}")
        return fallback_extraction(data)
    
def fallback_extraction(data: Dict[str, str]) -> QuestionnaireResponse:
    """Fallback method to extract information if AI extraction fails"""
    # Default values
    property_type = "Residential Home"
    occupants = "4"
    budget = "0"
    location = "Nairobi"
    roof_type = "Other"
    timeline = "Within 1 month"
    water_source = "Municipal"
    electricity_source = "Grid"
    
    # Basic extraction based on keywords
    for question, answer in data.items():
        question_lower = question.lower()
        answer_lower = answer.lower() if answer else ""
        
        # Extract roof type
        if "roof" in question_lower:
            if "tile" in answer_lower:
                roof_type = "Tiles"
            elif "corrugated" in answer_lower or "iron" in answer_lower or "mabati" in answer_lower:
                roof_type = "Pitched(Mabati)"
            elif "flat" in answer_lower or "concrete" in answer_lower:
                roof_type = "Flat"
        
        # Extract budget
        if "budget" in question_lower:
            budget_match = re.search(r'\d+', answer)
            if budget_match:
                budget = budget_match.group(0)
        
        # Extract timeline
        if "when" in question_lower or "timeline" in question_lower or "installed" in question_lower:
            timeline = answer if answer else timeline
        
        # Extract water usage to estimate occupants
        if "usage" in question_lower and "water" in question_lower:
            try:
                usage = int(re.search(r'\d+', answer).group(0))
                # Assuming 50L per person per day
                estimated_occupants = max(1, round(usage / 50))
                occupants = str(estimated_occupants)
            except (ValueError, AttributeError):
                pass
    
    # Create QuestionnaireResponse with extracted data
    return QuestionnaireResponse(
        propertyType=property_type,
        occupants=occupants,
        budget=budget,
        location=location,
        existingSystem=roof_type,
        timeline=timeline,
        waterSource=water_source,
        electricitySource=electricity_source
    )