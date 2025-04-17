import asyncio
from typing import Dict
from fastapi import APIRouter, HTTPException, Query,status,Depends, Body
from langchain.chains import LLMChain
from langchain_google_genai import ChatGoogleGenerativeAI
from triaging.schemas import UserQuery, QuestionnaireResponse, RecommendationResponse, ExpansionParameters, ExpansionResponse, SystemComponent
from triaging.prompt import get_triaging_prompt_template
from dotenv import load_dotenv
from openai import OpenAI
from langchain_openai import ChatOpenAI
from triaging.services import process_model_response, generate_ai_recommendations
from triaging.helper import generate_prompt_from_questionnaire, generate_embeddings, get_recommendations_from_pinecone, analyze_requirements, extract_questionnaire_data_with_ai
# import google.generativeai as genai
import os
from triaging.services import process_model_response

load_dotenv()

client = OpenAI()

# Initialize Gemini model
model = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest")


# load_dotenv()

# OpenAI Configuration (commented out)
# client = OpenAI()
# model = ChatOpenAI(
#     model_name="gpt-4o-mini",
#     temperature=0.5,
#     # streaming=True
# )

# Gemini Configuration
# api_key = os.getenv("GEMINI_API_KEY")
# genai.configure(api_key=api_key)
# model = genai.GenerativeModel('models/gemini-1.5-pro-latest')

router = APIRouter(
    prefix="/api",
    tags=["Triaging Endpoints"],
    responses={404: {"description": "Not found"}},
)

@router.post('/triage', status_code=status.HTTP_201_CREATED)
async def get_user_question(user_query: UserQuery):
    """Receive user query, process it using Gemini, and generate a list of 5 relevant questions."""
    
    # Initialize the prompt
    prompt_template = get_triaging_prompt_template()
    prompt = prompt_template.format(user_query=user_query.user_query)

    try:
        response_text = await asyncio.to_thread(model.invoke, prompt)
        # print(response)
        # Use Gemini to generate response
        # response = await asyncio.to_thread(
        #     lambda: model.generate_content(prompt)
        # )
        
        # Extract the text from Gemini's response
        # response_text = response.text
        print(response_text)
        
        # Extract the list of questions from the model's response
        # question_list = process_model_response(response)
        question_list = process_model_response(response_text)
        
        # Return the generated questions as a list
        return {"generated_questions": question_list}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")
    
@router.post("/triage/answers", response_model=RecommendationResponse)
async def recommend_system_ai_extraction(data: Dict[str, str] = Body(...)):
    """Generate solar hot water system recommendations based on questionnaire data with AI extraction"""
    try:
        print(f"Received Data: {data}")
        # Extract structured data from questionnaire using AI
        transformed_data = await extract_questionnaire_data_with_ai(data)
        print(f"Transformed data: {transformed_data}")
        
        # Generate prompt and embeddings
        prompt = generate_prompt_from_questionnaire(transformed_data)
        print(f"Prompt: {prompt}")
        
        # Generate embeddings for the prompt
        embeddings = generate_embeddings(prompt)
        
        # Query Pinecone for similar systems
        pinecone_results = get_recommendations_from_pinecone(embeddings)
        # print(f"Pinecone results: {pinecone_results}")
        
        # Analyze requirements
        analysis = analyze_requirements(transformed_data)
        
        # Generate detailed recommendations
        recommendations = generate_ai_recommendations(analysis, pinecone_results, transformed_data)
        
        return recommendations
        
    except Exception as e:
        import traceback
        error_detail = f"Error processing recommendation: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        raise HTTPException(status_code=500, detail=error_detail)
    
@router.post("/recommend", response_model=RecommendationResponse)
async def recommend_system(data: QuestionnaireResponse = Body(...)):
    """Generate solar hot water system recommendations based on questionnaire responses"""
    try:
        # Generate prompt and embeddings
        prompt = generate_prompt_from_questionnaire(data)
        # print(f"Prompt: {prompt}")
        
        # Generate embeddings for the prompt
        embeddings = generate_embeddings(prompt)
        # print(f"Embeddings: {embeddings}")
        
        # Query Pinecone for similar systems
        pinecone_results = get_recommendations_from_pinecone(embeddings)
        # print(f"Pinecone results: {pinecone_results}")
        
        # Analyze requirements
        analysis = analyze_requirements(data)
        
        # Generate detailed recommendations
        recommendations = generate_ai_recommendations(analysis, pinecone_results, data)
        
        return recommendations
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing recommendation: {str(e)}")

