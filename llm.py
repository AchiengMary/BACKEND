from dotenv import load_dotenv
from openai import OpenAI
load_dotenv()

client = OpenAI()

model = client.responses.create(
    model="gpt-4o-mini",
    
)
