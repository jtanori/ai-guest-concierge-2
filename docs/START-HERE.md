# AI Concierge for Luxury Hotels — MVP Pack v3.3

**Prepared:** 21 Oct 2026 · **Status:** decisions locked, ready to execute
**Scope:** Americas + Europe footprint · **Beachhead locked: Mexico + Spain** · **Build: solo, AI-assisted**

---

## Decisions locked (21 Oct 2026)

| Decision | Locked value | Consequence |
|---|---|---|
| **Build** | **Solo, AI-assisted tooling** | ~12 weeks pure build; **~14–15 weeks elapsed** at 4 build-days/week (§5.1). Breakeven at ~19 properties. Funding requirement **~$64k base / ~$81k conservative** (~$105k buffer) |
| **Beachhead** | **Mexico + Spain, Spanish + English** | One language pair covers two WhatsApp-dominant markets and two continents. 3,742 + 14,103 serviceable properties — the base case needs 31 of them |
| **Cadence** | Mon–Thu build · **Friday selling, never skipped** | The Friday rule is what makes 14–15 weeks honest rather than wishful (§5.1) |

**First action:** Day 1 of Phase 0 — start from the shipped eval pack in `04-eval/` (nothing is blocked on hotel access), and submit both Meta/BSP applications for Mexico and Spain.

---

## Read in this order

| # | File | Time | Why |
|---|---|---|---|
| 1 | `01-plan/mvp-dev-plan-v3.3.md` | 25 min | The plan. Start at **§0** (what changed and why), then **§1.4–1.5** (market and per-market requirements), **§5.1** (solo cadence), **§7** (economics) |
| 2 | `02-financials/financial-model.xlsx` | 15 min | The evidence behind §7. Open `03_Unit_Economics` and `09_Market_Sizing` first. All blue cells are inputs |
| 3 | `03-backlog/dev-backlog.csv` | 10 min | 71 tasks with acceptance criteria, dependencies, and an AI-leverage factor per task. Imports to Linear/Jira/Sheets |
| 4 | `04-eval/README.md` | 10 min | How quality is measured — scorer, gates, v0.1 correction, and the replacement protocol |

---

## Key numbers (all computed live in the workbook)

| | Value |
|---|---|
| Serviceable market (Americas + Europe) | 23,046 properties |
| Blended ARPU / property / month | $439.50 |
| Blended gross margin | 84.6% |
| Gross profit / property / month | $371.69 |
| Properties to cover solo fixed opex | **~19** |
| Base case: month-24 properties / ARR | 31 / $163k |
| Peak funding requirement (base / conservative) | **$64.0k / $80.9k** |
| Recommended cash buffer (conservative + 30%) | ~$105k |
| Dev-days to pilot (unaided → AI-assisted) | 90.2 → **57.9** |
| **Elapsed to pilot, solo, at 4 build-days/week** | **~14–15 weeks** |

---

## What this pack answers

| Question | Where |
|---|---|
| Is the market big enough? | §1.4 + `09_Market_Sizing` — 57k target properties, 23k serviceable, $121.5M ARR pool; the base case needs 0.13% of it |
| Does a single property make money? | §7.1 — 83–87% gross margin at every size, payback under 4 months |
| How many properties to break even? | §7.2 — ~19 properties on a solo cost base |
| How much cash is needed? | §7.5 — $64k base / $81k conservative peak; ~$105k recommended buffer |
| How long, realistically, alone? | §5.1 — 12 weeks of build, 14–15 weeks elapsed once one day a week goes to selling |
| What stops a hallucination reaching a guest? | §2 doctrine + §2.5 reliability + the eval pack in `04-eval/` |
| What if we have no hotel access yet? | §9.1 — the proxy eval pack; fixtures carry ~6–8 weeks while partner recruitment runs in parallel |

---

## What is deliberately NOT in this pack

- **`mvp-evaluation-and-dev-plan.md` (v1)** — superseded and actively contradictory (it argues Telegram-first, which the plan reverses). Kept in the working workspace, excluded here so reviewers don't read two strategies.
- **The original 2–4 week MVP proposal.** Its assumptions are answered point by point in §0.
- **Sales and marketing collateral.** Not written yet; this pack is the build and business case only.

---

## Companion sources (`05-source/`)

`build_model.py` regenerates `financial-model.xlsx` (needs `openpyxl`); `cache_values.py` injects calculated values so the workbook reads correctly in pandas, Google Sheets and preview panes while keeping formulas live for Excel (needs `formulas`). Run them in that order to rebuild. Not required to use the workbook.

---

## Honest limitations, stated up front

1. **No hotel is signed yet.** Market sizing uses published counts; engagement, churn, conversion and support hours are estimates. The eval set is built on published conversation data, not this product's traffic.
2. **Labour deflection alone does not justify the price** (§7.6C): it covers 8–19% of the subscription. Renewal depends on after-hours coverage, language reach and attributable upsell — instrument all three from day one.
3. **AI tooling shortens the build, not the business.** It does not recruit partners, do native-language tone QA, or make security-critical code safe without review.
4. **The six-week story is dead.** Solo, this scope is **~14–15 weeks elapsed**. Under-promising is the competitive advantage here.
5. **Solo means no second pair of eyes.** The plan buys an external security review ($2,000) before the first real guest, and treats the eval harness — not memory — as the authority on quality.
6. **The clock that matters is partner recruitment, not code.** Fixtures carry the build for ~6–8 weeks; past that, no signed property means no pilot and no revenue, and §7.4 stops being conservative and becomes fictional.
