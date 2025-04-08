from fastapi import HTTPException
import openai
from triaging.schemas import QuestionnaireResponse, RecommendationResponse
from typing import Any, Dict, List
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()

model = ChatGoogleGenerativeAI(model="gemini-1.5-flash")

# Helper function to process model response
def process_model_response(response):
    """Extracts the list of questions from the model's response."""
    try:
        
        # Extract the questions from the content, assuming they are separated by '\n'
        question_list = response.content.strip().split("\n")

        # Ensure we got exactly 5 questions
        if len(question_list) != 5:
            raise ValueError("The model did not return the expected number of questions.")
        
        return question_list
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing the model's response: {str(e)}")
    
def generate_ai_recommendations(analysis: Dict[str, Any], pinecone_results: List[Dict[str, Any]], data: QuestionnaireResponse) -> RecommendationResponse:
    """Generate detailed recommendations using Gemini model based on analysis and Pinecone results"""
    
    # Import required libraries
    from langchain.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import JsonOutputParser
    import json
    
    # Construct the system prompt for AI
    system_prompt = """
    You are an expert solar hot water system advisor for Davis & Shirtliff. Your task is to analyze customer requirements and provide detailed, practical recommendations for solar hot water systems.
    
    Follow these guidelines:
    1. Prioritize systems that match the customer's daily hot water needs and budget constraints
    2. Consider roof space availability and sunlight hours when recommending collector size
    3. Factor in location type (urban/rural) and existing infrastructure
    4. Provide clear reasoning for each recommendation
    5. Include practical installation considerations
    6. Format estimates in Kenya Shillings (KSh)
    7. Be specific about expected ROI and payback periods
    
    Your response should be professional, concise, and immediately actionable by sales engineers.
    """
    
    # Format pinecone results for the prompt - convert to a simple string representation
    formatted_results_str = json.dumps([
        {
            "system_name": item.get("metadata", {}).get("system_name", "Unknown System"),
            "source": item.get("metadata", {}).get("source", "Unknown"),
            "score": item.get("score", 0),
            "text": item.get("metadata", {}).get("text", "No description available")[:300] + "..."  # Truncate long texts
        } 
        for item in pinecone_results
    ], indent=2)
    
    # Construct the user prompt with analysis and Pinecone results
    user_prompt = f"""
    ## Customer Requirements:
    - Property Type: {data.propertyType}
    - Occupants: {data.occupants}
    - Current System: {data.currentHeating}
    - Water Usage: {data.waterUsage}
    - Roof Space: {data.roofSpace}
    - Budget: {data.budget}
    - Location: {data.location}
    - Sunlight Hours: {data.sunlightHours}
    - Existing Solar: {data.existingSystem}
    - Timeline: {data.timeline}
    
    ## Technical Analysis:
    - Estimated Daily Hot Water Need: {analysis['daily_hot_water_needed']} liters
    - Recommended Tank Capacity: {analysis['system_size_recommendation']['ideal_capacity_liters']:.0f} liters
    - Collector Area Needed: {analysis['system_size_recommendation']['collector_area_needed']:.1f} m²
    - Available Roof Space: {analysis['available_roof_space']} m²
    - Effective Sunlight: {analysis['effective_sunlight_hours']} hours
    
    ## Top Matching Systems from Database:
    {formatted_results_str}
    
    Based on this information, provide:
    1. Top 2-3 recommended systems with specific models from Davis & Shirtliff
    2. Clear reasoning for each recommendation
    3. Estimated costs breakdown
    4. Expected savings and ROI
    5. Additional considerations for this specific customer
    
    Format your response as structured JSON that can be directly parsed into a RecommendationResponse object with these fields:
    - recommended_systems (array of objects with name, description, specifications)
    - reasoning (string)
    - estimated_costs (object)
    - estimated_savings (object)
    - additional_considerations (array of strings)
    
    """
    
    # Define the output schema for structured parsing
    json_parser = JsonOutputParser()
    
    # Create prompt template - using simple string templates instead of variable interpolation
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", user_prompt)
    ])
    
    # Create chain with the Gemini model
    from langchain_google_genai import ChatGoogleGenerativeAI
    model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.3)
    
    # Generate AI response
    try:
        # Use a simple chain without variable interpolation
        result = model.invoke(user_prompt)
        
        # Parse the model response as JSON
        import re
        import json
        
        # Extract JSON content from the response
        response_text = result.content
        # Sometimes the model wraps the JSON in markdown code blocks, so we need to extract it
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response_text)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find anything that looks like JSON
            json_match = re.search(r'(\{[\s\S]*\})', response_text)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response_text
        
        try:
            parsed_json = json.loads(json_str)
        except json.JSONDecodeError:
            # If JSON parsing fails, create a basic structure with the full response as reasoning
            parsed_json = {
                "recommended_systems": [],
                "reasoning": response_text,
                "estimated_costs": {},
                "estimated_savings": {},
                "additional_considerations": ["Please check with a Davis & Shirtliff representative for more details."]
            }
        
        # Convert the parsed response to the expected format
        return RecommendationResponse(
            recommended_systems=parsed_json.get("recommended_systems", []),
            reasoning=parsed_json.get("reasoning", ""),
            estimated_costs=parsed_json.get("estimated_costs", {}),
            estimated_savings=parsed_json.get("estimated_savings", {}),
            additional_considerations=parsed_json.get("additional_considerations", [])
        )
        
    except Exception as e:
        import traceback
        error_detail = f"Error generating AI recommendations: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        raise HTTPException(status_code=500, detail=error_detail)
    
