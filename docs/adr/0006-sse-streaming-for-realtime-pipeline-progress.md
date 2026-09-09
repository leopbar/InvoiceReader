# ADR-0006: Server-Sent Events for real-time pipeline progress

## Status
Accepted

## Context
The extraction pipeline (ADR-0001) can take several seconds — preprocessing,
one or two LLM calls, possible retries, possible provider fallback. A plain
request/response upload leaves the UI frozen with no feedback for the entire
duration, which reads as unresponsive or broken even when it's working
correctly, and gives the user no visibility into *why* a request is slow (a
transient provider fallback looks identical to a hang).

## Decision
Expose a second upload endpoint, `POST /api/upload/stream`
(`backend/main.py`), that runs the LangGraph pipeline in a background thread
and streams progress as Server-Sent Events:

- The pipeline thread pushes `{"type": "progress", "step": ..., "detail": ...}`
  onto a `queue.Queue` from each node via a `progress_callback` injected into
  graph state (`_emit()` in `nodes.py`; see ADR-0001).
- An `async def event_generator()` drains the queue via
  `loop.run_in_executor` (so the blocking `queue.get` doesn't block the event
  loop) and yields each item as `data: {...}\n\n`.
- A 120-second `queue.get(timeout=...)` guards against a hung pipeline thread;
  timing out emits an `error` event and closes the stream.
- The final event is `{"type": "result", "data": {...}}`, carrying the same
  payload the non-streaming endpoint returns.
- Response headers set `Cache-Control: no-cache` and
  `X-Accel-Buffering: no` to prevent proxy/Nginx buffering from delaying
  delivery.

The synchronous `POST /api/upload` endpoint is kept alongside the streaming one
for callers that just want a single response (e.g. scripts, tests).

## Consequences

### Positive
- The frontend can render each pipeline step (`reading`, `sending_to_ai`,
  `waiting_for_ai`, `ai_failed`, `trying_new_ai`, `preparing_data`) as it
  happens, including visualizing a provider fallback transition instead of it
  looking like a stall.
- SSE is one-directional and works over plain HTTP with no extra protocol
  (unlike WebSockets), which keeps the Nginx/reverse-proxy configuration
  simple (`X-Accel-Buffering: no` is the only special case).
- Running the pipeline in a background thread with a queue decouples the
  synchronous LangGraph execution (`graph.invoke`, which blocks) from the
  async FastAPI event loop.

### Negative / trade-offs
- Two upload endpoints (`/api/upload` and `/api/upload/stream`) do the same
  underlying work through two separate call paths (`run_extraction` vs.
  `run_extraction_streaming`), which have to be kept behaviorally consistent.
- One `daemon=True` thread per in-flight streaming upload with no worker pool
  or concurrency cap — under heavy concurrent load this scales threads
  linearly with concurrent uploads.
- SSE is one-way; there's no way for the client to cancel an in-flight
  extraction once started, only to stop listening.

## Alternatives considered
- **No progress feedback (synchronous only)** — rejected: user testing/dev
  experience showed the same pipeline "feels twice as fast" when progress is
  visible, even at identical total latency.
- **WebSockets** — rejected: bidirectional communication isn't needed for a
  one-way progress stream, and SSE has simpler reverse-proxy/CDN semantics
  (plain HTTP, auto-reconnect built into the browser's `EventSource`, though
  the current frontend consumes it via `fetch` streaming rather than
  `EventSource` since it needs to send an `Authorization` header).
- **Client-side polling of a job-status endpoint** — rejected: adds a
  persistence requirement (job state store) and polling latency/overhead for
  a pipeline that already completes in seconds.
