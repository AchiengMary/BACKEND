import asyncio
from typing import Dict
from fastapi import APIRouter, HTTPException, Query,status,Depends, Body
from langchain.chains import LLMChain
from langchain_google_genai import ChatGoogleGenerativeAI
from triaging.schemas import UserQuery, QuestionnaireResponse, RecommendationResponse, ExpansionParameters, ExpansionResponse, SystemComponent
from triaging.prompt import get_triaging_prompt_template, expansion_system_prompt
from dotenv import load_dotenv
from openai import OpenAI
from langchain_openai import ChatOpenAI
from triaging.services import process_model_response, generate_ai_recommendations
from triaging.helper import generate_prompt_from_questionnaire, generate_embeddings, get_recommendations_from_pinecone, analyze_requirements, extract_questionnaire_data_with_ai
# import google.generativeai as genai
import os
from triaging.services import process_model_response
import json
import re

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
    """Generate recommendations for system expansion using Davis & Shirtliff products from Pinecone"""
    try:
        # Generate prompt for the expansion scenario
        expansion_prompt = f"""
        Current System:
        - Model: {params.selected_system}
        - Capacity: {params.current_capacity} litres
        - Users: {params.current_users}
        - Location: {params.location}
        Target Capacity: {params.target_capacity} litres
        Additional Capacity Needed: {params.target_capacity - params.current_capacity} litres
        """
        
        # Generate embeddings for the expansion requirements
        embeddings = generate_embeddings(expansion_prompt)
        
        # Query Pinecone for similar systems
        pinecone_results = get_recommendations_from_pinecone(embeddings)
        
        # Analyze expansion requirements
        analysis = {
            "current_capacity": params.current_capacity,
            "target_capacity": params.target_capacity,
            "additional_capacity_needed": params.target_capacity - params.current_capacity,
            "location": params.location,
            "current_users": params.current_users
        }
        
        # Use AI to generate detailed recommendations
        user_prompt = f"""
        ## Current System Information:
        - Model: {params.selected_system}
        - Current Capacity: {params.current_capacity} litres
        - Location: {params.location}
        - Current Users: {params.current_users}
        
        ## Expansion Requirements:
        - Target Capacity: {params.target_capacity} litres
        - Additional Capacity Needed: {analysis['additional_capacity_needed']} litres
        
        ## Available Systems from Database:
        {json.dumps(pinecone_results, indent=2)}
        
        Based on the current system and expansion requirements:
        1. Recommend specific additional Davis & Shirtliff systems that would best complement the existing system
        2. Ensure the total capacity meets or slightly exceeds the target
        3. Prefer combinations that use standard system sizes (e.g., 300L + 150L for 450L need)
        4. Include specific installation and integration considerations
        
        Format your response as a JSON object with:
        - current_system: object with model and capacity
        - additional_systems: array of recommended systems with model, capacity, and description
        - total_new_capacity: total capacity after expansion
        - capacity_breakdown: object showing capacity contribution from each component
        - reasoning: detailed explanation of recommendations
        - installation_notes: array of specific installation steps
        - considerations: array of important considerations
        """
        
        # Generate AI response using expansion-specific system prompt
        messages = [
            {"role": "system", "content": expansion_system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        result = model.invoke(messages)
        response_text = result.content
        
        try:
            # Parse JSON response
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
            if json_match:
                parsed_json = json.loads(json_match.group(1))
            else:
                json_match = re.search(r'(\{[\s\S]*\})', response_text)
                if json_match:
                    parsed_json = json.loads(json_match.group(1))
                else:
                    parsed_json = json.loads(response_text)
                    
            # Convert to ExpansionResponse
            return ExpansionResponse(
                current_system=parsed_json["current_system"],
                additional_systems=[
                    SystemComponent(
                        model=sys["model"],
                        capacity=sys["capacity"],
                        description=sys["description"]
                    ) for sys in parsed_json["additional_systems"]
                ],
                total_new_capacity=parsed_json["total_new_capacity"],
                capacity_breakdown=parsed_json["capacity_breakdown"],
                reasoning=parsed_json["reasoning"],
                installation_notes=parsed_json["installation_notes"],
                considerations=parsed_json["considerations"]
            )
            
        except Exception as json_err:
            print(f"Error parsing AI response: {str(json_err)}")
            raise HTTPException(status_code=500, detail="Error processing AI recommendations")
            
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
