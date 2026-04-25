"""
Tests for backend.extraction.preprocessor — text cleanup and complexity routing.
"""
import pytest

from backend.extraction.preprocessor import preprocess


class TestTextCleaning:
    def test_removes_page_headers(self):
        text = "Invoice data Page 1 of 5 more data Page 2 of 5"
        cleaned, _ = preprocess(text, None, None)
        assert "Page 1 of 5" not in cleaned
        assert "Page 2 of 5" not in cleaned
        assert "Invoice data" in cleaned

    def test_collapses_whitespace(self):
        text = "Hello    World\n\n\n  Foo"
        cleaned, _ = preprocess(text, None, None)
        assert "    " not in cleaned
        assert "\n\n" not in cleaned
        assert "Hello World Foo" == cleaned

    def test_truncates_long_text(self):
        long_text = "A" * 10000
        cleaned, _ = preprocess(long_text, None, None)
        assert len(cleaned) == 8000

    def test_empty_text(self):
        cleaned, complexity = preprocess("", None, None)
        assert cleaned == ""
        assert complexity == "simple"

    def test_none_text(self):
        cleaned, complexity = preprocess(None, None, None)
        assert cleaned == ""


class TestComplexityRouting:
    def test_simple_short_text(self):
        _, complexity = preprocess("Short invoice text", None, "txt")
        assert complexity == "simple"

    def test_complex_long_text(self):
        long_text = "X" * 3500
        _, complexity = preprocess(long_text, None, "txt")
        assert complexity == "complex"

    def test_complex_when_image_present(self):
        _, complexity = preprocess("short text", "base64data", "png")
        assert complexity == "complex"

    def test_complex_for_image_file_types(self):
        _, complexity = preprocess(None, None, "png")
        assert complexity == "complex"

    def test_complex_for_jpg(self):
        _, complexity = preprocess(None, None, "jpg")
        assert complexity == "complex"

    def test_complex_for_jpeg(self):
        _, complexity = preprocess(None, None, "jpeg")
        assert complexity == "complex"

    def test_simple_for_csv(self):
        _, complexity = preprocess("a,b,c", None, "csv")
        assert complexity == "simple"

    def test_boundary_3000_chars(self):
        """Exactly 3000 chars should be simple (not >3000)."""
        text = "X" * 3000
        _, complexity = preprocess(text, None, "txt")
        assert complexity == "simple"

    def test_3001_chars_is_complex(self):
        text = "X" * 3001
        _, complexity = preprocess(text, None, "txt")
        assert complexity == "complex"
