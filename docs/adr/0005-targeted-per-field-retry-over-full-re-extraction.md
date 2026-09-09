# ADR-0005: Targeted per-field retry instead of full re-extraction

## Status
Accepted

## Context
When validation (ADR-0004) fails on a subset of fields — say
`supplier.name` and `totals.total_amount` — the naive recovery is to re-run
the entire extraction prompt against the full document. This re-pays the full
token cost and latency for fields that were already extracted correctly, and
gives the model another full opportunity to get the *already-correct* fields
wrong too.

## Decision
`targeted_retry_node` (`backend/extraction/nodes.py`) retries only the fields
that failed validation:

1. Collect keywords from the dotted failed-field paths
   (`totals.total_amount` → `{"totals", "total_amount"}`).
2. Scan the preprocessed document line-by-line and keep only lines containing
   any keyword (case-insensitive, keywords longer than 2 chars), building an
   excerpt capped at 1500 characters (falling back to the first 1500 characters
   of the full document if no line matches).
3. Build a focused prompt (`build_targeted_retry_prompt`) asking the model to
   correct only the failed fields from that excerpt.
4. Merge the corrected fields into the existing `parsed_data` (dict-level
   merge for nested objects, else overwrite) rather than discarding prior
   output.
5. Route back to `validate` (ADR-0001's graph), bounded by `max_attempts` (2)
   before falling through to provider fallback (ADR-0002).

## Consequences

### Positive
- Retry prompts are a fraction of the size of the original extraction prompt
  (a ≤1500-character excerpt vs. up to 8000 characters), reducing both cost
  and latency per retry.
- Already-correct fields are never re-sent to the model, so they can't be
  silently overwritten with a worse answer.
- Retry failures are additive: `existing_data` is preserved and only touched
  fields are merged in, so a failed retry attempt doesn't regress previously
  valid data.

### Negative / trade-offs
- Keyword-based excerpt selection is a heuristic, not semantic search — a
  field whose relevant text doesn't literally contain the field name/keyword
  (e.g. `totals.total_amount` when the document just says "Amount Due") may
  produce an empty or irrelevant excerpt, falling back to the first 1500
  characters of the document.
- The dict-merge strategy (`existing_data[k].update(v)` for nested dicts) can
  produce inconsistent results if the retry model changes the *shape* of a
  nested object rather than just its values.
- Bounded at `max_attempts = 2`, then falls through to fallback — deep
  validation failures still eventually consume a full provider-fallback cycle.

## Alternatives considered
- **Full re-extraction on any validation failure** — rejected: the original,
  more expensive approach this ADR replaces; strictly worse in cost/latency
  for the common case of one or two bad fields.
- **Semantic/embedding-based excerpt retrieval** — deferred: would improve
  excerpt relevance over keyword matching but adds an embedding call (cost and
  latency) for a problem currently solved acceptably by simple string
  matching; worth revisiting if keyword matching proves too lossy in
  production.
