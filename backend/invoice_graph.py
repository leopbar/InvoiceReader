import os
import logging
from typing import TypedDict, Optional, List, Dict, Any
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

# Absolute imports to be consistent with main.py
from backend.schemas import InvoiceData
from backend.text_preprocessor import clean_text, truncate_if_needed, normalize_amount
from backend.file_processor import process_file
from backend.regex_extractor import extract_with_regex

logger = logging.getLogger(__name__)

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)

class GraphState(TypedDict):
    file_bytes: bytes
    filename: str
    file_type: str
    raw_text: str
    cleaned_text: str
    image_base64: str
    extracted_data: Dict[str, Any]
    regex_data: Dict[str, Any]
    regex_confidence: float
    ai_skipped: bool
    extraction_method: str # regex_only, regex_plus_ai, ai_only
    is_valid: bool
    error: str
    retry_count: int

def classify_node(state: GraphState) -> GraphState:
    logger.info(f"Node: classify | File: {state['filename']}")
    ext = state["filename"].split('.')[-1].lower() if '.' in state["filename"] else ''
    state["file_type"] = ext
    # Default extraction method
    if ext in ['png', 'jpg', 'jpeg']:
        state["extraction_method"] = "ai_only"
    else:
        state["extraction_method"] = "regex_only"
    return state

def extract_text_node(state: GraphState) -> GraphState:
    logger.info("Node: extract_text")
    result = process_file(state["file_bytes"], state["filename"])
    state["raw_text"] = result.get("text") or ""
    state["image_base64"] = result.get("image_base64") or ""
    return state

def preprocess_node(state: GraphState) -> GraphState:
    logger.info("Node: preprocess")
    if state["raw_text"]:
        state["cleaned_text"] = clean_text(state["raw_text"])
        state["cleaned_text"] = truncate_if_needed(state["cleaned_text"])
    return state

def regex_extract_node(state: GraphState) -> GraphState:
    """
    Tries to extract data using regex logic.
    Only applicable for text-based files.
    """
    if state["image_base64"] or not state["cleaned_text"]:
        state["regex_confidence"] = 0.0
        state["ai_skipped"] = False
        return state
    
    logger.info("Node: regex_extract")
    regex_result = extract_with_regex(state["cleaned_text"])
    
    state["regex_data"] = regex_result["extracted_data"]
    state["regex_confidence"] = regex_result["confidence_score"]
    
    if state["regex_confidence"] >= 0.75:
        logger.info("Regex extraction sufficient — AI skipped, 0 tokens used")
        state["ai_skipped"] = True
        state["extracted_data"] = state["regex_data"]
    else:
        logger.info(f"Regex confidence low ({state['regex_confidence']}). Proceeding to AI.")
        state["ai_skipped"] = False
        state["extraction_method"] = "regex_plus_ai"
        
    return state

def extract_invoice_node(state: GraphState) -> GraphState:
    logger.info(f"Node: extract_invoice | Retry: {state['retry_count']}")
    
    # Use the model requested by the user
    llm = ChatGoogleGenerativeAI(
        model="gemini-3-flash-preview",
        temperature=0,
        google_api_key=os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    )
    
    structured_llm = llm.with_structured_output(InvoiceData)
    
    # Base prompt with strict monetary formatting instructions
    prompt = (
        "Extract all invoice data from this document. Return structured data matching the schema exactly. "
        "Use null for missing fields. Dates in YYYY-MM-DD format. "
        "IMPORTANT: For all monetary values, return plain numbers with a dot as decimal separator and no thousands separator. "
        "Examples: 1234.56 (correct), 1.234,56 (wrong), $1,234.56 (wrong). Just the number: 1234.56"
    )
    
    # Optimization if regex already found some data
    if state.get("regex_data") and not state["ai_skipped"]:
        found_data = state["regex_data"]
        missing = [f for f, v in [
            ("invoice_number", found_data["invoice_info"]["invoice_number"]),
            ("invoice_date", found_data["invoice_info"]["invoice_date"]),
            ("supplier_name", found_data["supplier"]["name"]),
            ("total_amount", found_data["totals"]["total_amount"])
        ] if v is None]
        
        prompt = f"Extract invoice data. Some fields were already partially extracted via regex. Verify these and fill in the missing ones: {', '.join(missing) if missing else 'all fields'}. Already found partial data: {found_data}. Return the full structured data matching the schema."

    content = []
    content.append({"type": "text", "text": prompt})
    
    if state["image_base64"]:
        # Vision extraction
        mime_type = f"image/{state['file_type']}"
        if state['file_type'] == 'jpg': mime_type = "image/jpeg"
        
        content.append({
            "type": "image_url",
            "image_url": f"data:{mime_type};base64,{state['image_base64']}"
        })
    elif state["cleaned_text"]:
        # Text extraction
        content.append({"type": "text", "text": f"Document Content:\n{state['cleaned_text']}"})
    
    if state["retry_count"] > 0:
        content.append({"type": "text", "text": f"\nIMPORTANT: This is a retry attempt {state['retry_count']}. Please ensure you extract the following missing or incorrect fields accurately: {state['error']}"})

    try:
        response = structured_llm.invoke([HumanMessage(content=content)])
        raw_data = response.model_dump()
        
        # Normalize all monetary values in the response
        if raw_data.get("totals"):
            raw_data["totals"]["subtotal"] = normalize_amount(raw_data["totals"].get("subtotal"))
            raw_data["totals"]["tax_amount"] = normalize_amount(raw_data["totals"].get("tax_amount"))
            raw_data["totals"]["discount"] = normalize_amount(raw_data["totals"].get("discount"))
            raw_data["totals"]["total_amount"] = normalize_amount(raw_data["totals"].get("total_amount"))
        
        if raw_data.get("line_items"):
            for item in raw_data["line_items"]:
                item["unit_price"] = normalize_amount(item.get("unit_price"))
                item["total_price"] = normalize_amount(item.get("total_price"))
        
        state["extracted_data"] = raw_data
    except Exception as e:
        logger.error(f"Error in extraction: {str(e)}")
        state["error"] = str(e)
        state["extracted_data"] = state.get("regex_data", {}) # Fallback to regex if available
        
    return state