# def generate_ai_recommendations(analysis: Dict[str, Any], pinecone_results: List[Dict[str, Any]], data: QuestionnaireResponse) -> RecommendationResponse:
#     """Generate detailed recommendations using AI based on analysis and Pinecone results"""
    
#     # Construct the system prompt for AI
#     system_prompt = """
#     You are an expert solar hot water system advisor for Davis & Shirtliff. Your task is to analyze customer requirements and provide detailed, practical recommendations for solar hot water systems.
    
#     Follow these guidelines:
#     1. Prioritize systems that match the customer's daily hot water needs and budget constraints
#     2. Consider roof space availability and sunlight hours when recommending collector size
#     3. Factor in location type (urban/rural) and existing infrastructure
#     4. Provide clear reasoning for each recommendation
#     5. Include practical installation considerations
#     6. Format estimates in Kenya Shillings (KSh)
#     7. Be specific about expected ROI and payback periods
    
#     Your response should be professional, concise, and immediately actionable by sales engineers.
#     """
    
#     # Construct the user prompt with analysis and Pinecone results
#     user_prompt = f"""
#     ## Customer Requirements:
#     - Property Type: {data.propertyType}
#     - Occupants: {data.occupants}
#     - Current System: {data.currentHeating}
#     - Water Usage: {data.waterUsage}
#     - Roof Space: {data.roofSpace}
#     - Budget: {data.budget}
#     - Location: {data.location}
#     - Sunlight Hours: {data.sunlightHours}
#     - Existing Solar: {data.existingSystem}
#     - Timeline: {data.timeline}
    
#     ## Technical Analysis:
#     - Estimated Daily Hot Water Need: {analysis['daily_hot_water_needed']} liters
#     - Recommended Tank Capacity: {analysis['system_size_recommendation']['ideal_capacity_liters']:.0f} liters
#     - Collector Area Needed: {analysis['system_size_recommendation']['collector_area_needed']:.1f} m²
#     - Available Roof Space: {analysis['available_roof_space']} m²
#     - Effective Sunlight: {analysis['effective_sunlight_hours']} hours
    
#     ## Top Matching Systems from Database:
#     {[{
#         "system_name": match.metadata.get("system_name", "Unknown"),
#         "tank_capacity": match.metadata.get("tank_capacity", "Unknown"),
#         "collector_area": match.metadata.get("collector_area", "Unknown"),
#         "price_range": match.metadata.get("price_range", "Unknown"),
#         "features": match.metadata.get("features", []),
#         "score": match.score
#     } for match in pinecone_results]}
    
#     Based on this information, provide:
#     1. Top 2-3 recommended systems with specific models from Davis & Shirtliff
#     2. Clear reasoning for each recommendation
#     3. Estimated costs breakdown
#     4. Expected savings and ROI
#     5. Additional considerations for this specific customer
    
#     Format your response as structured data that can be directly parsed into a RecommendationResponse object.
#     """
    
#     # Generate AI response
#     try:
#         response = openai.chat.completions.create(
#             model="gpt-4-turbo",
#             messages=[
#                 {"role": "system", "content": system_prompt},
#                 {"role": "user", "content": user_prompt}
#             ],
#             temperature=0.3,
#             max_tokens=1500,
#             response_format={"type": "json_object"}
#         )
        
#         # Parse the AI-generated response 
#         ai_response = response.choices[0].message.content
#         print(f'AI Response: {ai_response}')
        
#         # Process the AI response into the expected format
#         # In a production environment, you'd want more robust parsing and validation
#         import json
#         parsed_response = json.loads(ai_response)
        
#         return RecommendationResponse(
#             recommended_systems=parsed_response.get("recommended_systems", []),
#             reasoning=parsed_response.get("reasoning", ""),
#             estimated_costs=parsed_response.get("estimated_costs", {}),
#             estimated_savings=parsed_response.get("estimated_savings", {}),
#             additional_considerations=parsed_response.get("additional_considerations", [])
#         )
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error generating AI recommendations: {str(e)}")

# #