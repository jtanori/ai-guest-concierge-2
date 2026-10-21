# Phase 0 decisions — founder answers (21 Oct 2026)

Answers to the five blocking questions in the Phase 0 plan review, plus the two approved deviations from the backlog.

---

## Q1 — C18/C22 contradiction. Your diagnosis was right; the eval was wrong, not the fixtures.

This is a defect in **my** artefact, and your recommendation is correct. Fixture text **is** knowledge: a sourced *"we have no charger on the hotel"* is a correct **answer**, not a refusal. v0 would have punished the right behaviour.

**Resolved — you do not need to choose between bad options. `eval-set-v0.1.csv` is in `04-eval/`:**

| Item | v0 | v0.1 |
|---|---|---|
| C18 EV charging | decline | **answer** (MX: none on site; ES: garage has two Type-2 points) |
| C22 pool heated | decline | **answer** (both: not heated; ES adds May–Oct season) |
| **C31** pool water temperature in January | — | **decline** — genuine gap; MX forbids speculating on temperature |
| **C32** accessible-bathroom dimensions | — | **decline** — genuine gap; ES marks `[GAP]` and refers to reception. High-stakes: a wrong dimension is real harm |

**Also added: per-property expected behaviours** (`behaviour_mx` / `behaviour_es`), because whether an item is a gap depends on the property. The scorer now takes `--hotel mx|es` and writes a `language` column, which also resolves your finding #4. Set is **32 canonical + 25 adversarial = 57 items**. v0 is retained for audit and is not edited in place — your instinct to refuse an in-place edit was right.

**Do not** soften the fixture to restore the old expectation. The fixtures are correct; the eval was stale.

## Q2 — Providers

- **Generation:** primary **Anthropic (Haiku-class)**, secondary **OpenAI (mini-class)**.
- **Embeddings:** **OpenAI `text-embedding-3-small` (1536 dims)** — Anthropic has no embeddings endpoint and the schema already says `vector(1536)`.
- Note the asymmetry deliberately: generation fails over **across vendors**, embeddings do not (they are cached at ingestion and a failure there is a slow-path problem, not a guest-facing one).
- **Keys:** create a dedicated dev key on **each** provider with a hard monthly spend cap ($50 is generous for Phase 0). Anthropic + OpenAI both sit behind `src/lib/provider.ts`; nothing else in the codebase may import an SDK directly — that is a CI grep gate alongside the threshold-literal gate.
- The CI smoke test must run with **no keys** (mocked provider). Only the full 57-item run needs real keys; expect cents, not dollars.

## Q3 — Repo and accounts

- **GitHub:** create a **private** repo under your account. `git init` in T01, push, then protect `main`: PR required, CI required, no direct pushes. Solo does not mean unguarded — it means you are the only person who can approve your own PR, so make CI the approver.
- **Accounts you create, I cannot:** Supabase (staging now, prod at Phase 5), Sentry (one project, environment tag), and the two LLM providers.
- **Secrets:** `.env.example` committed with placeholders; `.env.local` gitignored and never committed; GitHub Actions secrets for CI. The service-role key is **never** in the client bundle, never in a `NEXT_PUBLIC_*` variable, and gets its own CI grep gate.

## Q4 — Supabase region

**Confirmed: EU (Frankfurt / `eu-central-1`) for staging and production.** Reasoning, so you can defend it later:

- Spain is in the beachhead and GDPR + AI Act Art. 50 posture are cheapest to satisfy by default than to retrofit.
- The extra ~150 ms to Mexican tenants is **invisible**: guest-perceived latency is dominated by the model call (~2.4 s p50), and webhook acceptance is async anyway. Optimise the LLM path, not the database hop.
- Local Supabase for development, so your own iteration speed is unaffected.
- Mexican guest data stored in the EU is permitted under LFPDPPP with the right privacy notice (cross-border transfer disclosure). **Flag it in the DPA/privacy notice as a legal review item** — not an engineering blocker, and not something to discover at contract signing.
- T66 (per-tenant residency) keeps open the option to move Mexican tenants to a US region later if latency or counsel demands it.

## Q5 — Repo layout

**Approved as proposed**, with three additions:

1. **`docs/DECISIONS.md`** — append-only ADR log (date, decision, why, what it costs). You are the only person who will remember why a threshold is 0.72 in six months, and this is the cheapest possible insurance against re-litigating your own choices.
2. **`prompts/` stays at root as the *seed* source, but the database wins at runtime.** `prompt_versions` is authoritative; the file is what seeds it. Publishing a prompt is eval-gated (plan §2.5.3) — a filesystem edit alone must never change guest-facing behaviour.
3. `docs/` is **read-only reference**. Consider a `docs/.readonly` marker or a CODEOWNERS entry so future-you does not "tidy" the fixtures.

---

## Approved deviations from the backlog

Both of your flags are **approved**. You spotted real sequencing errors:

| Your finding | Verdict |
|---|---|
| **#2 Storage RLS is in T59 (Phase 2) but the Phase 0 gate requires it** | **Approved — pull the storage slice into T02.** Private buckets, path convention, storage policies, 60 s signed-URL RPC and the storage isolation test ship in Phase 0. T59 keeps the *hardening* (rotation, audit of mint calls), not the foundation. The gate is right and the backlog was wrong |
| **#5 T07 depends on T05 but the proxy pack makes it runnable now** | **Approved — dependency satisfied.** T05/T64 matter at eval v1, not v0.1 |
| **#3 paths** | Noted; cosmetic |
| **#6 57.4 vs 57.9** | Fixed in v3.3 |

---

## Two additional founder directives

1. **Do not build the dashboard in Phase 0.** Auth shell and provisioning only. The gate does not require UI, and dashboard work before the eval harness exists is the most common way this kind of project dies with a beautiful product that answers questions badly.
2. **Report at the gate, not at the end.** If the isolation test or the negative-control job fights you for more than a day, surface it — a security test that is hard to write usually means the policy is wrong, and that is worth knowing before Phase 1 builds on it.

## Your negative-control CI job is the best idea in the plan

Dropping a policy and asserting the suite goes red is exactly right, and it is now a permanent requirement, not a nice-to-have: **every security-critical test must be proven to fail when the protection is removed.** Extend it to the storage test and to the service-role grep gate.

---

**Next action:** update the plan-mode assumptions to eval set **v0.1** and proceed with **T01** on my go-ahead. Everything above is now reflected in pack **v3.3**.
