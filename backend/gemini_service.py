import os
import logging
from typing import Optional
from dotenv import load_dotenv

# Absolute imports to be consistent with main.py
from backend.invoice_graph import run_invoice_workflow
from backend.cache_service import cache_service
from backend.text_preprocessor import estimate_tokens

logger = logging.getLogger(__name__)

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)

def extract_invoice_data(file_bytes: bytes = None, filename: str = None, text: str = None, image_base64: str = None):
    """
    Extracts invoice data using the LangGraph workflow.
    - Checks cache first.
    - If miss, runs the LangGraph workflow.
    - Caches the result.
    - Returns structured data with extraction details.
    """
    if not file_bytes:
        logger.warning("extract_invoice_data called without file_bytes. This may bypass caching.")
        raise ValueError("file_bytes is required for the new workflow.")

    # 1. Check cache first
    file_hash = cache_service.hash_file(file_bytes)
    cached_entry = cache_service.get_cached(file_hash)
    
    if cached_entry:
        logger.info(f"Returning cached result for {filename}")
        tokens_saved = cached_entry.get("estimated_tokens", 500)
        cache_service.add_tokens_saved(tokens_saved)
        return cached_entry.get("data")

    # 2. Run LangGraph workflow
    logger.info(f"Cache miss for {filename}. Running LangGraph workflow...")
    result = run_invoice_workflow(file_bytes, filename)
    
    extracted_data = result.get("extracted_data", {})
    ai_skipped = result.get("ai_skipped", False)
    extraction_method = result.get("extraction_method", "ai_only")
    
    # Add extraction info to the data
    extracted_data["ai_skipped"] = ai_skipped
    extracted_data["extraction_method"] = extraction_method
    
    # 3. Token estimation
    if ai_skipped:
        # We saved what would have been used if we didn't have regex
        cleaned_text = result.get("cleaned_text", "")
        saved_count = 200 + estimate_tokens(cleaned_text)
        cache_service.add_tokens_saved(saved_count)
        total_estimated_tokens = 0
        logger.info(f"AI skipped. {saved_count} tokens saved by regex.")
    else:
        # Estimate tokens used for this request
        cleaned_text = result.get("cleaned_text", "")
        text_tokens = estimate_tokens(cleaned_text)
        total_estimated_tokens = 200 + text_tokens
    
    # 4. Cache the result
    if extracted_data:
        cache_entry = {
            "data": extracted_data,
            "estimated_tokens": total_estimated_tokens
        }
        cache_service.set_cache(file_hash, cache_entry)
        
    return extracted_data
