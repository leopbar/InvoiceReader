"""
Tests for backend.extraction.graph — routing logic and graph structure.
"""
import pytest

from backend.extraction.graph import route_after_validate, build_graph


class TestRouteAfterValidate:
    def test_success_route(self):
        """No errors → finalize_success."""
        state = {"validation_errors": None, "failed_fields": None}
        assert route_after_validate(state) == "finalize_success"

    def test_empty_lists_route_to_success(self):
        state = {"validation_errors": [], "failed_fields": []}
        assert route_after_validate(state) == "finalize_success"

    def test_generic_error_no_fallback_goes_to_fallback(self):
        """Errors exist but no failed_fields → go to fallback model."""
        state = {
            "validation_errors": [{"type": "api_error"}],
            "failed_fields": None,
            "fallback_used": False,
        }
        assert route_after_validate(state) == "fallback_model"

    def test_generic_error_fallback_used_goes_to_error(self):
        """Already used fallback, still no fields → finalize error."""
        state = {
            "validation_errors": [{"type": "api_error"}],
            "failed_fields": None,
            "fallback_used": True,
        }
        assert route_after_validate(state) == "finalize_error"

    def test_field_errors_with_retries_left(self):
        """Failed fields + retries available → targeted_retry."""
        state = {
            "validation_errors": [{"type": "missing_field"}],
            "failed_fields": ["supplier.name"],
            "attempts": 0,
            "max_attempts": 2,
        }
        assert route_after_validate(state) == "targeted_retry"

    def test_field_errors_retries_exhausted_no_fallback(self):
        """Retries used up, fallback not used yet → fallback_model."""
        state = {
            "validation_errors": [{"type": "missing_field"}],
            "failed_fields": ["supplier.name"],
            "attempts": 2,
            "max_attempts": 2,
            "fallback_used": False,
        }
        assert route_after_validate(state) == "fallback_model"

    def test_field_errors_retries_exhausted_fallback_used(self):
        """Everything exhausted → finalize_error."""
        state = {
            "validation_errors": [{"type": "missing_field"}],
            "failed_fields": ["supplier.name"],
            "attempts": 2,
            "max_attempts": 2,
            "fallback_used": True,
        }
        assert route_after_validate(state) == "finalize_error"

    def test_missing_attempts_defaults(self):
        """state.get('attempts', 0) should default to 0."""
        state = {
            "validation_errors": [{"type": "error"}],
            "failed_fields": ["totals.total_amount"],
            "fallback_used": False,
        }
        # attempts defaults to 0, max_attempts defaults to 2
        assert route_after_validate(state) == "targeted_retry"


class TestBuildGraph:
    def test_graph_compiles(self):
        """Ensure the LangGraph StateGraph compiles without errors."""
        graph = build_graph()
        assert graph is not None

    def test_graph_has_expected_nodes(self):
        graph = build_graph()
        node_names = set(graph.nodes.keys())
        expected = {
            "preprocess_document", "select_model", "extract", "validate",
            "targeted_retry", "fallback_model", "finalize_success", "finalize_error",
            "__start__",
        }
        # graph.nodes includes __start__ and our nodes
        assert expected.issubset(node_names), f"Missing nodes: {expected - node_names}"
