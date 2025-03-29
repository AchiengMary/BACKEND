from typing import Any, List, Dict, Optional
from fastapi import HTTPException
from langchain_openai import ChatOpenAI  # Changed from OpenAI to ChatOpenAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
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

load_dotenv()

# Configuration
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
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

def generate_answer(question: str, chat_history: List[Dict[str, str]]) -> AnswerResponse:
    try:
        # Initialize the custom retriever with the fixed implementation
        retriever = PineconeRetriever(index=index, embeddings=embeddings)
        
        # Initialize LLM with ChatOpenAI instead of OpenAI and use gpt-4o-mini
        llm = ChatOpenAI(
            temperature=0.4,
            api_key=OPENAI_API_KEY,
            model="gpt-4o"  # Changed to gpt-4o-mini
        )
        
        # Create prompt with chat history
        messages = [("system", system_prompt)]
        for turn in chat_history:
            messages.append(("human", turn["question"]))
            messages.append(("ai", turn["answer"]))
        messages.append(("human", question))
        
        prompt = ChatPromptTemplate.from_messages(messages)
        question_answer_chain = create_stuff_documents_chain(llm, prompt)
        rag_chain = create_retrieval_chain(retriever, question_answer_chain)
        
        response = rag_chain.invoke({"input": question})
        
        # Check for answer in the response
        if not response or 'answer' not in response:
            # For debugging
            print(f"Response structure: {response}")
            # Try to get the answer from different possible response structures
            if isinstance(response, dict) and 'result' in response:
                answer = response['result']
            else:
                raise ValueError("LLM response missing expected output field")
        else:
            answer = response['answer']
            
        chat_history.append({"question": question, "answer": answer})
        
        return AnswerResponse(answer=answer)
    
    except Exception as e:
        print(f"Error in generate_answer: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate answer: {str(e)}"
        )