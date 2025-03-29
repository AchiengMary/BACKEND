from typing import List, Dict
from pydantic import BaseModel

class QuestionRequest(BaseModel):
    question: str
    chat_history: List[Dict[str, str]] = []

class AnswerResponse(BaseModel):
    answer: str