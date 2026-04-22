import os
import json
import google.generativeai as genai
from openai import OpenAI
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)

# Configure Gemini API key
gemini_api_key = os.environ.get("GEMINI_API_KEY")
if gemini_api_key:
    genai.configure(api_key=gemini_api_key)

# Configure OpenAI client
openai_api_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key) if openai_api_key else None

PROMPT = """
You are an expert invoice data extraction AI. Analyze the following invoice content and extract ALL data into a structured JSON format.

Return ONLY valid JSON with no additional text, no markdown formatting, no code blocks. Just pure JSON.

Extract the following structure:
{
  "supplier": {
    "name": "Company name of the supplier/vendor",
    "address": "Full address",
    "email": "Email if present",
    "phone": "Phone if present",
    "tax_id": "Tax ID / VAT number / EIN if present"
  },
  "invoice_info": {
    "invoice_number": "Invoice number/ID",
    "invoice_date": "Date issued (YYYY-MM-DD format)",
    "due_date": "Payment due date (YYYY-MM-DD format)",
    "currency": "Currency code (USD, EUR, GBP, etc.)",
    "payment_terms": "Payment terms if stated (Net 30, etc.)",
    "purchase_order": "PO number if present"
  },
  "bill_to": {
    "company_name": "Bill-to company name",
    "address_line": "Street address",
    "city": "City",
    "state": "State/Province",
    "zip_code": "ZIP/Postal code",
    "country": "Country"
  },
  "ship_to": {
    "company_name": "Ship-to company name (if different from bill-to)",
    "address_line": "Street address",
    "city": "City",
    "state": "State/Province",
    "zip_code": "ZIP/Postal code",
    "country": "Country"
  },
  "line_items": [
    {
      "description": "Item description",
      "quantity": 0,
      "unit": "Unit of measure",
      "unit_price": 0.00,
      "total_price": 0.00,
      "item_code": "SKU/Item code if present"
    }
  ],
  "totals": {
    "subtotal": 0.00,
    "tax_amount": 0.00,
    "discount": 0.00,
    "total_amount": 0.00
  },
  "notes": "Any additional notes, terms, or bank details on the invoice"
}

If any field is not found in the invoice, use null for that field.
For dates, always convert to YYYY-MM-DD format.
For monetary values, use numbers without currency symbols.

Invoice content to analyze:
"""

def extract_invoice_data(text=None, image_base64=None):
    """
    Tries to extract data using Gemini. If it fails (quota, error, etc.), 
    falls back to OpenAI if configured.
    """
    try:
        print("Attempting extraction with Gemini...")
        return extract_with_gemini(text, image_base64)
    except Exception as gemini_err:
        print(f"Gemini extraction failed: {str(gemini_err)}")
        
        if client:
            try:
                print("Falling back to OpenAI...")
                return extract_with_openai(text, image_base64)
            except Exception as openai_err:
                print(f"OpenAI fallback failed: {str(openai_err)}")
                raise Exception(f"Both AI models failed. Gemini error: {str(gemini_err)}. OpenAI error: {str(openai_err)}")
        else:
            print("OpenAI is not configured as fallback.")
            raise gemini_err

def extract_with_gemini(text=None, image_base64=None):
    model = genai.GenerativeModel("gemini-3-flash-preview")
    
    contents = [PROMPT]
    
    if text:
        contents.append(text)
        
    if image_base64:
        contents.append(
            {"mime_type": "image/jpeg", "data": image_base64}
        )
        
    response = model.generate_content(contents)
    
    response_text = response.text.strip()
    return parse_json_response(response_text)

def extract_with_openai(text=None, image_base64=None):
    if not client:
        raise Exception("OpenAI client not initialized")
    
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": PROMPT}
            ]
        }
    ]
    
    if text:
        messages[0]["content"].append({"type": "text", "text": f"Text content: {text}"})
        
    if image_base64:
        # OpenAI expects base64 in a specific URL format
        image_url = f"data:image/jpeg;base64,{image_base64}"
        messages[0]["content"].append({
            "type": "image_url",
            "image_url": {"url": image_url}
        })
        
    response = client.chat.completions.create(
        model="gpt-4o", # Using gpt-4o for best results with vision
        messages=messages,
        max_tokens=2000,
        response_format={"type": "json_object"}
    )
    
    response_text = response.choices[0].message.content.strip()
    return parse_json_response(response_text)

def parse_json_response(response_text):
    print(f"Raw Model Response Length: {len(response_text)}")
    
    # Find the first '{' and the last '}' to extract the JSON dictionary block
    start_idx = response_text.find('{')
    end_idx = response_text.rfind('}')
    
    if start_idx != -1 and end_idx != -1 and end_idx >= start_idx:
        json_str = response_text[start_idx:end_idx+1]
        try:
            parsed_json = json.loads(json_str)
            return parsed_json
        except json.JSONDecodeError as de:
            raise Exception(f"AI returned improperly formatted JSON. Parse error: {str(de)}")
    else:
        raise Exception("The AI model did not return any JSON object.")
