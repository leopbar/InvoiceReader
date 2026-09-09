# ADR-0007: Supabase for managed Postgres, Auth, and Row Level Security

## Status
Accepted

## Context
The application needs a relational database (invoices have normalized
relations to suppliers, line items, and addresses — see `setup_db.sql`), user
authentication, and a way to gate access without hand-rolling a full auth
system (password hashing, session/JWT issuance, email verification) for what
is a solo/small-scale production project.

## Decision
Use **Supabase** as a managed Postgres + Auth + Data API layer:

- Schema (`backend/setup_db.sql`) defines `suppliers`, `invoices`,
  `invoice_items`, `invoice_addresses`, and `user_roles`, with foreign keys and
  `ON DELETE CASCADE` for line items/addresses tied to an invoice.
- Row Level Security (RLS) is enabled on every table
  (`ALTER TABLE ... ENABLE ROW LEVEL SECURITY`).
- Supabase Auth issues JWTs on login; the backend verifies them per-request
  (see ADR-0008) rather than managing its own session store.
- Two Supabase clients are configured (`backend/database.py`): an
  anon-key client (`supabase`) for normal request-scoped operations, and a
  service-role client (`supabase_admin`) used only for admin operations
  (user management, admin-role checks) and never exposed to the frontend.
- Explicit `GRANT` statements are required in the schema (`setup_db.sql`,
  step 8) for Supabase's PostgREST Data API to work — this is a
  platform-specific requirement introduced by Supabase (rolling out from
  2026-05-30 for new projects) and is not optional boilerplate.

## Consequences

### Positive
- No custom auth system to build or maintain (password storage, JWT signing
  keys, refresh-token rotation) — Supabase Auth handles this, and the backend
  only needs to verify tokens.
- RLS is enforced at the database layer, so even a bug in application-level
  authorization logic doesn't automatically mean unrestricted data access —
  defense in depth against a backend logic error.
- Free tier is sufficient for the project's current scale, keeping
  infrastructure cost near zero.

### Negative / trade-offs
- **Current RLS policies are permissive** (`USING (true) WITH CHECK (true)`
  on every table) — see the explicit note in `setup_db.sql` and the README's
  Security Considerations section. This means RLS is enabled but not yet
  doing real per-user data isolation; authorization currently relies on the
  application layer (JWT verification + `user_roles` check in
  `backend/main.py`). This is a known, tracked gap — see the project roadmap
  for per-user RLS policies (`USING (auth.uid() = user_id)`).
- Coupling to Supabase's specific Data API behavior (e.g. the `GRANT`
  requirement above) means a platform-level change in Supabase can silently
  break persistence (`42501` errors) without any code change on our side —
  this already happened once and required the explicit-GRANTs fix.
- Vendor dependency: migrating off Supabase later means replacing both the
  Postgres hosting and the Auth system, not just a connection string.

## Alternatives considered
- **Self-hosted Postgres + custom JWT auth (e.g. FastAPI + `passlib` +
  `python-jose`)** — rejected: significantly more code to build and secure
  correctly (password hashing, token refresh, email verification flows) for
  no functional benefit at this project's scale.
- **Firebase (Firestore + Firebase Auth)** — rejected: the data model is
  relational (invoices → items, addresses, suppliers with foreign keys), which
  fits Postgres naturally; Firestore's document model would require
  denormalization or client-side joins.
