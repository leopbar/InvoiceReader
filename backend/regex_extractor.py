import re
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

def parse_date(date_str: str) -> Optional[str]:
    """
    Tries to parse a date string and return it in YYYY-MM-DD format.
    Formats: MM/DD/YYYY, DD/MM/YYYY, YYYY-MM-DD, Month DD YYYY, DD-Mon-YYYY
    """
    if not date_str:
        return None
    
    # Remove ordinal suffixes like 1st, 2nd, 3rd, 4th
    date_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)
    
    formats = [
        "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%d-%m-%Y",
        "%B %d, %Y", "%b %d, %Y", "%d %B %Y", "%d %b %Y",
        "%m/%d/%y", "%d/%m/%y", "%Y/%m/%d"
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
            
    return None

def parse_amount(amount_str: str) -> Optional[float]:
    """
    Extracts numeric value from a string, handling currency symbols and commas.
    """
    if not amount_str:
        return None
    
    # Remove currency symbols and spaces
    clean_str = re.sub(r'[^\d\.,-]', '', amount_str)
    
    # Handle cases like "1.234,56" (European) vs "1,234.56" (US)
    if ',' in clean_str and '.' in clean_str:
        if clean_str.rfind(',') > clean_str.rfind('.'):
            # European format: 1.234,56
            clean_str = clean_str.replace('.', '').replace(',', '.')
        else:
            # US format: 1,234.56
            clean_str = clean_str.replace(',', '')
    elif ',' in clean_str:
        # Check if comma is decimal separator (e.g., "123,45") or thousands (e.g., "1,000")
        parts = clean_str.split(',')
        if len(parts[-1]) == 2:
            clean_str = clean_str.replace(',', '.')
        else:
            clean_str = clean_str.replace(',', '')

    try:
        return float(clean_str)
    except ValueError:
        return None

def extract_with_regex(text: str) -> dict:
    """
    Extracts invoice data using regex patterns.
    Returns structured data and a confidence score.
    """
    data = {
        "supplier": {"name": None, "address": None, "email": None, "phone": None, "tax_id": None},
        "invoice_info": {"invoice_number": None, "invoice_date": None, "due_date": None, "currency": None, "payment_terms": None, "purchase_order": None},
        "bill_to": {"company_name": None, "address_line": None, "city": None, "state": None, "zip_code": None, "country": None},
        "ship_to": {"company_name": None, "address_line": None, "city": None, "state": None, "zip_code": None, "country": None},
        "line_items": [],
        "totals": {"subtotal": None, "tax_amount": None, "discount": None, "total_amount": None},
        "notes": None
    }

    # 1. Invoice Number
    inv_num_patterns = [
        r"(?:Invoice\s*(?:#|No\.?|Number)|Inv\s*(?:#|No\.?|Number)|Inv\.?|Invoice\s*ID)[:\s]*([A-Z0-9\-\/]+)",
        r"Document\s*(?:#|No\.?|Number)[:\s]*([A-Z0-9\-\/]+)"
    ]
    for pattern in inv_num_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            data["invoice_info"]["invoice_number"] = match.group(1).strip()
            break

    # 2. Dates
    date_regex = r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})"
    
    # Invoice Date
    inv_date_pattern = r"(?:Invoice\s*Date|Date(?:\s*of\s*issue)?|Issue\s*Date|Issued|Date)[:\s]*" + date_regex
    match = re.search(inv_date_pattern, text, re.IGNORECASE)
    if match:
        data["invoice_info"]["invoice_date"] = parse_date(match.group(1).strip())
    
    # Due Date
    due_date_pattern = r"(?:Due\s*Date|Payment\s*Due|Due)[:\s]*" + date_regex
    match = re.search(due_date_pattern, text, re.IGNORECASE)
    if match:
        data["invoice_info"]["due_date"] = parse_date(match.group(1).strip())

    # 3. Currency
    currency_pattern = r"(\$|€|£|¥|USD|EUR|GBP|BRL|R\$)"
    match = re.search(currency_pattern, text)
    if match:
        data["invoice_info"]["currency"] = match.group(1).strip().replace("$", "USD").replace("€", "EUR").replace("£", "GBP").replace("¥", "JPY").replace("R$", "BRL")

    # 4. Amounts
    amount_regex = r"([+-]?[0-9]{1,3}(?:[.,\s][0-9]{3})*(?:[.,][0-9]{2}))"
    
    # Total
    total_patterns = [
        r"(?:Total|Total\s*Amount|Grand\s*Total|Amount\s*Due|Balance\s*Due|Total\s*Due)[:\s]*" + amount_regex,
        r"TOTAL\s*PAYABLE[:\s]*" + amount_regex,
        r"Grand\s*Total\s*[:\s]*" + amount_regex
    ]
    for pattern in total_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            data["totals"]["total_amount"] = parse_amount(match.group(1).strip())
            break
    
    # Subtotal
    subtotal_pattern = r"(?:Subtotal|Sub-Total|Sub\s*Total)[:\s]*" + amount_regex
    match = re.search(subtotal_pattern, text, re.IGNORECASE)
    if match:
        data["totals"]["subtotal"] = parse_amount(match.group(1).strip())
    
    # Tax
    tax_pattern = r"(?:Tax|VAT|GST|Sales\s*Tax|Tax\s*Amount)[:\s]*" + amount_regex
    match = re.search(tax_pattern, text, re.IGNORECASE)
    if match:
        data["totals"]["tax_amount"] = parse_amount(match.group(1).strip())

    # 5. Supplier Info
    # Supplier Name (usually first 3 non-empty lines)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines:
        # Filter out lines that look like "INVOICE" or "QUOTATION"
        for i in range(min(len(lines), 5)):
            if not re.match(r"^(Invoice|Quote|Order|Page|Date)", lines[i], re.IGNORECASE):
                data["supplier"]["name"] = lines[i]
                break
    
    # Email
    email_pattern = r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"
    match = re.search(email_pattern, text)
    if match:
        data["supplier"]["email"] = match.group(1).strip()
    
    # Phone
    phone_pattern = r"(?:Phone|Tel|Mobile|Ph)[:\s]*([\+\d\s\-\(\)]{8,})"
    match = re.search(phone_pattern, text, re.IGNORECASE)
    if match:
        data["supplier"]["phone"] = match.group(1).strip()
    
    # Tax ID
    tax_id_pattern = r"(?:Tax\s*ID|EIN|VAT\s*(?:No\.?)?|ABN|TIN|CNPJ|CPF)[:\s]*([A-Z0-9\-\.\s]+)"
    match = re.search(tax_id_pattern, text, re.IGNORECASE)
    if match:
        data["supplier"]["tax_id"] = match.group(1).strip()

    # 6. Payment Terms
    terms_pattern = r"(?:Payment\s*Terms)[:\s]*(.*)"
    match = re.search(terms_pattern, text, re.IGNORECASE)
    if match:
        data["invoice_info"]["payment_terms"] = match.group(1).strip()
    elif re.search(r"\b(Net\s*\d+|Due\s*on\s*Receipt|COD)\b", text, re.IGNORECASE):
        term_match = re.search(r"\b(Net\s*\d+|Due\s*on\s*Receipt|COD)\b", text, re.IGNORECASE)
        data["invoice_info"]["payment_terms"] = term_match.group(1).strip()

    # 7. PO Number
    po_pattern = r"(?:PO\s*(?:#|Number)|Purchase\s*Order|P\.O\.)[:\s]*([A-Z0-9\-\/]+)"
    match = re.search(po_pattern, text, re.IGNORECASE)
    if match:
        data["invoice_info"]["purchase_order"] = match.group(1).strip()

    # Confidence Score Calculation
    critical_fields_found = 0
    missing_fields = []
    
    if data["invoice_info"]["invoice_number"]:
        critical_fields_found += 1
    else:
        missing_fields.append("invoice_number")
        
    if data["totals"]["total_amount"] is not None:
        critical_fields_found += 1
    else:
        missing_fields.append("total_amount")
        
    if data["supplier"]["name"]:
        critical_fields_found += 1
    else:
        missing_fields.append("supplier_name")
        
    if data["invoice_info"]["invoice_date"]:
        critical_fields_found += 1
    else:
        missing_fields.append("invoice_date")
    
    confidence_score = critical_fields_found / 4.0
    
    return {
        "extracted_data": data,
        "confidence_score": confidence_score,
        "missing_fields": missing_fields,
        "critical_fields_found": critical_fields_found,
        "critical_fields_total": 4
    }
