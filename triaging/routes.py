import asyncio
from typing import Dict
from fastapi import APIRouter, HTTPException, Query,status,Depends, Body
from langchain.chains import LLMChain
from langchain_google_genai import ChatGoogleGenerativeAI
from triaging.schemas import UserQuery, QuestionnaireResponse, RecommendationResponse, ExpansionParameters, ExpansionResponse
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
        print(f"Prompt: {prompt}")
        
        # Generate embeddings for the prompt
        embeddings = generate_embeddings(prompt)
        # print(f"Embeddings: {embeddings}")
        
        # Query Pinecone for similar systems
        pinecone_results = get_recommendations_from_pinecone(embeddings)
        print(f"Pinecone results: {pinecone_results}")
        
        # Analyze requirements
        analysis = analyze_requirements(data)
        
        # Generate detailed recommendations
        recommendations = generate_ai_recommendations(analysis, pinecone_results, data)
        
        return recommendations
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing recommendation: {str(e)}")

@router.post("/futureexpansion", response_model=ExpansionResponse)
async def recommend_expansion(params: ExpansionParameters = Body(...)):
    """Generate recommendations for future system expansion based on current and expected parameters"""
    try:
        # Calculate required capacity increase based on new users
        per_person_usage = params.current_daily_usage / params.current_users
        future_daily_usage = per_person_usage * params.new_users
        required_capacity = (future_daily_usage * 1.2)  # Adding 20% buffer
        capacity_increase = max(0, required_capacity - params.current_capacity)
        
        # Generate recommendations
        recommendations = {
            "system_type": "Hot Water System Expansion",
            "additional_capacity": f"{capacity_increase:.2f} litres",
            "recommended_components": [
                "Additional storage tank" if capacity_increase > 100 else "Tank upgrade",
                "Additional solar collectors",
                "Enhanced circulation system"
            ]
        }
        
        # Calculate estimated costs
        base_cost_per_litre = 100  # Base cost per litre of capacity
        installation_factor = 0.3  # 30% of hardware cost
        hardware_cost = capacity_increase * base_cost_per_litre
        installation_cost = hardware_cost * installation_factor
        
        estimated_costs = {
            "hardware": hardware_cost,
            "installation": installation_cost,
            "total": hardware_cost + installation_cost
        }
        
        # Generate implementation steps
        implementation_steps = [
            "1. Technical assessment of current system",
            "2. Site survey for expansion feasibility",
            "3. Procurement of additional components",
            "4. System upgrade installation",
            "5. Testing and commissioning"
        ]
        
        # Important considerations
        considerations = [
            "Structural capacity of current installation location",
            "Integration with existing system",
            "Minimal disruption to current operations during upgrade",
            "Future maintenance requirements",
            f"Expected completion time: {2 + int(capacity_increase/500)} days"
        ]
        
        return ExpansionResponse(
            recommended_changes=recommendations,
            capacity_increase=capacity_increase,
            estimated_cost=estimated_costs,
            implementation_steps=implementation_steps,
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
