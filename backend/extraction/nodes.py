import json
import logging
from typing import Dict, Any, List
from pydantic import ValidationError
from langchain_core.messages import HumanMessage, SystemMessage

from .state import ExtractionState
from .preprocessor import preprocess
from .llm_clients import get_llm
from .schemas import Invoice
from .prompts import EXTRACTION_PROMPT, build_targeted_retry_prompt

logger = logging.getLogger("invoice_reader.nodes")
import os

def preprocess_document_node(state: ExtractionState) -> Dict[str, Any]:
    cleaned_text, complexity = preprocess(
        state.get("raw_text"), 
        state.get("image_base64"), 
        state.get("file_type")
    )
    return {
        "cleaned_text": cleaned_text,
        "complexity_signal": complexity
    }

def select_model_node(state: ExtractionState) -> Dict[str, Any]:
    complexity = state.get("complexity_signal", "simple")
    # Default to gemini
    model_key = "gemini_cheap" if complexity == "simple" else "gemini_expensive"
    
    return {
        "current_model": model_key,
        "attempts": 0,
        "max_attempts": 2,
        "fallback_used": False
    }

def extract_node(state: ExtractionState) -> Dict[str, Any]:
    model_key = state.get("current_model")
    
    try:
        llm = get_llm(model_key)
    except Exception as e:
        logger.error(f"Failed to initialize LLM client {model_key}: {str(e)}")
        return {
            "validation_errors": [{"type": "api_config_error", "msg": str(e)}],
            "attempts": state.get("attempts", 0) + 1
        }
    
    content = []
    if state.get("cleaned_text"):
        content.append({"type": "text", "text": f"Invoice content to analyze:\n{state['cleaned_text']}"})
    
    if state.get("image_base64"):
        content.append({"type": "text", "text": "Please extract the invoice data from the attached image."})
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{state['image_base64']}"}
        })
    
    messages = [
        SystemMessage(content=EXTRACTION_PROMPT),
        HumanMessage(content=content)
    ]
    
    logger.info(f"Invoking LLM ({model_key}) with {len(content)} content items")
    try:
        result = llm.invoke(messages)
        logger.info(f"LLM extraction successful for {model_key}")
        # result is an Invoice object
        parsed_data = result.model_dump(mode="json")
        logger.debug(f"Parsed data: {parsed_data}")
        return {
            "parsed_data": parsed_data,
            "raw_output": "Structured Output Received", # We don't have raw JSON here easily with LangChain
            "validation_errors": None
        }
    except Exception as e:
        logger.error(f"LLM extraction failed: {str(e)}")
        return {
            "validation_errors": [{"type": "api_error", "msg": str(e)}],
            "attempts": state.get("attempts", 0) + 1
        }

def validate_node(state: ExtractionState) -> Dict[str, Any]:
    data = state.get("parsed_data")
    if not data:
        return {}
    
    try:
        invoice = Invoice.model_validate(data)
        return {
            "parsed_data": invoice.model_dump(mode="json"),
            "validation_errors": None,
            "failed_fields": None
        }
    except ValidationError as e:
        failed_fields = []
        for error in e.errors():
            loc = ".".join([str(p) for p in error["loc"]])
            failed_fields.append(loc)
            
        return {
            "validation_errors": e.errors(),
            "failed_fields": failed_fields
        }

def targeted_retry_node(state: ExtractionState) -> Dict[str, Any]:
    failed_fields = state.get("failed_fields") or []
    cleaned_text = state.get("cleaned_text", "")
    
    if not failed_fields:
        # If no specific fields failed (e.g., API error), we can't do a targeted retry.
        # We'll just increment attempts and return, which will likely trigger fallback or finalize_error.
        return {"attempts": state.get("attempts", 0) + 1}

    # Simple excerpt extraction: find lines containing keywords from failed fields
    relevant_lines = []
    keywords = set()
    for field in failed_fields:
        keywords.update(field.split("."))
    
    lines = cleaned_text.split("\n")
    for line in lines:
        if any(kw.lower() in line.lower() for kw in keywords if len(kw) > 2):
            relevant_lines.append(line)
            
    excerpt = "\n".join(relevant_lines)[:1500]
    if not excerpt:
        excerpt = cleaned_text[:1500]
        
    prompt = build_targeted_retry_prompt(failed_fields, excerpt)
    
    model_key = state.get("current_model")
    try:
        llm = get_llm(model_key)
    except Exception as e:
        return {
            "validation_errors": [{"type": "api_config_error", "msg": str(e)}],
            "attempts": state.get("attempts", 0) + 1
        }
    
    try:
        result = llm.invoke([HumanMessage(content=prompt)])
        # Merge with existing parsed_data
        existing_data = state.get("parsed_data", {})
        new_data = result.model_dump(mode="json")
        
        # Deep merge for simple fields (one level for simplicity)
        for k, v in new_data.items():
            if isinstance(v, dict) and k in existing_data and isinstance(existing_data[k], dict):
                existing_data[k].update(v)
            elif v is not None:
                existing_data[k] = v
                
        return {
            "parsed_data": existing_data,
            "attempts": state.get("attempts", 0) + 1
        }
    except Exception as e:
        return {
            "validation_errors": [{"type": "retry_error", "msg": str(e)}],
            "attempts": state.get("attempts", 0) + 1
        }

def fallback_model_node(state: ExtractionState) -> Dict[str, Any]:
    current_model = state.get("current_model")
    if "gemini" in current_model:
        new_model = current_model.replace("gemini", "openai")
    else:
        new_model = current_model.replace("openai", "gemini")
        
    return {
        "current_model": new_model,
        "fallback_used": True,
        "parsed_data": None,
        "validation_errors": None,
        "failed_fields": None
    }

def finalize_success_node(state: ExtractionState) -> Dict[str, Any]:
    return {
        "final_result": state.get("parsed_data"),
        "final_error": None
    }

def finalize_error_node(state: ExtractionState) -> Dict[str, Any]:
    errors = state.get("validation_errors", [])
    error_msg = json.dumps(errors) if errors else "Unknown extraction error"
    return {
        "final_result": None,
        "final_error": f"Extraction failed after multiple attempts. Last errors: {error_msg}"
    }
