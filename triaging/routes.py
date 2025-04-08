
import asyncio
from fastapi import APIRouter, HTTPException, Query,status,Depends, Body
from langchain.chains import LLMChain
from triaging.schemas import UserQuery
from triaging.prompt import get_triaging_prompt_template
from dotenv import load_dotenv
from openai import OpenAI
from langchain_openai import ChatOpenAI
from triaging.services import process_model_response, generate_ai_recommendations
from triaging.schemas import QuestionnaireResponse, RecommendationResponse
from triaging.helper import generate_prompt_from_questionnaire, generate_embeddings, get_recommendations_from_pinecone, analyze_requirements

load_dotenv()

client = OpenAI()

# Initialize Gemini model
# model = ChatGoogleGenerativeAI(model="gemini-1.5-flash")

model = ChatOpenAI(
    model_name="gpt-4o-mini",
    temperature=0.5,
    # streaming=True
)


router = APIRouter(
    prefix="/api",
    tags=["Triaging Endpoints"],
    responses={404: {"description": "Not found"}},
)

@router.post('/triage', status_code=status.HTTP_201_CREATED)
async def get_user_question(user_query: UserQuery):
    """Receive user query, process it using OpenAI, and generate a list of 5 relevant questions."""
    
    # Initialize the Langchain model and prompt
    prompt_template = get_triaging_prompt_template()
    prompt = prompt_template.format(user_query=user_query.user_query)

    try:
        response = await asyncio.to_thread(model.invoke, prompt)
        print(response)
        
        # Extract the list of questions from the model's response
        question_list = process_model_response(response)
        
        # Return the generated questions as a list
        return {"generated_questions": question_list}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")
    
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

