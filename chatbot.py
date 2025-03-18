## Q&A Chatbot
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv() # take environment variables from .env file

## function to load our llm model and get response
def get_openai_response(question):
    llm = ChatOpenAI(
        openai_api_key = os.getenv('OPENAI_API_KEY'),
        model_name='gpt-3.5-turbo', 
        temperature=0.7
    )
    response = llm.invoke(question).content
    return response