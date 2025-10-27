# openai_client.py - Simple OpenAI client configuration
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize OpenAI client
client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY')
)

def get_openai_client():
    """Get the configured OpenAI client."""
    return client