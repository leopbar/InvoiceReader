# ADR-0009: React + TypeScript + Vite + Tailwind for the frontend

## Status
Accepted

## Context
The frontend needs to: render a live pipeline-progress visualization driven by
an SSE stream (ADR-0006), manage auth/session state and admin-role–gated
routes/UI, support a customizable, high-column-count data table (30+ optional
columns with `localStorage`-persisted preferences), and support export
(CSV/TSV/clipboard) — all with type safety matching the backend's Pydantic
models.

## Decision
- **React 19** with **TypeScript 5.8** for the UI layer and end-to-end type
  safety with the backend's Pydantic schemas.
- **Vite 6** as the build tool/dev server, for fast HMR during development
  and an optimized production build (served as static files via
  `Dockerfile.frontend`/Nginx — see ADR-0010).
- **Tailwind CSS 4.1** (oxide compiler) for styling, utility-first rather than
  a component library, keeping bundle size and styling conventions
  predictable across a UI with many small stateful pieces (progress steps,
  column pickers, toasts).
- **React Router 7** for routing between upload/history/admin pages.
- **React Context** (`AuthContext`) for auth/session and admin-role state,
  rather than a larger state-management library — the app's cross-cutting
  state surface is small (current user, role, session).
- **Axios** for standard REST calls and the native `fetch` streaming body
  reader for the SSE endpoint (needed because `EventSource` cannot send a
  custom `Authorization: Bearer` header, which the streaming upload endpoint
  requires per ADR-0008).
- `lucide-react`, `react-dropzone`, `react-hot-toast` for icons, drag-and-drop
  upload, and toast notifications respectively — small, focused libraries
  rather than a full UI kit.

## Consequences

### Positive
- Full type safety from Pydantic (backend) to TypeScript (frontend) interface
  contracts eliminated an entire class of "field doesn't exist" runtime bugs
  in practice.
- Vite's dev server and Tailwind's utility classes keep iteration fast for a
  UI that's mostly custom (progress visualization, dynamic column tables)
  rather than assembled from a component library's defaults.
- React Context is sufficient for the app's actual state complexity; avoids
  the overhead of introducing Redux/Zustand for a small, mostly-local state
  surface.

### Negative / trade-offs
- Using `fetch` instead of `EventSource` for the SSE stream means giving up
  `EventSource`'s built-in auto-reconnect — reconnection on a dropped stream
  has to be handled manually if ever needed.
- Column-visibility preferences are stored in `localStorage`, which is
  per-browser/per-device, not synced across a user's sessions or devices.
- No component library means more custom CSS/markup to build and maintain
  for common patterns (modals, dropdowns) versus adopting something like
  Radix or shadcn/ui.

## Alternatives considered
- **Next.js** — rejected: the app is a client-rendered SPA behind a separate
  FastAPI backend; server-side rendering/routing conventions from Next.js
  aren't needed and would add deployment complexity (ADR-0010 already
  separates frontend/backend as independent containers).
- **Redux/Zustand for state management** — rejected: current state needs
  (auth/session, admin role) are adequately served by React Context without
  the extra dependency and boilerplate.
