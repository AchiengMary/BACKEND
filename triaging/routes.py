
import asyncio
from fastapi import APIRouter, HTTPException, Query,status,Depends
from langchain.chains import LLMChain
from triaging.schemas import UserQuery
from triaging.prompt import get_triaging_prompt_template
from dotenv import load_dotenv
from openai import OpenAI
from langchain_openai import ChatOpenAI
from triaging.services import process_model_response

load_dotenv()

client = OpenAI()

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