# ADR-0010: Dockerized deployment via GitHub Actions SSH to a single VPS

## Status
Accepted

## Context
The project needs a deployment path that's simple to operate for a
small/solo-maintained production app, reproducible across the dev/VPS
environment gap, and cheap. It also needs to keep secrets (API keys, Supabase
service-role key, admin bootstrap credentials) out of source control while
still being usable by an automated deploy step.

## Decision
- **Backend and frontend are independently containerized**
  (`Dockerfile.backend`, `Dockerfile.frontend`), orchestrated with
  `docker-compose.yml`. The backend binds to `127.0.0.1:8000` and the frontend
  (a static build served by Nginx, `nginx-frontend.conf`) to
  `127.0.0.1:3001` — both loopback-only, with an external reverse proxy
  (`nginx/`) expected to terminate public traffic and route to these ports.
  Frontend build-time Supabase/API config is passed as Docker build `args`
  (`VITE_SUPABASE_URL`, `VITE_SUPABASE_KEY`, `VITE_API_URL`), since Vite
  inlines `VITE_*` env vars at build time, not runtime.
- **Deployment is triggered by a push to `main`** via a GitHub Actions
  workflow (`.github/workflows/deploy.yml`) using `appleboy/ssh-action` to
  run a script on the VPS over SSH (mirrored locally as `deploy.sh` for
  manual/reference use):
  1. `git fetch`/`reset --hard origin/main` (or clone if not yet present) into
     `/app/InvoiceReader` on the VPS.
  2. Write the `VPS_ENV` GitHub Actions secret to `.env`, then derive
     `backend/.env` by filtering out `VITE_`-prefixed and comment/blank lines
     (frontend vars are baked in at Docker build time instead, per above).
  3. `docker compose build --no-cache && docker compose up -d --remove-orphans`,
     then `docker image prune -f` to reclaim disk space from superseded
     image layers.
- All secrets (`GOOGLE_API_KEY`, `OPENAI_API_KEY`, Supabase keys, admin
  bootstrap credentials, the VPS SSH private key) live in GitHub Actions
  secrets and are never committed — consistent with the "no credentials in
  source code" principle applied elsewhere in the project (ADR-0007, ADR-0008).

## Consequences

### Positive
- `git push` to `main` is the entire deploy operation from a developer's
  perspective — no manual SSH session or manual container rebuild step in the
  common case.
- Docker containerization means the VPS environment (Python/Node versions,
  system libraries) matches what's defined in the Dockerfiles, not whatever
  happens to be installed on the host — eliminates "works on my machine"
  drift between dev and production.
- `--no-cache` on every deploy build trades build time for guaranteeing the
  image reflects the latest `main`, not a stale cached layer.
- Loopback-only container ports (`127.0.0.1:*`) mean the reverse proxy is the
  only public entry point, reducing the exposed attack surface.

### Negative / trade-offs
- **Single VPS, no redundancy** — a deploy failure, VPS outage, or a bad
  `git reset --hard` mid-deploy has no failover; `docker compose up -d` does
  cause a brief service interruption during the swap (not a zero-downtime
  blue/green deploy).
- **`git reset --hard origin/main` on the deploy target** — matches expected
  behavior for a push-to-deploy model, but means the VPS working tree is
  fully disposable/non-authoritative by design; any manual on-VPS change
  would be silently discarded on the next deploy (this is intentional, but
  worth stating explicitly).
- **No automated rollback** — reverting a bad deploy means pushing a revert
  commit to `main` and waiting for the next deploy cycle, or manually SSHing
  in; there's no one-click "redeploy previous image" step.
- **No CI gate before deploy** — the workflow deploys directly on push to
  `main` with no test/build-check step in between; a broken commit on `main`
  reaches production immediately. (The project does have a pytest suite —
  see the README's Testing section — but it is not currently wired into the
  deploy workflow as a gate.)
- `docker compose build --no-cache` on every push means every deploy pays
  full image rebuild cost (no layer cache reuse), trading deploy speed for
  freshness guarantees.

## Alternatives considered
- **Managed PaaS (Render, Railway, Fly.io, etc.)** — rejected for this
  project's stage: a single low-cost VPS is cheaper and sufficient at current
  scale; a PaaS would reduce operational surface (zero-downtime deploys,
  managed TLS/scaling) at a recurring cost premium, and is worth revisiting if
  traffic/reliability requirements grow.
- **Kubernetes** — rejected: orchestration overhead unjustified for a
  two-container app on a single host.
- **Manual deploy (SSH + manual `docker compose` commands)** — rejected:
  what the project effectively had before this ADR's automation; error-prone
  and undocumented compared to a scripted, secret-managed GitHub Actions
  workflow.
