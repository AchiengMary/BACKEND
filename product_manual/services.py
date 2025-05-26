from typing import Any, List, Dict, Optional
from fastapi import HTTPException
from langchain_openai import ChatOpenAI  # Changed from OpenAI to ChatOpenAI
# from langchain.chains import create_retrieval_chain
# from langchain.chains.combine_documents import create_stuff_documents_chain
# from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from product_manual.schema import AnswerResponse
from product_manual.prompt import *
import os
from langchain_openai import OpenAIEmbeddings
from pinecone import Pinecone
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from pydantic import Field, BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
import uuid

load_dotenv()

# Configuration
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
# GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
# GOOGLE_APPLICATION_CREDENTIALS = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
index_name = "davisandshirliff"

# Validate environment variables
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables")
if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY not found in environment variables")

# Initialize services
embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(index_name)
model = ChatOpenAI(
    model="gpt-4o-mini", # gpt-4o-mini gpt-3.5-turbo
    temperature=0.7
)

# Updated PineconeRetriever class that's compatible with newer LangChain versions
class PineconeRetriever(BaseRetriever, BaseModel):
    index: Any = Field(exclude=True)
    embeddings: Any = Field(exclude=True)
    top_k: int = 5
    
    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
    ) -> List[Document]:
        try:
            # Get embedding for the query
            query_embedding = self.embeddings.embed_query(query)
            
            # Query Pinecone
            results = self.index.query(
                vector=query_embedding,
                top_k=self.top_k,
                include_metadata=True
            )
            
            # Convert Pinecone results to LangChain Documents
            documents = []
            for match in results.matches:
                content = match.metadata.get('text', '') if match.metadata else str(match.id)
                documents.append(
                    Document(
                        page_content=content,
                        metadata=match.metadata or {}
                    )
                )
            return documents
        except Exception as e:
            print(f"Error in Pinecone retrieval: {str(e)}")
            return []  # Return empty list on error

def get_relevant_documents(query: str, top_k: int = 5) -> List[str]:
    """
    Get relevant documents from Pinecone using OpenAI embeddings.
    """
    try:
        # Initialize the retriever with OpenAI embeddings
        retriever = PineconeRetriever(index=index, embeddings=embeddings)
        
        # Create a callback manager for the retriever with required parameters
        run_id = str(uuid.uuid4())
        run_manager = CallbackManagerForRetrieverRun(
            run_id=run_id,
            handlers=[],
            inheritable_handlers=[]
        )
        
        # Get relevant documents with the run_manager
        documents = retriever._get_relevant_documents(query, run_manager=run_manager)
        
        # Extract text from documents
        return [doc.page_content for doc in documents]
    except Exception as e:
        print(f"Error in document retrieval: {str(e)}")
        return []

def generate_answer(question: str, chat_history: List[Dict[str, str]]) -> AnswerResponse:
    try:
        # Get relevant documents using OpenAI embeddings
        relevant_docs = get_relevant_documents(question)
        
        # Create context from relevant documents
        context = "\n\n".join(relevant_docs)
        
        # Create prompt with chat history
        prompt = f"{system_prompt.format(context=context)}\n\n"
        
        # Add chat history to the prompt
        for turn in chat_history:
            prompt += f"Human: {turn['question']}\n"
            prompt += f"Assistant: {turn['answer']}\n\n"
        
        # Add the current question
        prompt += f"Human: {question}\n"
        prompt += "Assistant: "
        
        # Generate answer using Gemini
        response = model.invoke(prompt)
        answer = response.content.strip()
        
        # Update chat history
        chat_history.append({"question": question, "answer": answer})
        
        return AnswerResponse(answer=answer)
    
    except Exception as e:
        print(f"Error in generate_answer: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate answer: {str(e)}"
        )
