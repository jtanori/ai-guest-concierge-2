# Decision log (append-only)

Format per entry: **date · decision · why · cost**. Never rewrite history — a correction is a new
entry that supersedes the old one. This file exists because a solo builder is the only person who
will remember why a threshold is 0.72 in six months (R25, bus-factor discipline).

---

## ADR-0001 — LLM providers: Anthropic primary, OpenAI secondary; embeddings OpenAI-only

**Date:** 21 Oct 2026 (founder decision, PHASE-0-DECISIONS.md Q2)
**Decision:** Generation — primary Anthropic (Haiku-class), secondary OpenAI (mini-class).
Embeddings — OpenAI `text-embedding-3-small` (1536 dims), no failover vendor.
**Why:** Founder's call. Anthropic has no embeddings endpoint; the schema pins `vector(1536)`.
Cross-vendor failover protects the guest-facing generation path; embeddings are cached at
ingestion, so an embedding outage is a slow-path (re-embed) problem, not a guest-facing one.
**Cost:** Two vendor SDKs, both behind `src/lib/provider.ts` only (CI grep gate: no SDK import
elsewhere). Embedding failover = re-embed job, not another vendor. Dev keys capped at $50/month
per provider.

## ADR-0002 — eval-set-v0.1 `kb_source` is advisory; strict source-class only for money facts

**Date:** 21 Oct 2026 (raised in Phase 0 plan review; founder approved, PHASE-0-DECISIONS.md Q1)
**Decision:** The eval runner treats `kb_source` in `eval-set-v0.1.csv` as advisory. Groundedness
requires a cited source id that resolves to that hotel's knowledge (`knowledge_qa`, `offers`, or a
retrieved `knowledge_chunks` id). Strict source-class enforcement applies **only** to
`answer_from_structured_only` items, whose facts must come from `offers`/`knowledge_qa`.
**Why:** C18/C22 carry `answer_type=qa` but `kb_source=knowledge_documents`; the ES fixture
answers them from `knowledge_qa` while MX answers from prose. Enforcing `kb_source` literally
would fail correct behaviour on one property or the other. `04-eval/*.csv` are versioned
artefacts and are not edited in place — the runner, not the CSV, absorbs the inconsistency.
**Cost:** The runner is one notch looser on prose-expected items; compensated by the strict money-fact
rule (doctrine §2.1) and by `grounded_in` id resolution, which still blocks unsourced answers.

## ADR-0003 — Single Next.js app, no monorepo; Supabase CLI NOT vendored

**Date:** 21 Oct 2026 (amended 22 Oct 2026 before first push)
**Decision:** One Next.js (App Router, TypeScript) app at the repo root — no pnpm workspace, no
packages/ tree. **Correction (22 Oct):** the Supabase CLI is *not* a devDependency — the binary is
large and platform-specific. Local dev requires a globally installed CLI
(`supabase start`/`db reset`); CI installs it via `supabase/setup-cli@v1`. Documented as a
prerequisite in DEVELOPMENT.md. The vendoring idea was reversed during T01 implementation:
a devDependency CLI adds install weight everywhere, while CI already documents its own
sanctioned install path.
**Cost:** The embeddable widget (Phase 2) must live inside this app as routes/files, not a separate
package. A new contributor must install the Supabase CLI once (one command, per-platform).
Revisit only if a second deployable target appears.