@router.post("/futureexpansion", response_model=ExpansionResponse)
async def recommend_expansion(params: ExpansionParameters = Body(...)):
    """Generate recommendations for system expansion using specific Davis & Shirtliff products"""
    try:
        # Mock D&S product database (in real implementation, this would come from your actual database)
        available_systems = {
            "Standard": [
                {"model": "DS-HW300", "capacity": 300, "description": "300L Solar Water Heater"},
                {"model": "DS-HW150", "capacity": 150, "description": "150L Solar Water Heater"},
                {"model": "DS-HW200", "capacity": 200, "description": "200L Solar Water Heater"},
                {"model": "DS-HW500", "capacity": 500, "description": "500L Solar Water Heater"}
            ]
        }

        # Calculate required additional capacity
        required_additional = params.target_capacity - params.current_capacity
        
        # Current system details
        current_system = {
            "model": params.selected_system,
            "capacity": params.current_capacity,
            "location": params.location
        }
        
        # Find optimal combination of additional systems
        additional_systems = []
        remaining_capacity = required_additional
        capacity_breakdown = {"current": params.current_capacity}
        
        # Logic for selecting additional systems
        while remaining_capacity > 0:
            # Find the largest suitable system that doesn't exceed remaining capacity
            suitable_system = None
            for system in available_systems["Standard"]:
                if system["capacity"] <= remaining_capacity:
                    if not suitable_system or system["capacity"] > suitable_system["capacity"]:
                        suitable_system = system
            
            if not suitable_system:
                # If no exact fit, get smallest system that can help
                suitable_system = min(available_systems["Standard"], key=lambda x: x["capacity"])
            
            additional_systems.append(SystemComponent(
                model=suitable_system["model"],
                capacity=suitable_system["capacity"],
                description=suitable_system["description"]
            ))
            
            capacity_breakdown[suitable_system["model"]] = suitable_system["capacity"]
            remaining_capacity -= suitable_system["capacity"]
            
            if len(additional_systems) >= 3:  # Limit to prevent too many separate systems
                break
        
        # Calculate total new capacity
        total_new_capacity = params.current_capacity + sum(system.capacity for system in additional_systems)
        
        # Generate detailed reasoning
        reasoning = f"Based on your target capacity of {params.target_capacity}L and current capacity of {params.current_capacity}L, "
        reasoning += f"we recommend adding {len(additional_systems)} additional system(s) to achieve a total capacity of {total_new_capacity}L. "
        reasoning += "The combination was selected to optimize for:\n"
        reasoning += "1. Minimal number of additional units\n"
        reasoning += "2. Standard available system sizes\n"
        reasoning += "3. Efficient integration with existing system"
        
        # Generate installation notes
        installation_notes = [
            f"Connect new {system.model} ({system.capacity}L) to existing system using parallel configuration"
            for system in additional_systems
        ]
        installation_notes.extend([
            "Install non-return valves between systems to prevent backflow",
            "Ensure balanced flow distribution across all units",
            "Configure temperature sensors for synchronized operation"
        ])
        
        # Specific considerations for this expansion
        considerations = [
            f"Total system capacity after expansion: {total_new_capacity}L vs target {params.target_capacity}L",
            "Ensure roof structure can support additional weight",
            f"Available roof space needed: approximately {sum(system.capacity * 0.5 for system in additional_systems)} sq meters for new collectors",
            "Pressure balancing between multiple systems required",
            "May need to upgrade circulation pump depending on final configuration",
            f"Location considerations for {params.location}: ensure adequate solar exposure for all collectors"
        ]
        
        return ExpansionResponse(
            current_system=current_system,
            additional_systems=additional_systems,
            total_new_capacity=total_new_capacity,
            capacity_breakdown=capacity_breakdown,
            reasoning=reasoning,
            installation_notes=installation_notes,
            considerations=considerations
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing expansion recommendation: {str(e)}")


# import google.generativeai as genai
# from dotenv import load_dotenv
# import os

# # Load environment variables from .env
# load_dotenv()

# # Fetch the API key
# api_key = os.getenv("GEMINI_API_KEY")

# # Configure Gemini
# genai.configure(api_key=api_key)

# for m in genai.list_models():
#     print(m.name, "→", m.supported_generation_methods)


# # Create and use the model
# model = genai.GenerativeModel('models/gemini-1.5-pro-latest')
# response = model.generate_content("Suggest a solar water heating solution for a 5-person household.")

# print(response.text)
