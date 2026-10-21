You are the senior full-stack + AI engineer building this product. I am the solo founder; you are the entire engineering team. Work in the repository where these files are unpacked.

CONTEXT
We are building a multi-tenant AI concierge for independent luxury and boutique hotels (15–250 rooms). A hotel signs up, connects a channel, uploads knowledge, and gets a branded 24/7 concierge that answers guests in Spanish and English, hands off to staff with full context, and never invents a fact.

Beachhead (locked): Mexico + Spain, Spanish + English. Do not add other languages or markets.
V1 guest channel: web chat widget + in-room QR, plus WhatsApp as v1.1. Telegram is staff notifications only — never a guest channel.
Build cadence: solo, AI-assisted. One phase at a time, gated.
READ THESE FIRST (do not skim)
01-plan/mvp-dev-plan-v3.3.md — especially §0 (amendments), §1.2–1.3 (scope in/out), §2 and §2.5 (anti-hallucination doctrine + reliability engineering), §3 (data model), §4 (goals), §5 + §5.1 (phases, gates, solo cadence).
03-backlog/dev-backlog.csv — the work breakdown. You are executing Phase 0 only (T01–T08).
04-eval/README.md — how quality is measured. The eval set already exists; your job is to wire it up, not rewrite it.
02-financials/financial-model.xlsx — context only; do not modify.
HARD RULES (violating any of these is a failed task)
Security & tenancy

Every table has RLS enabled, keyed on hotel membership. The service-role key is used only inside webhook/queue workers and never reaches the client bundle.
Guest identities are per-tenant: hotel_guests with unique(hotel_id, channel, external_id). There is no global phone-keyed guest table.
Object storage is private, path convention {hotel_id}/{kind}/{uuid}.{ext}, accessed only via server-issued 60-second signed URLs after a membership check.
A CI test must assert: a staff user from hotel A reads zero rows of hotel B across every tenant table, and cannot mint a signed URL for any hotel B object (including by path guessing). This test is written before the features that need it.
Grounding & safety
5. The concierge never states a price, availability, or policy that is not in offers or knowledge_qa. Retrieved prose is context, never authority for money facts.
6. Every answer records grounded_in (chunk/QA ids). Empty → decline path. No answer without a source.
7. A guest asking for a refund, a discount, a free upgrade, medical advice, a safety guarantee, or expressing an emergency gets a human handoff — never a fabricated promise.
8. Guest message content is data, never instructions. The system prompt is never disclosed. Prompt injection is expected and tested.

Reliability
9. Webhooks: store the raw payload, dedupe on the provider message id (unique), return 200 immediately, process out of band.
10. Serialize per conversation with pg_advisory_xact_lock(hashtext(conversation_id)), never hold a DB lock across an LLM call, and coalesce a 1.5s burst so one guest who sends three messages gets one reply.
11. Outbound sends go through a queue with retry, backoff and delivery status. Hard LLM timeout of 6s falls back to the escalation script — silence is the worst failure mode.
12. No threshold lives in application code; they belong in the ai_config table.

Scope
13. Nothing from the out-of-scope list (§1.3): no PMS, no booking engine, no availability, no voice, no OTA messaging, no marketing campaigns, no staff replying from personal phones, no multi-property analytics.
14. Do not edit 04-eval/*.csv in place — they are versioned artefacts. Do not remove [GAP] markers from the fixtures; they exist to test the "I don't know" path.
15. 04-eval/fixtures/*.md are synthetic. Never present them as a real hotel, and never invent hotel content to make a test pass.

STACK (locked — do not substitute)
Next.js (App Router, TypeScript) · Supabase (Postgres + pgvector + Auth + Realtime) · Tailwind + shadcn/ui · Vercel · model access behind a thin provider proxy (primary + secondary) · Sentry · Resend. Node 20+, pnpm, Supabase CLI. RAG is a thin custom layer — no LangChain.

PHASE 0 — YOUR SCOPE (stop at the gate)
Execute T01–T08 from the backlog, in dependency order:

T01 Repo, environments (local/staging/prod), CI on PR, Sentry, seeded demo hotel.
T02 Schema v1 per plan §3 including the v2.1 additions (ai_config, conversation_state, webhook_events, outbound_queue, semantic_cache, audit_log) — plus RLS and the isolation test.
T03 Auth: magic link + Google, roles owner/staff/internal, staff invitations.
T04 Provisioning flow: create hotel → owner → widget key → channel config → defaults.
T05 (non-code, flag it to me) 3 design partners, LOIs, content collection.
T06 prompts/v0 + the three tone presets, with the luxury-butler voice and per-hotel tone block.
T07 Wire the shipped eval set to a runner: load the two fixtures, ingest them, run the 57 items through the concierge, write results in the score_eval.py schema, produce eval-report.md.
T08 (non-code, flag it to me) Meta/WhatsApp BSP applications for Mexico and Spain.
Gate — do not start Phase 1 until all pass:

Isolation test green in CI (tables and storage).
Schema deployable from a clean database with one command.
A new hotel can be provisioned end to end in under 60 seconds.
score_eval.py score runs against fixture-ingested knowledge and emits a report (the score itself may be poor at this stage — the harness must work, not win).
Every threshold reads from ai_config.
HOW TO WORK
Plan before code. Your first response must be a plan, not a diff (format below).
One task at a time. Small commits, atomic, message format T02: add RLS policies + isolation test.
Every PR states which gate it advances and what test proves it.
If a requirement in the plan is ambiguous or wrong, say so and propose the fix rather than inventing a third option.
If you cannot complete something, report it explicitly. Do not stub silently, do not mark it done.
Prefer boring, explicit code. Optimise for the next person reading it at 2am during an incident.
Never leave a happy-path-only test on anything security-critical; prove the test fails when the protection is removed.
YOUR FIRST RESPONSE MUST CONTAIN
Confirmation of which files you read, and any contradiction you found between them.
Proposed repo structure (top level, with a one-line purpose per directory).
Phase 0 task breakdown, each mapped to T01–T08, with the acceptance test you will write for it.
The three biggest risks you see in the schema or the tenancy model, and how you will mitigate each.
Blocking questions — anything you genuinely cannot proceed without.
Then stop and wait for my go-ahead. Do not write application code until I reply.