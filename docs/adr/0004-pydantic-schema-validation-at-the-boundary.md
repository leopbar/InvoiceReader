# ADR-0004: Enforce Pydantic schema validation at the LLM boundary

## Status
Accepted

## Context
LLM output is untrusted input, structurally: even with "structured output"
modes, a provider can return a wrong type, an out-of-range value, or omit a
required field. If that output is persisted directly into PostgreSQL, malformed
data corrupts the `invoices`/`suppliers`/`invoice_items` tables silently, and
the failure surfaces later (e.g. a broken export or a UI crash) far from its
root cause.

## Decision
Every LLM response is validated against a Pydantic model (`Invoice`, in
`backend/extraction/schemas.py`) immediately after extraction, in
`validate_node`:

```python
try:
    invoice = Invoice.model_validate(data)
    return {"parsed_data": invoice.model_dump(mode="json"), "validation_errors": None, "failed_fields": None}
except ValidationError as e:
    failed_fields = [".".join(str(p) for p in err["loc"]) for err in e.errors()]
    return {"validation_errors": e.errors(), "failed_fields": failed_fields}
```

Field-level validation errors are captured with their dotted path (e.g.
`totals.total_amount`), which becomes the input to targeted retry (ADR-0005)
rather than being treated as an opaque pass/fail. Nothing reaches
`supabase_service.save_invoice` that hasn't passed this validation, and the
`/api/upload` and `/api/upload/stream` endpoints return HTTP 422 with the raw
`validation_errors` list when extraction ultimately fails.

## Consequences

### Positive
- Malformed LLM output is caught at the earliest possible point, before it
  reaches the database, the frontend, or a CSV export.
- Field-level error paths (`e.errors()` with `loc`) are structured data that
  downstream logic (targeted retry, error responses) can consume directly
  instead of parsing free-text error messages.
- The same schema doubles as the LangChain `with_structured_output` target
  (ADR-0002) and the FastAPI response/request model
  (`ExtractionResult`, `InvoiceWithMetadata`), so there is one schema
  definition instead of three.

### Negative / trade-offs
- Pydantic validation is necessarily stricter than "good enough for a human,"
  so a technically-imperfect-but-usable extraction (e.g. a total as a string
  `"1,200.00"` instead of a decimal) is rejected and forces a retry cycle
  rather than being coerced and accepted.
- Schema changes are a coordination point: the Pydantic model, the frontend
  TypeScript types, and the Supabase table columns must all move together, or
  validation passes while persistence silently drops fields.

## Alternatives considered
- **Trust LLM structured-output modes without re-validation** — rejected:
  provider "structured output" is a request-time constraint, not a guarantee;
  it still needs a server-side check, and provider behavior differs
  (Gemini native structured output vs. OpenAI function-calling, per ADR-0002).
- **Validate only at the database layer (constraints/triggers)** — rejected:
  surfaces errors too late to drive retry/fallback logic, and SQL constraint
  errors are far less specific than Pydantic's per-field error paths.
