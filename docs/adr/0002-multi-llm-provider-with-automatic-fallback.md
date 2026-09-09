# ADR-0002: Multi-LLM provider strategy — Gemini primary, OpenAI fallback

## Status
Accepted

## Context
Relying on a single LLM provider means a provider-side outage or a `429` quota
error becomes an application-wide outage. During development, both Google
Gemini and OpenAI experienced outages independently — a single-provider design
would have caused user-visible downtime in both cases.

## Decision
`backend/extraction/llm_clients.py` exposes a factory, `get_llm(model_key)`,
keyed on four model identifiers: `gemini_cheap`, `gemini_expensive`,
`openai_cheap`, `openai_expensive`. Google **Gemini** (`gemini-3-flash-preview`)
is the primary provider for all requests. On an API error or exhausted retries,
`fallback_model_node` (`backend/extraction/nodes.py`) swaps the provider by
string-replacing `gemini` ↔ `openai` in the current model key, preserving the
cheap/expensive tier, and re-enters the `extract` node:

```python
def fallback_model_node(state):
    current_model = state.get("current_model")
    new_model = current_model.replace("gemini", "openai") if "gemini" in current_model \
        else current_model.replace("openai", "gemini")
    return {"current_model": new_model, "fallback_used": True, ...}
```

`fallback_used` is a one-shot flag — the graph tries the fallback provider
exactly once per request and never fallback-loops back to the original
provider (see `route_after_validate` in ADR-0001).

Both providers are wrapped in LangChain chat clients with
`.with_structured_output(Invoice)` so both return the same Pydantic-validated
shape regardless of provider (Gemini via native structured output,
OpenAI via `method="function_calling"`).

## Consequences

### Positive
- A quota error or outage on the primary provider degrades to "slightly slower,
  possibly different model" instead of a failed upload — the user never sees
  the switch happen except through the SSE progress stream
  (`trying_new_ai` step).
- Structured-output wrapping means the rest of the pipeline (`validate_node`,
  schemas) is provider-agnostic; adding a third provider only touches
  `llm_clients.py` and the fallback string-replace logic.

### Negative / trade-offs
- Fallback is exactly one hop (`gemini → openai` or `openai → gemini`); if both
  providers are down, the request fails after at most 2 provider attempts —
  there is no round-robin across more than two providers.
- The two providers are not equivalent in output quality/latency/cost, so a
  fallback-triggered response may differ subtly from what the primary provider
  would have produced. This is judged an acceptable trade-off against hard
  failure.
- `fallback_model_node`'s string-replace (`current_model.replace("gemini", "openai")`)
  is a naming convention, not a type-checked mapping — a future model-key
  naming change silently breaks fallback routing unless tests catch it.

## Alternatives considered
- **Single provider (Gemini only)** — rejected: no resilience to provider
  outages, which were observed in practice during development.
- **Round-robin / N-provider fallback chain** — deferred: added complexity not
  justified while only two providers are integrated; can be added later by
  generalizing `fallback_model_node` into a provider list.
- **Retry the same provider on failure instead of switching** — rejected for
  `api_error`/`api_config_error` cases specifically, since retrying the same
  provider during an outage or quota exhaustion is unlikely to succeed.
