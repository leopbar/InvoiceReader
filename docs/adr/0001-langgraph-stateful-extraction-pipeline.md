# ADR-0001: Use LangGraph for a stateful extraction pipeline instead of a single LLM call

## Status
Accepted

## Context
Invoice extraction is not a single deterministic transformation — LLMs hallucinate
fields, hit provider outages, and sometimes return output that fails schema
validation. A naive implementation would look like:

```
User upload → LLM call → trust the output → save
```

This has no way to recover from a partially wrong response (e.g. valid supplier
name but malformed total), no place to insert a retry, and no way to switch
providers mid-request. Every failure mode collapses into "extraction failed,"
even when 90% of the fields were extracted correctly.

We needed a way to express extraction as a sequence of steps with explicit
branching on outcome (success / field-level failure / API failure), where each
step can be tested, logged, and observed independently.

## Decision
Model the extraction pipeline as an explicit state machine using **LangGraph**
(`backend/extraction/graph.py`), with typed state (`ExtractionState`,
`backend/extraction/state.py`) threaded through named nodes:

```
preprocess_document → select_model → extract → validate
                                         ├─(valid)──────────────→ finalize_success
                                         ├─(field errors, retries left)─→ targeted_retry ─→ validate
                                         ├─(api error / retries exhausted)→ fallback_model ─→ extract
                                         └─(all paths exhausted)─→ finalize_error
```

The branching logic lives in one function, `route_after_validate`, which is the
single place that decides what happens next based on `validation_errors`,
`failed_fields`, `attempts`, `max_attempts`, and `fallback_used` in state.

## Consequences

### Positive
- Retry/fallback/success paths are explicit edges in a graph, not nested
  `try/except`/`if` chains — the routing table in `route_after_validate` is
  independently unit-testable (`tests/test_graph_routing.py`).
- Each node is a plain function of `ExtractionState → dict`, so nodes can be
  unit-tested in isolation (`tests/test_nodes.py`) without invoking an LLM.
- The same graph powers both the synchronous endpoint (`run_extraction`) and the
  streaming endpoint (`run_extraction_streaming`) — the only difference is a
  `progress_callback` injected into initial state.
- New failure-handling strategies (e.g. a third provider) are new nodes/edges,
  not a rewrite of a monolithic function.

### Negative / trade-offs
- Adds a dependency (`langgraph`) and a mental model (state machines) that a
  contributor unfamiliar with the library has to learn before touching
  `extraction/`.
- State is a loosely-typed `dict`-like `TypedDict`; correctness of what each
  node reads/writes is enforced by convention and tests, not the type checker.
- Debugging requires reasoning about accumulated state across multiple node
  invocations rather than a single stack trace.

## Alternatives considered
- **Single LLM call, trust output** — rejected: no recovery path, fails hard on
  any bad field or transient provider error.
- **Plain LangChain chain with manual `if` branching** — rejected: conditional
  retry/fallback logic becomes nested and hard to test as branches multiply;
  LangGraph's conditional edges make the state transitions declarative.
- **Custom hand-rolled state machine** — rejected: would reimplement what
  LangGraph already provides (state typing conventions, conditional edges,
  compiled graph execution), for no clear benefit at this scale.
