import os
import logging
from typing import TypedDict, Optional, List, Dict, Any
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

# Absolute imports to be consistent with main.py
from backend.schemas import InvoiceData
from backend.text_preprocessor import clean_text, truncate_if_needed
from backend.file_processor import process_file

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
    is_valid: bool
    error: str
    retry_count: int

def classify_node(state: GraphState) -> GraphState:
    logger.info(f"Node: classify | File: {state['filename']}")
    ext = state["filename"].split('.')[-1].lower() if '.' in state["filename"] else ''
    state["file_type"] = ext
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

def extract_invoice_node(state: GraphState) -> GraphState:
    logger.info(f"Node: extract_invoice | Retry: {state['retry_count']}")
    
    # Use the model requested by the user
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0,
        google_api_key=os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    )
    
    structured_llm = llm.with_structured_output(InvoiceData)
    
    prompt = "Extract all invoice data from this document. Return structured data matching the schema exactly. Use null for missing fields. Dates in YYYY-MM-DD format. Numbers without currency symbols."
    
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
        # response is an InvoiceData object
        state["extracted_data"] = response.model_dump()
    except Exception as e:
        logger.error(f"Error in extraction: {str(e)}")
        state["error"] = str(e)
        state["extracted_data"] = {}
        
    return state

def validate_node(state: GraphState) -> GraphState:
    logger.info("Node: validate")
    data = state["extracted_data"]
    if not data:
        state["is_valid"] = False
        state["error"] = "No data extracted"
        return state

    missing_fields = []
    
    # Check critical fields as requested
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
    return state

def decide_next_node(state: GraphState) -> str:
    if state["is_valid"]:
        return END
    if state["retry_count"] < 2:
        return "retry"
    logger.error("Max retries reached. Returning partial data.")
    return END

# Build Graph
builder = StateGraph(GraphState)
builder.add_node("classify", classify_node)
builder.add_node("extract_text", extract_text_node)
builder.add_node("preprocess", preprocess_node)
builder.add_node("extract_invoice", extract_invoice_node)
builder.add_node("validate", validate_node)
builder.add_node("retry", retry_node)

builder.add_edge(START, "classify")
builder.add_edge("classify", "extract_text")
builder.add_edge("extract_text", "preprocess")
builder.add_edge("preprocess", "extract_invoice")
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
        "is_valid": False,
        "error": "",
        "retry_count": 0
    }
    return invoice_graph.invoke(initial_state)
