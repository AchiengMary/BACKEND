from fastapi import HTTPException
import openai
from triaging.schemas import QuestionnaireResponse, RecommendationResponse
from typing import Any, Dict, List
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage
import json
import re
    
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
    
    
    # Construct the system prompt for AI with instructions for data extraction
    system_prompt = """
    You are an expert solar hot water system advisor for Davis & Shirtliff. Your task is to analyze customer requirements, extract information from product documents, and provide detailed, practical recommendations for solar hot water systems.
    
    First, carefully examine the raw product data from our database. For each product:
    1. Extract the system name, model, and type from the filename or text content
    2. Identify key specifications like tank capacity, collector type, and efficiency
    3. Note special features or technologies mentioned
    
    Then, analyze the customer requirements and provide recommendations based on:
    1. Daily hot water needs matching the ideal tank capacity
    2. Budget constraints and value proposition
    3. Available roof space for collector installation
    4. Sunlight hours in the customer's location
    5. Existing infrastructure compatibility
    
    Your recommendations should be:
    - Specific with exact model names and specifications
    - Supported by clear reasoning
    - Include cost estimates in Kenya Shillings (KSh)
    - Provide expected ROI and payback periods
    - Address installation considerations
    
    Your response should be professional, concise, and immediately actionable by sales engineers.
    """
    
    # Preserve raw Pinecone results but format as readable JSON string
    raw_results_str = json.dumps(pinecone_results, indent=2)
    
    # Construct the user prompt with analysis and raw Pinecone results
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
    3. Estimated costs breakdown (in KSh)
    4. Expected savings and ROI
    5. Additional considerations for this specific customer
    
    Strictly always format your response as a JSON object with these fields:
    - recommended_systems: array of objects with name, description, specifications
    - reasoning: string explaining your recommendations
    - estimated_costs: object with installation, system, and maintenance costs
    - estimated_savings: object with monthly savings, annual savings, and payback period
    - additional_considerations: array of strings with installation tips
    """
    
    # Create model instance with higher temperature for better extraction
    model = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0.2,  # Lower temperature for more factual responses
        max_output_tokens=2048  # Ensure enough tokens for complete response
    )
    
    # Generate AI response
    try:
        # Build messages list
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
            - estimated_costs: object with installation, system, and maintenance costs
            - estimated_savings: object with monthly savings, annual savings, and payback period
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
                    "estimated_costs": {
                        "system": "Contact Davis & Shirtliff for a quote",
                        "installation": "Varies based on complexity",
                        "total": "Contact Davis & Shirtliff for a quote"
                    },
                    "estimated_savings": {
                        "monthly": "Depends on current energy costs",
                        "annual": "Typically 60-70% of water heating costs",
                        "payback_period": "Typically 2-4 years"
                    },
                    "additional_considerations": [
                        "Contact a Davis & Shirtliff representative for detailed installation advice.",
                        "Professional installation is recommended for optimal performance."
                    ]
                }
        
        # Return structured response
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