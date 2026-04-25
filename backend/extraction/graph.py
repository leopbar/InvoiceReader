from langgraph.graph import StateGraph, START, END
from .state import ExtractionState
from .nodes import (
    preprocess_document_node,
    select_model_node,
    extract_node,
    validate_node,
    targeted_retry_node,
    fallback_model_node,
    finalize_success_node,
    finalize_error_node
)

def route_after_validate(state: ExtractionState):
    if not state.get("validation_errors") and not state.get("failed_fields"):
        return "finalize_success"
    
    # If we have an API error (e.g. 429 Quota), jump straight to fallback
    errors = state.get("validation_errors") or []
    is_api_error = any(e.get("type") in ["api_error", "api_config_error"] for e in errors)
    
    if is_api_error:
        if not state.get("fallback_used"):
            return "fallback_model"
        return "finalize_error"

    # If we have errors but NO specific failed fields, it's a generic failure.
    # Targeted retry won't help, so we go straight to fallback or error.
    if not state.get("failed_fields"):
        if not state.get("fallback_used"):
            return "fallback_model"
        return "finalize_error"
    
    # If we have already used a fallback model, we DO NOT retry or cycle further.
    # We either succeed with what we have or finalize the error.
    if state.get("fallback_used"):
        if state.get("parsed_data"):
            return "finalize_success"
        return "finalize_error"

    attempts = state.get("attempts", 0)
    max_attempts = state.get("max_attempts", 2)
    
    if attempts < max_attempts:
        return "targeted_retry"
    
    return "fallback_model"

def build_graph():
    workflow = StateGraph(ExtractionState)

    workflow.add_node("preprocess_document", preprocess_document_node)
    workflow.add_node("select_model", select_model_node)
    workflow.add_node("extract", extract_node)
    workflow.add_node("validate", validate_node)
    workflow.add_node("targeted_retry", targeted_retry_node)
    workflow.add_node("fallback_model", fallback_model_node)
    workflow.add_node("finalize_success", finalize_success_node)
    workflow.add_node("finalize_error", finalize_error_node)

    workflow.add_edge(START, "preprocess_document")
    workflow.add_edge("preprocess_document", "select_model")
    workflow.add_edge("select_model", "extract")
    workflow.add_edge("extract", "validate")
    
    workflow.add_conditional_edges(
        "validate",
        route_after_validate,
        {
            "finalize_success": "finalize_success",
            "targeted_retry": "targeted_retry",
            "fallback_model": "fallback_model",
            "finalize_error": "finalize_error"
        }
    )
    
    workflow.add_edge("targeted_retry", "validate")
    workflow.add_edge("fallback_model", "extract")
    workflow.add_edge("finalize_success", END)
    workflow.add_edge("finalize_error", END)

    return workflow.compile()

def run_extraction(text: str = None, image_base64: str = None, file_type: str = None) -> dict:
    graph = build_graph()
    
    initial_state = {
        "raw_text": text,
        "image_base64": image_base64,
        "file_type": file_type,
        "attempts": 0,
        "fallback_used": False
    }
    
    final_state = graph.invoke(initial_state)
    
    from .schemas import ExtractionResult
    
    result = ExtractionResult(
        success=final_state.get("final_result") is not None,
        data=final_state.get("final_result"),
        error=final_state.get("final_error"),
        validation_errors=final_state.get("validation_errors"),
        attempts=final_state.get("attempts", 0),
        model_used=final_state.get("current_model"),
        token_stats=final_state.get("token_stats")
    )
    
    return result.model_dump(mode="json")
