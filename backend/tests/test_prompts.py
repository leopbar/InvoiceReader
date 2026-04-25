"""
Tests for backend.extraction.prompts — prompt templates and formatting.
"""
import pytest

from backend.extraction.prompts import EXTRACTION_PROMPT, build_targeted_retry_prompt


class TestExtractionPrompt:
    def test_prompt_exists_and_not_empty(self):
        assert EXTRACTION_PROMPT is not None
        assert len(EXTRACTION_PROMPT) > 50

    def test_prompt_mentions_key_instructions(self):
        prompt = EXTRACTION_PROMPT.lower()
        assert "extract" in prompt
        assert "invoice" in prompt
        assert "null" in prompt  # "leave it null" instruction


class TestBuildTargetedRetryPrompt:
    def test_includes_failed_fields(self):
        prompt = build_targeted_retry_prompt(
            ["supplier.name", "totals.total_amount"],
            "ACME Corp Invoice #123"
        )
        assert "supplier.name" in prompt
        assert "totals.total_amount" in prompt

    def test_includes_document_excerpt(self):
        prompt = build_targeted_retry_prompt(
            ["supplier.name"],
            "ACME Corp"
        )
        assert "ACME Corp" in prompt

    def test_empty_fields_list(self):
        """Should still produce a valid string."""
        prompt = build_targeted_retry_prompt([], "some text")
        assert isinstance(prompt, str)

    def test_formatting(self):
        prompt = build_targeted_retry_prompt(["field1"], "excerpt")
        assert "- field1" in prompt  # Should use bullet formatting
