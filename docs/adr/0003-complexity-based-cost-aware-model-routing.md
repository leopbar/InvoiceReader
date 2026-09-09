# ADR-0003: Complexity-based, cost-aware model routing

## Status
Accepted

## Context
Not every invoice needs the same model tier. A one-page plain-text invoice with
a handful of fields is trivial for a cheap/fast model; a scanned image or a
long, dense document benefits from a more capable (and more expensive) model.
Always calling the expensive tier wastes money; always calling the cheap tier
produces more validation failures (and therefore more retries/fallbacks, which
cost more overall) on hard documents.

## Decision
`backend/extraction/preprocessor.py` classifies every document as `"simple"` or
`"complex"` before model selection, using cheap heuristics rather than a model
call:

```python
is_image = file_type in ["png", "jpg", "jpeg", "webp", "pdf_scanned", "image"]
if image_base64 or is_image or len(cleaned_text) > 3000:
    complexity = "complex"
else:
    complexity = "simple"
```

`select_model_node` maps this signal directly to a model tier:
`gemini_cheap` for `"simple"`, `gemini_expensive` for `"complex"`. The same
preprocessor also normalizes text (strips `Page X of Y` headers, collapses
whitespace, truncates at 8000 characters) before the complexity check.

## Consequences

### Positive
- Cost scales with actual document complexity instead of a flat per-request
  rate — the majority of short text/CSV/DOCX invoices route to the cheap tier.
- The heuristic is a pure function with no external calls, so it's instant and
  fully deterministic/testable (`tests/test_preprocessor.py`).
- The 8000-character truncation bounds worst-case token cost and prompt size
  even for pathological inputs.

### Negative / trade-offs
- The heuristic (byte length, file type) is a proxy for actual document
  difficulty, not a measurement of it — a long but simple invoice (e.g.
  repetitive line items) is routed to the expensive tier unnecessarily, and a
  short but visually dense scanned image is caught only because images are
  unconditionally `"complex"`.
- The 3000-character and 8000-character thresholds are hardcoded, not
  configurable or derived from measured accuracy data.
- Misrouting a genuinely complex document to the cheap tier still gets a
  second chance via targeted retry (ADR-0005) and fallback (ADR-0002), so the
  cost of a wrong complexity call is bounded but not zero.

## Alternatives considered
- **Always use the expensive model** — rejected: unnecessary cost on the
  majority of simple invoices observed in practice.
- **Always use the cheap model** — rejected: unacceptably high validation
  failure rate on images and long documents.
- **LLM-based complexity classification** — rejected: adds an extra paid model
  call purely to decide which model to call next, defeating the cost-saving
  purpose.
