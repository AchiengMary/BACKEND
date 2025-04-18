from dotenv import load_dotenv
from openai import OpenAI
load_dotenv()

client = OpenAI()

model = client.responses.create(
    model="gpt-4o-mini",
    
)

'''
import os
from dotenv import load_dotenv

load_dotenv()

llm = None  # default in case nothing loads

# If you're in a local dev environment and want to use Gemini
if os.environ.get("ENV") != "production":
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        llm = ChatGoogleGenerativeAI(model="gemini-pro")
    except ImportError as e:
        print("LangChain Gemini not available, skipping:", e)

# If you're in production or using OpenAI generally
if llm is None:
    from openai import OpenAI
    client = OpenAI()

    # You can change to match the actual call structure you're using
    model = client.responses.create(
        model="gpt-4o-mini",
    )
    llm = model  # assign it to `llm` so the rest of your app uses it
'''
