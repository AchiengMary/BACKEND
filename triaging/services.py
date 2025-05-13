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
from triaging.data_table import solar_water_heaters

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
    - Recommended Tank Capacity: {int(analysis['system_size_recommendation']['ideal_capacity_liters'])} liters
    - Effective Sunlight: {analysis['effective_sunlight_hours']} hours
    
    ## Product names as they are in our ERP database:
    "ULTRASUN UFS150D FLATPLATE SOLAR HOT WATER SYSTEM": "DSD150",
    "ULTRASUN UFS150D SOLAR HOT WATER TANK": "DSD150/8",
    "ULTRASUN UFS200D FLATPLATE SOLAR HOT WATER SYSTEM": "DSD200",
    "ULTRASUN UFS200D SOLAR HOT WATER TANK": "DSD200/1",
    "ULTRASUN UFS300D FLATPLATE SOLAR HOT WATER SYSTEM": "DSD300",
    "ULTRASUN UFS300D SOLAR HOT WATER TANK": "DSD300/1",
    "ULTRASUN UFS150I INDIRECT SOLAR HOT WATER SYSTEM": "UFS150I",
    "ULTRASUN UFS150I INDIRECT SOLAR HOT WATER TANK": "UFS150I/1",
    "ULTRASUN UFS200DE DIRECT ENAMEL SOLAR HOT WATER SYSTEM": "UFS200DE",
    "ULTRASUN UFS200I INDIRECT SOLAR HOT WATER SYSTEM": "UFS200I",
    "ULTRASUN UFS200I SOLAR HOT WATER TANK": "UFS200I/1",
    "ULTRASUN UFS300DE DIRECT ENAMEL SOLAR HOT WATER SYSTEM": "UFS300DE",
    "ULTRASUN UFS300I INDIRECT SOLAR HOT WATER SYSTEM": "UFS300I",
    "BOX ULTRASUN UFS300D FLATPLATE SOLAR HOT WATER SYSTEM": "ZBOX10",
    "ULTRASUN UFX160D FLATPLATE SOLAR HOT WATER SYSTEM": "ESD 150",
    "ULTRASUN UFX160D TANK": "ESD150/1",
    "ULTRASUN UFX200D FLATPLATE SOLAR HOT WATER SYSTEM": "ESD200",
    "ULTRASUN UFX160I HOT WATER TANK": "ESD200/2",
    "ULTRASUN UFX300D FLATPLATE SOLAR HOT WATER SYSTEM": "ESD300",
    "ULTRASUN UFX300D TANK": "ESD300A",
    "ULTRASUN UFX160I FLATPLATE SOLAR HOT WATER SYSTEM": "ESI150",
    "ULTRASUN UFX200I FLATPLATE SOLAR HOT WATER SYSTEM": "ESI200",
    "ULTRASUN UFX200I HOT WATER TANK": "ESI200/2",
    "ULTRASUN UFX300I FLATPLATE SOLAR HOT WATER SYSTEM": "ESI300",
    "ULTRASUN UFX300I HOT WATER TANK": "ESI300A",
    "ULTRASUN UVT200 VACTUBE SOLAR HOT WATER SYSTEM": "DVS200",
    "ULTRASUN UVT300 VACTUBE SOLAR HOT WATER SYSTEM": "DVS300",
    "ULTRASUN UVT300 VACTUBE SOLAR HOT WATER TANK": "DVS300 / 1",
    "ULTRASUN UVR150 VACROD SOLAR HOT WATER SYSTEM": "DSH150",
    "ULTRASUN UVR150 VACROD SOLAR HOT WATER": "DSH150/2",
    "ULTRASUN UVR200 VACROD SOLAR HOT WATER SYSTEM": "DSH200",
    "ULTRASUN UVR200 SOLAR HOT WATER TANK": "DSH200/1",
    "ULTRASUN UVR300 VACROD SOLAR HOT WATER SYSTEM": "DSH300",
    "DAYLIFF HPW 80LITRES ALL-IN-ONE VERTICAL WALL MOUNT HEAT PUMP": "HPW080",
    "DAYLIFF HPW 120LITRES ALL-IN-ONE HEAT PUMP": "HPW120",
    "DAYLIFF HPW 150LITRES ALL-IN-ONE HEAT PUMP": "HPW150",
    "DAYLIFF HPW 200LITRES ALL-IN-ONE HEAT PUMP": "HPW200",
    "DAYLIFF HPW 300LITRES ALL-IN-ONE HEAT PUMP": "HPW300",
    "ULTRASUN CWS1000 SOLAR HOT WATER SYSTEM": "EST1000",
    "ULTRASUN CWS1500 SOLAR HOT WATER SYSTEM": "EST1500",
    "ULTRASUN CWS2000 SOLAR HOT WATER SYSTEM": "EST2000",
    "ULTRASUN CWS2000L SOLAR HOT WATER TANK": "EST2000/1"
    
    ## Raw Product Data from pinecone Database:

    {raw_results_str}
    
    Based on the customer requirements and technical analysis, provide ONE primary recommended system and TWO alternative options.
    
    For EACH system recommendation:
    1. Use EXACTLY the system name as it appears in the ERP database (e.g., "ULTRASUN UFS300D FLATPLATE SOLAR HOT WATER SYSTEM", "DAYLIFF HPW 300LITRES ALL-IN-ONE HEAT PUMP", "ULTRASUN CWS1500 SOLAR HOT WATER SYSTEM", "ULTRASUN UFS150I INDIRECT SOLAR HOT WATER TANK") 
    2. Include the exact model number (e.g., "DSD300")
    3. Always provide these key specifications:
       - Tank Size (in Liters)
       - Collector Type (Flatplate, Vacuum Tube, etc.)
       - Heat Output (kWh/day) when possible
       - Suitable For (number of people the system can serve)
    4. Include a brief description (2-3 sentences) highlighting key benefits
    
    IMPORTANT RULES:
    - When water source is "borehole", ALWAYS recommend an indirect system (marked with "I" in model names)
    - Match the tank capacity as closely as possible to the recommended capacity from technical analysis
    - The primary recommendation should be the closest match to the ideal specifications
    - Alternative options should offer different capacity/technology options that still meet basic requirements
    - Do NOT include pricing information in the recommendations
    - Do NOT include a system configuration diagram
    
    Also include:
    - Water Quality Requirements section with 2-4 relevant parameters (like TDS, hardness, pH, etc.)
    - Additional Components section with 2-3 required accessories (controller, heater fluid, backup heater, etc.)
    - Technical Specifications section with key performance metrics
    - Installation Notes with 2-3 practical tips
    - Warranty information
    
    Format your response as a JSON object with these specific fields (do NOT include any comments in the JSON):
    ```json
    {{
      "primary_recommendation": {{
        "name": "EXACT SYSTEM NAME",
        "model": "MODEL NUMBER",
        "description": "Brief description of benefits and features",
        "specifications": {{
          "tank_size": "XXX Liters",
          "collector_type": "Type of collector",
          "heat_output": "XX kWh/day (max)",
          "suitable_for": "Up to X people"
        }}
      }},
      "alternative_options": [
        {{
          "name": "EXACT SYSTEM NAME",
          "model": "MODEL NUMBER", 
          "description": "Brief description",
          "specifications": {{
            "tank_size": "XXX Liters",
            "collector_type": "Type of collector"
          }},
          "price_category": "High/Medium/Low"
        }},
        {{
          "name": "EXACT SYSTEM NAME",
          "model": "MODEL NUMBER",
          "description": "Brief description",
          "specifications": {{
            "tank_size": "XXX Liters",
            "collector_type": "Type of collector"
          }},
          "price_category": "High/Medium/Low"
        }}
      ],
      "water_quality_requirements": [
        {{"parameter": "Parameter name", "value": "Recommended value"}},
        {{"parameter": "Parameter name", "value": "Recommended value"}},
        {{"parameter": "Parameter name", "value": "Recommended value"}},
        {{"parameter": "Parameter name", "value": "Recommended value"}}
      ],
      "additional_components": [
        {{
          "name": "Component name",
          "description": "Brief description of purpose"
        }},
        {{
          "name": "Component name",
          "description": "Brief description of purpose"
        }},
        {{
          "name": "Component name",
          "description": "Brief description of purpose"
        }}
      ],
      "technical_specifications": [
        {{"parameter": "Parameter name", "value": "Value"}},
        {{"parameter": "Parameter name", "value": "Value"}},
        {{"parameter": "Parameter name", "value": "Value"}}
      ],
      "installation_notes": [
        "Installation tip 1",
        "Installation tip 2",
        "Installation tip 3"
      ],
      "warranty": {{
        "tank": "X years",
        "collector": "X years",
        "parts": "X years"
      }}
    }}
    ```
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
            
            # Map the parsed JSON to our response model
            recommended_systems = []
            
            # Add primary recommendation
            if "primary_recommendation" in parsed_json:
                primary = parsed_json["primary_recommendation"]
                recommended_systems.append({
                    "name": primary["name"],
                    "model": primary["model"],
                    "description": primary["description"],
                    "is_primary": True,
                    "specifications": primary["specifications"]
                })
            
            # Add alternative options
            if "alternative_options" in parsed_json:
                for alt in parsed_json["alternative_options"]:
                    recommended_systems.append({
                        "name": alt["name"],
                        "model": alt["model"],
                        "description": alt["description"],
                        "is_primary": False,
                        "specifications": alt["specifications"],
                        "price_category": alt.get("price_category", "")
                    })
            
            # Extract other details for the response
            water_quality = parsed_json.get("water_quality_requirements", [])
            additional_components = parsed_json.get("additional_components", [])
            technical_specs = parsed_json.get("technical_specifications", [])
            installation_notes = parsed_json.get("installation_notes", [])
            warranty = parsed_json.get("warranty", {})
            
            # Map product names to ERP IDs
            solar_water_heaters = {
                "ULTRASUN UFS150D FLATPLATE SOLAR HOT WATER SYSTEM": "DSD150",
                "ULTRASUN UFS200D FLATPLATE SOLAR HOT WATER SYSTEM": "DSD200",
                "ULTRASUN UFS300D FLATPLATE SOLAR HOT WATER SYSTEM": "DSD300",
                "ULTRASUN UFS150I INDIRECT SOLAR HOT WATER SYSTEM": "UFS150I",
                "ULTRASUN UFS200DE DIRECT ENAMEL SOLAR HOT WATER SYSTEM": "UFS200DE",
                "ULTRASUN UFS200I INDIRECT SOLAR HOT WATER SYSTEM": "UFS200I",
                "ULTRASUN UFS300DE DIRECT ENAMEL SOLAR HOT WATER SYSTEM": "UFS300DE",
                "ULTRASUN UFS300I INDIRECT SOLAR HOT WATER SYSTEM": "UFS300I",
                "ULTRASUN UFX160D FLATPLATE SOLAR HOT WATER SYSTEM": "ESD 150",
                "ULTRASUN UFX200D FLATPLATE SOLAR HOT WATER SYSTEM": "ESD200",
                "ULTRASUN UFX300D FLATPLATE SOLAR HOT WATER SYSTEM": "ESD300",
                "ULTRASUN UFX160I FLATPLATE SOLAR HOT WATER SYSTEM": "ESI150",
                "ULTRASUN UFX200I FLATPLATE SOLAR HOT WATER SYSTEM": "ESI200",
                "ULTRASUN UFX300I FLATPLATE SOLAR HOT WATER SYSTEM": "ESI300",
                "ULTRASUN UVT200 VACTUBE SOLAR HOT WATER SYSTEM": "DVS200",
                "ULTRASUN UVT300 VACTUBE SOLAR HOT WATER SYSTEM": "DVS300",
                "ULTRASUN UVR150 VACROD SOLAR HOT WATER SYSTEM": "DSH150",
                "ULTRASUN UVR200 VACROD SOLAR HOT WATER SYSTEM": "DSH200",
                "ULTRASUN UVR300 VACROD SOLAR HOT WATER SYSTEM": "DSH300",
                "DAYLIFF HPW 80LITRES ALL-IN-ONE VERTICAL WALL MOUNT HEAT PUMP": "HPW080",
                "DAYLIFF HPW 120LITRES ALL-IN-ONE HEAT PUMP": "HPW120",
                "DAYLIFF HPW 150LITRES ALL-IN-ONE HEAT PUMP": "HPW150",
                "DAYLIFF HPW 200LITRES ALL-IN-ONE HEAT PUMP": "HPW200",
                "DAYLIFF HPW 300LITRES ALL-IN-ONE HEAT PUMP": "HPW300",
                "ULTRASUN CWS1000 SOLAR HOT WATER SYSTEM": "EST1000",
                "ULTRASUN CWS1500 SOLAR HOT WATER SYSTEM": "EST1500",
                "ULTRASUN CWS2000 SOLAR HOT WATER SYSTEM": "EST2000"
            }
            
            # Extract all product names for validation
            recommended_names = [system["name"] for system in recommended_systems]
            
            # Check if recommended products exist in the mapping
            invalid_names = [name for name in recommended_names if name not in solar_water_heaters]
            if invalid_names:
                print(f"Warning: Some recommended products not found in ERP database: {invalid_names}")
            
            # Return structured response
            return RecommendationResponse(
                recommended_systems=recommended_systems,
                water_quality_requirements=water_quality,
                additional_components=additional_components,
                technical_specifications=technical_specs,
                installation_notes=installation_notes,
                warranty=warranty
            )
            
        except (json.JSONDecodeError, AttributeError) as json_err:
            print(f"JSON parsing error: {str(json_err)}")
            print(f"Raw response: {response_text}")
            
            # If JSON parsing fails, try to extract structured information using the model again
            extraction_prompt = f"""
            I couldn't parse your previous response as valid JSON. Please format your recommendations as valid JSON with these fields:
            - primary_recommendation: object with name, model, description, specifications
            - alternative_options: array of objects with name, model, description, specifications
            - water_quality_requirements: array of objects with parameter and value
            - additional_components: array of objects with name and description
            - technical_specifications: array of objects with parameter and value
            - installation_notes: array of strings
            - warranty: object with tank, collector, parts values
            
            Please provide ONLY the JSON response without any explanation or code blocks.
            """
            
            try:
                retry_result = model.invoke([
                    {"role": "system", "content": "You are a helpful assistant. Format your response as valid JSON."},
                    {"role": "user", "content": extraction_prompt}
                ])
                
                retry_response = retry_result.content
                parsed_json = json.loads(retry_response)
                
                # Process the parsed JSON (same as above)
                recommended_systems = []
                
                # Add primary recommendation
                if "primary_recommendation" in parsed_json:
                    primary = parsed_json["primary_recommendation"]
                    recommended_systems.append({
                        "name": primary["name"],
                        "model": primary["model"],
                        "description": primary["description"],
                        "is_primary": True,
                        "specifications": primary["specifications"]
                    })
                
                # Add alternative options
                if "alternative_options" in parsed_json:
                    for alt in parsed_json["alternative_options"]:
                        recommended_systems.append({
                            "name": alt["name"],
                            "model": alt["model"],
                            "description": alt["description"],
                            "is_primary": False,
                            "specifications": alt["specifications"],
                            "price_category": alt.get("price_category", "")
                        })
                
                # Extract other details for the response
                water_quality = parsed_json.get("water_quality_requirements", [])
                additional_components = parsed_json.get("additional_components", [])
                technical_specs = parsed_json.get("technical_specifications", [])
                installation_notes = parsed_json.get("installation_notes", [])
                warranty = parsed_json.get("warranty", {})
                
                return RecommendationResponse(
                    recommended_systems=recommended_systems,
                    water_quality_requirements=water_quality,
                    additional_components=additional_components,
                    technical_specifications=technical_specs,
                    installation_notes=installation_notes,
                    warranty=warranty
                )
                
            except Exception as retry_err:
                print(f"Retry failed: {str(retry_err)}")
                
                # Final fallback: create structured response manually
                return RecommendationResponse(
                    recommended_systems=[
                        {
                            "name": "ULTRASUN UFS200D FLATPLATE SOLAR HOT WATER SYSTEM",
                            "model": "DSD200",
                            "description": "Dayliff Ultrasun UFS Flat Plate Solar Hot Water Systems are efficient and economical water heaters that provide excellent performance in all domestic applications.",
                            "is_primary": True,
                            "specifications": {
                                "tank_size": f"{int(analysis['system_size_recommendation']['ideal_capacity_liters'])} Liters",
                                "collector_type": "Flatplate",
                                "heat_output": "13 kWh/day (max)",
                                "suitable_for": f"Up to {max(1, min(8, int(float(analysis['system_size_recommendation']['ideal_capacity_liters']) / 30)))} people"
                            }
                        },
                        {
                            "name": "ULTRASUN UFS300D FLATPLATE SOLAR HOT WATER SYSTEM",
                            "model": "DSD300",
                            "description": "Higher capacity system ideal for larger households with greater hot water demands.",
                            "is_primary": False,
                            "specifications": {
                                "tank_size": "300 Liters",
                                "collector_type": "Flatplate"
                            },
                            "price_category": "Medium"
                        },
                        {
                            "name": "ULTRASUN UVT200 VACTUBE SOLAR HOT WATER SYSTEM",
                            "model": "DVS200",
                            "description": "Vacuum tube technology for enhanced efficiency, especially in areas with less direct sunlight.",
                            "is_primary": False,
                            "specifications": {
                                "tank_size": "200 Liters",
                                "collector_type": "Vacuum Tube"
                            },
                            "price_category": "High"
                        }
                    ],
                    water_quality_requirements=[
                        {"parameter": "TDS", "value": "<1500mg/l"},
                        {"parameter": "Hardness", "value": "<400mg/l CaCO3"},
                        {"parameter": "Saturation Index", "value": ">0.8<1.0"}
                    ],
                    additional_components=[
                        {
                            "name": "SOLAR THERMAL SR609 AC CONTROLLER",
                            "description": "Programmable temperature controller that automatically switches ON/OFF the electric booster heaters at certain pre-programmed times."
                        },
                        {
                            "name": "SOLAR HOT WATER HEATER FLUID 20L",
                            "description": "Heat transfer fluid for indirect solar hot water systems."
                        },
                        {
                            "name": "HEATER 3KW RURAL",
                            "description": "Electric heating element for temperature boosting during cloudy days."
                        }
                    ],
                    technical_specifications=[
                        {"parameter": "Maximum Heating Output", "value": "Based on average irradiation levels of 6000W/m²/day prevailing in September - March"},
                        {"parameter": "Minimum Heating Output", "value": "Based on average irradiation levels of 4000W/m²/day prevailing in June/July"},
                        {"parameter": "Operating Pressure", "value": "4 bar"}
                    ],
                    installation_notes=[
                        "Professional installation recommended for optimal performance",
                        "South-facing installation provides optimal sunlight exposure",
                        "System must be installed with proper safety valves and pressure relief"
                    ],
                    warranty={
                        "tank": "5 years",
                        "collector": "10 years",
                        "parts": "1 year"
                    }
                )
        
    except Exception as e:
        import traceback
        error_detail = f"Error generating AI recommendations: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        raise HTTPException(status_code=500, detail=error_detail)
