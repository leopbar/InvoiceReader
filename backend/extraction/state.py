from typing import List, Optional, Literal, Dict, Any, TypedDict

class ExtractionState(TypedDict, total=False):
    # Inputs
    raw_text: Optional[str]
    image_base64: Optional[str]
    file_type: Optional[str]

    # After preprocessing
    cleaned_text: Optional[str]
    complexity_signal: Literal["simple", "complex"]

    # Control
    current_model: Literal["gemini_cheap", "gemini_expensive", "openai_cheap", "openai_expensive"]
    attempts: int
    max_attempts: int          # per model, default 2
    fallback_used: bool
    failed_fields: Optional[List[str]]   # for targeted retry

    # Transient
    raw_output: Optional[str]
    parsed_data: Optional[dict]
    validation_errors: Optional[List[dict]]

    # Terminal
    final_result: Optional[dict]
    final_error: Optional[str]
    token_stats: Optional[Dict[str, int]]  # {"prompt_tokens": n, "completion_tokens": n, ...}
