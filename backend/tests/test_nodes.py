"""
Tests for backend.extraction.nodes — graph node functions (no LLM calls).
"""
import pytest
from pydantic import ValidationError

from backend.extraction.nodes import (
    preprocess_document_node,
    select_model_node,
    validate_node,
    targeted_retry_node,
    fallback_model_node,
    finalize_success_node,
    finalize_error_node,
)


class TestPreprocessDocumentNode:
    def test_text_input(self):
        state = {"raw_text": "Invoice #123  Page 1 of 1  Total: $500", "image_base64": None, "file_type": "txt"}
        result = preprocess_document_node(state)
        assert "cleaned_text" in result
        assert "complexity_signal" in result
        assert "Page 1 of 1" not in result["cleaned_text"]

    def test_image_input(self):
        state = {"raw_text": None, "image_base64": "abc123", "file_type": "png"}
        result = preprocess_document_node(state)
        assert result["complexity_signal"] == "complex"


class TestSelectModelNode:
    def test_simple_gets_cheap(self):
        state = {"complexity_signal": "simple"}
        result = select_model_node(state)
        assert result["current_model"] == "gemini_cheap"
        assert result["attempts"] == 0

    def test_complex_gets_expensive(self):
        state = {"complexity_signal": "complex"}
        result = select_model_node(state)
        assert result["current_model"] == "gemini_expensive"

    def test_missing_complexity_defaults_to_simple(self):
        """state.get('complexity_signal', 'simple') default."""
        state = {}
        result = select_model_node(state)
        assert result["current_model"] == "gemini_cheap"


class TestValidateNode:
    def test_valid_data(self, valid_invoice_data):
        state = {"parsed_data": valid_invoice_data}
        result = validate_node(state)
        assert result["validation_errors"] is None
        assert result["failed_fields"] is None
        assert result["parsed_data"] is not None

    def test_empty_data_fails(self):
        """Data with no supplier name, no invoice number, no total should fail."""
        state = {"parsed_data": {"supplier": {}, "invoice_info": {}, "totals": {}}}
        result = validate_node(state)
        assert result["validation_errors"] is not None
        assert len(result["validation_errors"]) > 0
        assert result["failed_fields"] is not None

    def test_none_data_returns_empty(self):
        state = {"parsed_data": None}
        result = validate_node(state)
        assert result == {}

    def test_missing_parsed_data_key(self):
        state = {}
        result = validate_node(state)
        assert result == {}


class TestTargetedRetryNode:
    def test_no_failed_fields_increments_attempts(self):
        """When failed_fields is None/empty, just increment attempts."""
        state = {"failed_fields": None, "attempts": 1, "cleaned_text": "some text"}
        result = targeted_retry_node(state)
        assert result["attempts"] == 2

    def test_empty_failed_fields_increments_attempts(self):
        state = {"failed_fields": [], "attempts": 0, "cleaned_text": "text"}
        result = targeted_retry_node(state)
        assert result["attempts"] == 1


class TestFallbackModelNode:
    def test_gemini_to_openai(self):
        state = {"current_model": "gemini_cheap"}
        result = fallback_model_node(state)
        assert result["current_model"] == "openai_cheap"
        assert result["fallback_used"] is True
        assert result["attempts"] == 0

    def test_openai_to_gemini(self):
        state = {"current_model": "openai_expensive"}
        result = fallback_model_node(state)
        assert result["current_model"] == "gemini_expensive"

    def test_resets_state(self):
        state = {"current_model": "gemini_cheap", "parsed_data": {"some": "data"}, "validation_errors": [{"err": 1}]}
        result = fallback_model_node(state)
        assert result["parsed_data"] is None
        assert result["validation_errors"] is None
        assert result["failed_fields"] is None


class TestFinalizeSuccessNode:
    def test_sets_final_result(self):
        data = {"supplier": {"name": "Test"}}
        state = {"parsed_data": data}
        result = finalize_success_node(state)
        assert result["final_result"] == data
        assert result["final_error"] is None


class TestFinalizeErrorNode:
    def test_formats_errors(self):
        state = {"validation_errors": [{"type": "api_error", "msg": "quota exceeded"}]}
        result = finalize_error_node(state)
        assert result["final_result"] is None
        assert "quota exceeded" in result["final_error"]

    def test_no_errors(self):
        state = {}
        result = finalize_error_node(state)
        assert "Unknown extraction error" in result["final_error"]
