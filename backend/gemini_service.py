import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)

# Configure API key
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

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
    try:
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
    except Exception as e:
        print(f"Error extracting data with Gemini: {str(e)}")
        raise e