def validate_node(state: GraphState) -> GraphState:
    logger.info("Node: validate")
    data = state["extracted_data"]
    if not data:
        state["is_valid"] = False
        state["error"] = "No data extracted"
        return state

    missing_fields = []
    
    # Check critical fields
    invoice_info = data.get("invoice_info") or {}
    totals = data.get("totals") or {}
    supplier = data.get("supplier") or {}
    
    if not invoice_info.get("invoice_number"):
        missing_fields.append("invoice_number")
    
    if totals.get("total_amount") is None:
        missing_fields.append("total_amount")
        
    if not supplier.get("name"):
        missing_fields.append("supplier name")
        
    if missing_fields:
        state["is_valid"] = False
        state["error"] = ", ".join(missing_fields)
        logger.warning(f"Validation failed. Missing: {state['error']}")
    else:
        state["is_valid"] = True
        state["error"] = ""
        logger.info("Validation successful")
        
    return state

def retry_node(state: GraphState) -> GraphState:
    logger.info(f"Node: retry | Current count: {state['retry_count']}")
    state["retry_count"] += 1
    state["extraction_method"] = "regex_plus_ai" # Mark as using AI if we retry
    return state

def decide_next_node(state: GraphState) -> str:
    if state["is_valid"]:
        return END
    if state["retry_count"] < 2:
        return "retry"
    logger.error("Max retries reached. Returning partial data.")
    return END

def decide_regex_logic(state: GraphState) -> str:
    if state["ai_skipped"]:
        return "validate"
    return "extract_invoice"

# Build Graph
builder = StateGraph(GraphState)
builder.add_node("classify", classify_node)
builder.add_node("extract_text", extract_text_node)
builder.add_node("preprocess", preprocess_node)
builder.add_node("regex_extract", regex_extract_node)
builder.add_node("extract_invoice", extract_invoice_node)
builder.add_node("validate", validate_node)
builder.add_node("retry", retry_node)

builder.add_edge(START, "classify")
builder.add_edge("classify", "extract_text")
builder.add_edge("extract_text", "preprocess")
builder.add_edge("preprocess", "regex_extract")

builder.add_conditional_edges(
    "regex_extract",
    decide_regex_logic,
    {
        "validate": "validate",
        "extract_invoice": "extract_invoice"
    }
)

builder.add_edge("extract_invoice", "validate")

builder.add_conditional_edges(
    "validate",
    decide_next_node,
    {
        "retry": "retry",
        END: END
    }
)
builder.add_edge("retry", "extract_invoice")

# Compile the graph
invoice_graph = builder.compile()

def run_invoice_workflow(file_bytes: bytes, filename: str):
    initial_state = {
        "file_bytes": file_bytes,
        "filename": filename,
        "file_type": "",
        "raw_text": "",
        "cleaned_text": "",
        "image_base64": "",
        "extracted_data": {},
        "regex_data": {},
        "regex_confidence": 0.0,
        "ai_skipped": False,
        "extraction_method": "ai_only",
        "is_valid": False,
        "error": "",
        "retry_count": 0
    }
    return invoice_graph.invoke(initial_state)
