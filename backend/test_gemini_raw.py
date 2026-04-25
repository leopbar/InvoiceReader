import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)

api_key = os.environ.get("GOOGLE_API_KEY")

PROMPT = """You are an expert invoice data extraction AI. Analyze the following invoice content and extract ALL data into a structured JSON format. Return ONLY valid JSON.
{ "supplier": { "name": "Company name of the supplier/vendor" } }
"""

try:
    print("Initializing model gemini-3-flash-preview via LangChain...")
    llm = ChatGoogleGenerativeAI(
        model="gemini-3-flash-preview",
        google_api_key=api_key,
        temperature=0
    )
    response = llm.invoke([HumanMessage(content=PROMPT + "\nInvoice content: INVOICE from Test Co.")])
    print("Response text:")
    print(response.content)
except Exception as e:
    print("Error:", e)
