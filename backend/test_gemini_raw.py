import os
import google.generativeai as genai
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)

api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)

PROMPT = """You are an expert invoice data extraction AI. Analyze the following invoice content and extract ALL data into a structured JSON format. Return ONLY valid JSON.
{ "supplier": { "name": "Company name of the supplier/vendor" } }
"""

try:
    print("Initializing model gemini-3-flash-preview...")
    model = genai.GenerativeModel("gemini-3-flash-preview")
    response = model.generate_content([PROMPT, "Invoice content: INVOICE from Test Co."])
    print("Response text:")
    print(repr(response.text))
except Exception as e:
    print("Error:", e)
