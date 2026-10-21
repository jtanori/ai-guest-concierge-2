# Changelog

## v3.3 — 21 Oct 2026 — eval set v0.1 (correction raised by the Phase 0 plan review)
- **Fixed a defect in the eval pack.** v0 marked EV charging (C18) and pool heating (C22) as deliberate knowledge gaps, but both fixtures answer them — so a correct, grounded "we have no charger in the hotel" was scored as a failure. The eval was punishing the right behaviour.
- v0.1 makes both **answerable** and adds two **genuine** gaps: pool water temperature in January (C31) and accessible-bathroom dimensions (C32).
- Added **per-property expected behaviours** (`behaviour_mx` / `behaviour_es`), because whether an item is a gap depends on the property. Scorer gains `--hotel mx|es` and a `language` column.
- Set is now **32 canonical + 25 adversarial = 57 items** (was 55). References updated in the plan, eval README and backlog (T07/T15/T31).
- Fixed the cosmetic 57.4 vs 57.9 build-day inconsistency.
- v0 retained for audit; never edited in place.

## v3.2 — 21 Oct 2026 — decisions locked
- **Build locked: solo with AI-assisted tooling.**
- Added **§5.1 solo operating cadence**: Mon–Thu build, Friday selling (never skipped), 20-minute gate check at week end, 30-minute daily eval run.
- **Elapsed time corrected to ~14–15 weeks.** 57.9 AI-adjusted build-days at 5 days/week is 11.6 weeks; one sales day a week makes it 14.5. Publishing 12 weeks while also selling would repeat the optimism this plan has already corrected twice.
- **Beachhead locked: Mexico + Spain**, Spanish + English.
- Added solo safeguards: **contracted external security review** ($2,000, now inside the $17,000 pre-launch capital), bus-factor discipline (runbook a contractor could execute, infra as code), eval-harness-as-authority.
- Added risks **R25** (solo bus factor) and **R26** (selling and building on the same calendar).
- Funding updated: base peak **$63,961**, conservative **$80,867**, recommended buffer **~$105k**, 14.6 months of opex.
- Backlog 70 → **71 tasks** (T71 external security review).

## v3.1 — 21 Oct 2026
- Added the **proxy eval pack** (`04-eval/`): 30 canonical + 25 adversarial items in ES/EN, frequency-weighted from published conversation data, two synthetic fixtures with deliberate knowledge gaps, runnable scorer.
- Added §9.1: what the proxy does and does not prove, and the v0 → v0.5 → v1 replacement protocol.
- Backlog: T07 redefined as eval set v0; T64 as eval set v1.

## v3.0 — 21 Oct 2026
- Added market research across the Americas and Europe (§1.4) and `09_Market_Sizing`: 57,371 target properties, 23,046 serviceable, $121.5M ARR pool.
- Per-market channel reality: WhatsApp ~90% in MX/ES/BR but **~25–30% in the US**, so North America requires SMS/RCS (T69).
- Added **EU AI Act Art. 50** (in force 2 Aug 2026) plus GDPR/LGPD/LFPDPPP/VAT requirements (§1.5).
- Recommended wave sequencing: Mexico + Spain → Brazil → US/Canada → DACH/Italy.
- Timeline model for AI-assisted development: 90.2 dev-days unaided → 57.4 adjusted.

## v2.1 — 21 Oct 2026
- Response to external technical review (7.8/10). Added §2.5 Reliability engineering: per-conversation advisory locks with 1.5s coalescing, per-stage latency budget with streaming and semantic caching, config-not-constants, provider failover, object-storage RLS, provider contract tests.
- Added sensitivity tables F/G/H: margin vs support load × labour rate, high-touch onboarding, token inflation.
- Added 8 tasks; schedule corrected to reflect them.

## v2.0 — 21 Oct 2026
- First amended plan. Six amendments: web+QR as the v1 guest channel; Coverage Score as the hero feature; per-tenant identities and RLS; shadow mode before autonomy; async idempotent webhooks; realistic timeline.
- Added the financial model, backlog, risk register, unit economics and funding requirement.

## v1 — 21 Oct 2026 (excluded from this pack)
- Evaluation of the original proposal. Superseded; argues Telegram-first, which v2.0 reverses.
