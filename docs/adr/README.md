# Architecture Decision Records — InvoiceReader

This directory records the significant architectural decisions made while building
InvoiceReader, in the lightweight [ADR](https://adr.github.io/) format popularized by
Michael Nygard: **Title → Status → Context → Decision → Consequences**.

Each ADR is immutable once accepted. If a decision is later reversed, write a new ADR
that supersedes the old one instead of editing history — leave the old file's Status
updated to `Superseded by ADR-00NN`.

## Index

| # | Title | Status | Area |
|---|-------|--------|------|
| [0001](0001-langgraph-stateful-extraction-pipeline.md) | Use LangGraph for a stateful extraction pipeline instead of a single LLM call | Accepted | Extraction core |
| [0002](0002-multi-llm-provider-with-automatic-fallback.md) | Multi-LLM provider strategy — Gemini primary, OpenAI fallback | Accepted | Extraction core |
| [0003](0003-complexity-based-cost-aware-model-routing.md) | Complexity-based, cost-aware model routing | Accepted | Extraction core |
| [0004](0004-pydantic-schema-validation-at-the-boundary.md) | Enforce Pydantic schema validation at the LLM boundary | Accepted | Data integrity |
| [0005](0005-targeted-per-field-retry-over-full-re-extraction.md) | Targeted per-field retry instead of full re-extraction | Accepted | Extraction core |
| [0006](0006-sse-streaming-for-realtime-pipeline-progress.md) | Server-Sent Events for real-time pipeline progress | Accepted | API design |
| [0007](0007-supabase-for-postgres-auth-and-rls.md) | Supabase for managed Postgres, Auth, and Row Level Security | Accepted | Infrastructure |
| [0008](0008-stateless-jwt-based-rbac.md) | Stateless JWT-based role access control (admin/user) | Accepted | Security |
| [0009](0009-react-typescript-vite-tailwind-frontend.md) | React + TypeScript + Vite + Tailwind for the frontend | Accepted | Frontend |
| [0010](0010-dockerized-deploy-via-github-actions-to-vps.md) | Dockerized deployment via GitHub Actions SSH to a single VPS | Accepted | Infrastructure |

## Template

```markdown
# ADR-00NN: Title

## Status
Accepted | Proposed | Superseded by ADR-00NN

## Context
What forces are at play (technical, business, constraints)?

## Decision
What did we decide, stated as a plain assertion?

## Consequences
### Positive
### Negative / trade-offs

## Alternatives considered
```
