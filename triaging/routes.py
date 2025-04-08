import asyncio
from fastapi import APIRouter, HTTPException, Query, status, Depends
from langchain.chains import LLMChain
from triaging.schemas import UserQuery
from triaging.prompt import get_triaging_prompt_template
from dotenv import load_dotenv
import google.generativeai as genai
import os
from triaging.services import process_model_response

load_dotenv()

# OpenAI Configuration (commented out)
# client = OpenAI()
# model = ChatOpenAI(
#     model_name="gpt-4o-mini",
#     temperature=0.5,
#     # streaming=True
# )

# Gemini Configuration
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('models/gemini-1.5-pro-latest')

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
        # Use Gemini to generate response
        response = await asyncio.to_thread(
            lambda: model.generate_content(prompt)
        )
        
        # Extract the text from Gemini's response
        response_text = response.text
        print(response_text)
        
        # Extract the list of questions from the model's response
        question_list = process_model_response(response_text)
        
        # Return the generated questions as a list
        return {"generated_questions": question_list}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

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