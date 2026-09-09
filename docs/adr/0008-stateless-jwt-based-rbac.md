# ADR-0008: Stateless JWT-based role access control (admin/user)

## Status
Accepted

## Context
The application distinguishes two roles — regular users (upload/view/export
invoices) and admins (also manage other users) — and every API endpoint except
health/root needs to reject unauthenticated requests. The backend is stateless
(no server-side session store), so authentication has to be verifiable from
the request alone.

## Decision
Two FastAPI dependencies in `backend/main.py` gate every protected route:

```python
def verify_token(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing or invalid Bearer token")
    token = authorization.split(" ")[1]
    user_res = supabase.auth.get_user(token)   # validated against Supabase Auth
    if not user_res or not user_res.user:
        raise HTTPException(401, "Invalid token")
    return user_res.user

def verify_admin(user = Depends(verify_token)):
    role_res = supabase_admin.table("user_roles").select("role").eq("user_id", user.id).execute()
    if not role_res.data or role_res.data[0]["role"] != "admin":
        raise HTTPException(403, "Forbidden: Admin access required")
    return user
```

- Every data-touching endpoint (`/api/upload`, `/api/upload/stream`,
  `/api/save`, `/api/invoices*`) depends on `verify_token`.
- User-management endpoints (`GET/POST /api/users`, `DELETE /api/users/{id}`)
  depend on `verify_admin`, which composes `verify_token` and then checks the
  `user_roles` table using the **service-role** client (`supabase_admin`),
  never the anon client.
- An explicit self-deletion guard rejects an admin deleting their own account:
  `if target_id == admin_user.id: raise HTTPException(400, "Cannot delete yourself")`.
- Bearer format is validated strictly — non-`Bearer` auth headers (e.g. Basic
  auth) and missing headers are rejected before any token verification call.
- In production (`ENVIRONMENT=production`), FastAPI's auto-generated
  `/docs` and `/redoc` are disabled (`docs_url=None, redoc_url=None`) to avoid
  advertising the API surface.

## Consequences

### Positive
- No server-side session state to manage or invalidate — token verification
  is a single call to Supabase Auth per request, so the backend can scale
  horizontally without shared session storage.
- Role checks always hit the `user_roles` table live (not a claim embedded
  in the JWT), so revoking admin access takes effect immediately on the next
  request rather than waiting for token expiry.
- The admin-only path is double-gated: it needs both a valid token *and* a
  separate database check, so a bug that only checks token validity can't
  accidentally grant admin actions.

### Negative / trade-offs
- Every protected request makes at least one round-trip to Supabase Auth
  (`get_user`) and admin requests make a second round-trip to `user_roles` —
  there's no local caching/short-lived verification, so backend latency is
  coupled to Supabase Auth's latency on every single request.
- `verify_admin`'s failure handling logs the traceback and returns a generic
  403 for *any* exception (including transient Supabase errors), which is
  safe but can mask real infrastructure problems as "Forbidden" from the
  client's perspective.
- Role data (`user_roles`) currently has an `USING (true)` RLS policy (see
  ADR-0007) — application-layer checks are the actual enforcement boundary
  today, not the database.

## Alternatives considered
- **Encode role directly in the JWT custom claims** — rejected for now:
  would avoid the extra `user_roles` lookup per admin request, but requires
  configuring Supabase custom claims/hooks and accepting that a role change
  doesn't take effect until the token is refreshed; the current design
  trades a bit of latency for immediate revocation.
- **API-key based auth instead of JWT** — rejected: doesn't map to
  per-user identity or integrate with Supabase's existing user/session
  model.
