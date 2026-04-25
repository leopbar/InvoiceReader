import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from .schemas import Invoice

def get_llm(model_key: str):
    """
    Factory keyed on "gemini_cheap" / "gemini_expensive" / "openai_cheap" / "openai_expensive"
    """
    google_api_key = os.environ.get("GOOGLE_API_KEY")
    openai_api_key = os.environ.get("OPENAI_API_KEY")

    if "gemini" in model_key:
        if not google_api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment")
        
        model_name = "gemini-3-flash-preview"
        
        # Note: structured output for Gemini via langchain
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=google_api_key,
            temperature=0,
            response_mime_type="application/json",
            # We will pass the schema during the .with_structured_output call if supported, 
            # or use the raw model and parse it ourselves.
        ).with_structured_output(Invoice)

    elif "openai" in model_key:
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
            
        model_name = "gpt-4o-mini" if "cheap" in model_key else "gpt-4o"
        
        return ChatOpenAI(
            model=model_name,
            api_key=openai_api_key,
            temperature=0,
        ).with_structured_output(Invoice, method="function_calling")
    
    else:
        raise ValueError(f"Unknown model key: {model_key}")
