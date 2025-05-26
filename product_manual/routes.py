from fastapi import APIRouter, HTTPException
from product_manual.services import generate_answer
from product_manual.schema import AnswerResponse, QuestionRequest
import openai  # Import OpenAI library
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
from langdetect import detect, LangDetectException

router = APIRouter(
    prefix="/api",
    tags=["Product Manual Interaction"],
    responses={404: {"description": "Not found"}},
)

load_dotenv()

# OpenAI Configuration (commented out)
# OPENAI_API_KEY=os.environ.get('OPENAI_API_KEY')

# Gemini Configuration
# GOOGLE_APPLICATION_CREDENTIALS = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
# model = ChatGoogleGenerativeAI(
#     model="gemini-1.5-flash",
#     temperature=0.7,
#     convert_system_message_to_human=True
# )
model = ChatOpenAI(
    model="gpt-4o-mini", # gpt-4o-mini gpt-3.5-turbo
    temperature=0.7
)

def translate_text(text, target_language="en"):
    """
    Translates the given text to the target language using Gemini.
    Default target language is English ("en").
    """
    try:
        # response = openai.chat.completions.create(
        #     model="gpt-4o-mini",  # Using a valid model name
        #     messages=[
        #         {"role": "system", "content": "You are a translator."},
        #         {"role": "user", "content": f"Translate the following text to {target_language}: {text}"}
        #     ],
        #     temperature=0.3
        # )
        # translated_text = response.choices[0].message.content.strip()

        prompt = f"Translate the following text to {target_language}: {text}"
        response = model.invoke(prompt)
        translated_text = response.content.strip()
        return translated_text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")


@router.post("/question", response_model=AnswerResponse)
async def ask_question(question_request: QuestionRequest):
    try:
        question = question_request.question
        print(f"Received question: {question}")
        
        # Better language detection
        try:
            detected_lang = detect(question)
            if detected_lang != 'en':
                question = translate_text(question, target_language="english")
                print(f"Translated question: {question}")
        except LangDetectException:
            # If language detection fails, proceed with original question
            pass
        
        chat_history = question_request.chat_history
        response = generate_answer(question, chat_history)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
