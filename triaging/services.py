from fastapi import HTTPException
import openai
from triaging.schemas import QuestionnaireResponse, RecommendationResponse
from typing import Any, Dict, List
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage
import json
import re
from triaging.prompt import system_prompt

load_dotenv()

   
# Create model instance with higher temperature for better extraction
model = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0.2,  # Lower temperature for more factual responses
        max_output_tokens=2048  # Ensure enough tokens for complete response
    )

# Helper function to process model response
def process_model_response(response):
    """Extracts the list of questions from the model's response."""
    try:
        # # Extract the questions from the content, assuming they are separated by '\n'
        # question_list = response.content.strip().split("\n")
        # Handle both string and object responses
        if isinstance(response, str):
            # For string responses (from Gemini)
            question_list = response.strip().split("\n")
        else:
            # For object responses (from OpenAI)
            question_list = response.content.strip().split("\n")

        # Ensure we got exactly 5 questions
        if len(question_list) != 5:
            raise ValueError("The model did not return the expected number of questions.")
        
        return question_list
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing the model's response: {str(e)}")
    
    
def generate_ai_recommendations(analysis: Dict[str, Any], pinecone_results: List[Dict[str, Any]], data: QuestionnaireResponse) -> RecommendationResponse:
    """Generate detailed recommendations using AI model based on analysis and Pinecone results"""
    
    # Preserve raw Pinecone results but format as readable JSON string
    raw_results_str = json.dumps(pinecone_results, indent=2)
    
    # Construct the user prompt with analysis and raw Pinecone results
    user_prompt = f"""
    ## Customer Requirements:

    - Property Type: {data.propertyType}
    - Occupants: {data.occupants}
    - Budget: {data.budget}
    - Location: {data.location}
    - Roof Type: {data.existingSystem}
    - Timeline: {data.timeline}
    - Water Source: {data.waterSource}
    - Electricity Source: {data.electricitySource}
    
    ## Technical Analysis:

    - Estimated Daily Hot Water Need: {analysis['daily_hot_water_needed']} liters
    - Roof type needed is: {analysis['roof_type_needed']}
    - Recommended Tank Capacity: {analysis['system_size_recommendation']['ideal_capacity_liters']:.0f} liters
    - Effective Sunlight: {analysis['effective_sunlight_hours']} hours
    
    ## Raw Product Data from Database:

    {raw_results_str}
    
    First, extract and organize the key information from each product in the raw data. For each product:
    1. Identify the system name/model (e.g., "Dayliff CSW", "Ultrasun UFS", "Ultrasun UVR", etc.)
    2. Determine the collector type (flatplate, vacuum tube, pumped circulation, etc.)
    3. Extract capacity information if available
    4. Note key features and specifications
    
    Then, analyze which systems best match the customer requirements and provide:
    1. Top 2-3 recommended systems with specific models from Davis & Shirtliff
    2. Clear reasoning for each recommendation
    3. Additional considerations for this specific customer
    
    Strictly always format your response as a JSON object with these fields:
    - recommended_systems: array of objects with name, description, specifications
    - reasoning: string explaining your recommendations
    - additional_considerations: array of strings with installation tips
    """
    
    # Generate AI response
    try:
        # Assuming your model variable is defined elsewhere
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Direct invocation
        result = model.invoke(messages)
        
        # Extract response content
        response_text = result.content
        
        # Try to parse JSON from the response
        try:
            # First try: look for JSON block in markdown
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
            if json_match:
                json_str = json_match.group(1)
                parsed_json = json.loads(json_str)
            else:
                # Second try: look for anything that looks like JSON object
                json_match = re.search(r'(\{[\s\S]*\})', response_text)
                if json_match:
                    json_str = json_match.group(1)
                    parsed_json = json.loads(json_str)
                else:
                    # Last resort: try to parse the entire response as JSON
                    parsed_json = json.loads(response_text)
            
        except (json.JSONDecodeError, AttributeError) as json_err:
            print(f"JSON parsing error: {str(json_err)}")
            print(f"Raw response: {response_text}")
            
            # If JSON parsing fails, try to extract structured information using the model again
            extraction_prompt = f"""
            I couldn't parse your previous response as valid JSON. Please format your recommendations as valid JSON with these fields:
            - recommended_systems: array of objects with name, description, specifications
            - reasoning: string explaining your recommendations
            - additional_considerations: array of strings with installation tips
            
            Please provide ONLY the JSON response without any explanation or code blocks.
            """
            
            try:
                retry_result = model.invoke([
                    {"role": "system", "content": "You are a helpful assistant. Format your response as valid JSON."},
                    {"role": "user", "content": extraction_prompt}
                ])
                
                retry_response = retry_result.content
                parsed_json = json.loads(retry_response)
                
            except Exception as retry_err:
                print(f"Retry failed: {str(retry_err)}")
                
                # Final fallback: create structured response manually
                parsed_json = {
                    "recommended_systems": [
                        {
                            "name": "Solar Water Heating System",
                            "description": "Based on your requirements, this system is suitable for your needs.",
                            "specifications": {
                                "capacity": f"{analysis['system_size_recommendation']['ideal_capacity_liters']:.0f} liters",
                                "collector_area": f"{analysis['system_size_recommendation']['collector_area_needed']:.1f} m²"
                            }
                        }
                    ],
                    "reasoning": "The recommendation is based on your daily hot water needs and available roof space.",
                    "additional_considerations": [
                        "Contact a Davis & Shirtliff representative for detailed installation advice.",
                        "Professional installation is recommended for optimal performance."
                    ]
                }
        
        # Return structured response
        return RecommendationResponse(
            recommended_systems=parsed_json.get("recommended_systems", []),
            reasoning=parsed_json.get("reasoning", ""),
            additional_considerations=parsed_json.get("additional_considerations", [])
        )
        
    except Exception as e:
        import traceback
        error_detail = f"Error generating AI recommendations: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        raise HTTPException(status_code=500, detail=error_detail)