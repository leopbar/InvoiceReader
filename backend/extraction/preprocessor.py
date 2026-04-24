import re
import logging
from typing import Optional, Literal, Tuple

logger = logging.getLogger("invoice_reader.preprocessor")

def preprocess(text: Optional[str], image_base64: Optional[str], file_type: Optional[str]) -> Tuple[str, Literal["simple", "complex"]]:
    """
    Cleans text and determines document complexity.
    """
    cleaned_text = ""
    if text:
        # Strip page headers/footers (Page X of Y)
        cleaned_text = re.sub(r"(?i)Page\s+\d+\s+of\s+\d+", "", text)
        
        # Remove repeated whitespace
        cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()
        
        # Truncate to 8000 chars
        if len(cleaned_text) > 8000:
            logger.warning(f"Truncating document from {len(cleaned_text)} to 8000 characters.")
            cleaned_text = cleaned_text[:8000]

    # Complexity routing rules:
    # - simple: text/csv/docx AND cleaned content <= 3000 chars -> cheap tier.
    # - complex: image file OR content > 3000 chars -> expensive tier.
    
    is_image = file_type and file_type.lower() in ["png", "jpg", "jpeg", "webp", "pdf_scanned", "image"]
    # Note: frontend usually sends image_base64 if it's an image.
    
    if image_base64 or is_image or len(cleaned_text) > 3000:
        complexity = "complex"
    else:
        complexity = "simple"
        
    return cleaned_text, complexity
