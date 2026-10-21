# AI Concierge for Luxury Hotels — Development Plan v2
### Amended for the findings in the review · includes per-size economics and the 24-month financial run

**Version 3.3 · 21 Oct 2026 · decisions locked** — solo build with AI-assisted tooling; beachhead **Mexico + Spain**. Supersedes v1, v2.0, v2.1, v3.0 and v3.1. Scheduling and the funding requirement now reflect a solo operating cadence (§5.1).
**Companion file:** `financial-model.xlsx` (live model — every number below is a formula in that workbook)
**Companion file:** `dev-backlog.csv` (71 sequenced tasks, each with an AI-leverage factor and an AI-adjusted duration)

---

## 0. What changed from v1, and why

The v1 proposal's architecture survives intact. Six decisions were amended. Each one is now a fixed constraint on the build, not a suggestion.

| # | Amendment | Reason | Consequence |
|---|---|---|---|
| **A1** | **Web chat + in-room QR is the v1 guest channel.** WhatsApp is v1.1 (weeks 7–9). Telegram is demoted to *staff notifications only*. | Telegram is absent from this guest demographic. The QR card demos in one sentence; "download Telegram" demos in an apology. Telegram remains excellent for paging staff. | Phase 2 builds the widget, not a bot. WhatsApp verification starts week 1 so it is not on the critical path. |
| **A2** | **Knowledge Coverage Score is the hero feature**, not the chat bubble. 32 canonical guest questions, scored per property, re-run on every publish. | The GM's real question is "will it embarrass me?" This answers it, doubles as the eval harness and the sales demo, and is hard for a generic chatbot to copy. | Built in Phase 1 (harness) and Phase 4 (UI). Gates go-live at ≥80%. |
| **A3** | **Per-tenant guest identities + RLS.** No global phone-keyed `guests` table. | v1's schema let Hotel A's staff see that a guest also messaged Hotel B. Privacy and legal exposure (LFPDPPP/GDPR). | Phase 0 schema. Isolation test runs in CI on every commit. |
| **A4** | **Shadow mode before autonomy.** AI drafts → staff approves → guest receives approved text. Then supervised → autonomous, per property. | Luxury brand risk is existential during the period when prompt + KB are weakest. Also the best prompt-tuning signal you will get. | Phase 2 ships in shadow mode. Autonomy is a switch gated on the eval set (Phase 5). |
| **A5** | **Async, idempotent webhook pipeline from day one.** | Provider retries + serverless timeouts = duplicate guest replies in week one. The #1 production bug in this product class. | Phase 1: `webhook_events` with unique provider message id, queue, per-conversation serialisation, 6s LLM timeout → escalation script. |
| **A6** | **~14–15 weeks elapsed to pilot, solo, with AI-assisted tooling** (57.9 build-days, minus one day a week for selling). ~12 weeks if you defer the sales day; ~4–5 with three people. v1's 2–4 weeks is a demo, not a pilot. | RLS, ingestion robustness, eval harness, queueing, notifications, kill switch and onboarding polish are the product. | Phase gates, and a staffing-baseline table in §5. The commitment you give a design partner depends on how many people are building. |

Two commercial amendments follow from the market, not from the code:

| # | Amendment | Reason |
|---|---|---|
| **A7** | **LOCKED: beachhead Mexico + Spain, Spanish and English.** Footprint Americas + Europe; global-ready architecture (i18n, EU residency, AI Act disclosure), then Brazil → US/Canada → DACH/Italy in waves. | Confirmed 21 Oct 2026. The footprint's target segment is 57k properties and the base case needs 0.13% of it, so breadth is optionality, not revenue. The competitive set (HiJiffy €99–319, Duve $120–200, Asksuite, Quinta, Runnr) is European/Israeli, priced in EUR/USD, assumes a PMS connector and a sales call. "Your concierge voice, live before lunch, no PMS project, in Spanish and English" is a sentence none of them can say — and Mexico + Spain covers two continents and two WhatsApp-dominant markets with one language pair. |
| **A8** | **WhatsApp cost is passed through, and the hotel's ROI case is instrumented from day one.** | Meta began charging per delivered *service* message on 1 Oct 2026 (1,000 free per number/month, then per-message — ~$0.0085 in Mexico). And, as §7.5 shows, labour deflection alone does **not** justify the subscription: the ROI must come from coverage, language reach and attributable upsell. |

### 0.1 Response to the external review (v2.1 changelog)

The review scored the plan 7.8/10 and raised four critical failure points plus five remediations. Nine of the ten land; one rests on a misreading. All accepted items are now **specified in the build**, not just acknowledged — the point of a review is that the next person cannot re-litigate it.

| Review point | Verdict | What changed in v2.1 |
|---|---|---|
| Distributed race conditions in async webhooks | **Accept** — the mechanism was missing | §2.5.1: `pg_advisory_xact_lock` on `conversation_id`, burst coalescing window, state-machine guard, concurrency test in CI |
| <6s SLA breached by ingestion + retrieval + classifier | **Accept, with one correction** | §2.5.2 latency budget; **streaming to the widget**; classifier folded into the main call; OCR is *ingestion-time* and off the reply path (see note below) |
| Luxury sales-to-support paradox breaks the margin | **Accept** — this is the sharpest point in the review | §7.6F/G: margin at 1.5× and 2× support load and at $60/h labour; onboarding is absorbed by the setup fee to ~2.5×; assisted onboarding becomes a **paid** service |
| Public asset exposure / storage RLS missing | **Accept** — genuine gap | §2.5.5: private buckets, `hotel_id/` path convention, signed URLs, storage RLS policies, test in CI |
| Polling transport for the widget | **Partially accept** | Supabase Realtime (WebSocket) primary, SSE for the hosted page, polling only as fallback |
| Custom OCR parsing is a tech-debt trap | **Accept** | Phase 1 uses a managed document-intelligence service behind a thin interface; custom parsing only for the structured/QA paths |
| No multi-provider LLM failover / circuit breaker | **Accept** | §2.5.4: thin provider proxy, secondary provider, trip on 429/5xx/>5s |
| Threshold "magic numbers" in code | **Accept** | §2.5.3: all thresholds in a `ai_config` table, versioned and eval-gated |
| Provider payload schema drift + widget script blockers | **Accept** | Stored raw payloads + contract tests (§2.5.6); QR links to a **hosted chat page**, not a third-party script, so ad-blockers and hotel Wi-Fi filtering cannot break it |
| Token inflation 20–30% from retries/debug | **Accept, immaterial** | Modelled: +$0.04–0.88 per property per month across all sizes (7.6H). Noted, not feared |

**The correction.** The review states that "combining OCR fallback for document ingestion … will routinely breach the 6-second p95." OCR runs when a hotel uploads a PDF — never in the reply path. The real reply-path costs are retrieval (~80ms), context assembly (~10ms), and one model call with streaming. Treated correctly, the 6s target is comfortable; it was the *unexamined budget* that was the flaw, not the target, and that is now specified per stage in §2.5.2.

**The one place I'd push back harder than the review does.** It argues luxury GMs are risk-averse and will demand white-glove onboarding, so "unassisted 45-minute onboarding" is a fantasy that becomes founder-draining CSM overhead. Half right: the *onboarding* cost is absorbable — at 2.5× the estimated hours the setup fee is still profitable at every tier (§7.6G). The damage is in **ongoing** support, which is a multiplier on every month, not once. That is why §7.6F is now the headline sensitivity and why the paid assisted-onboarding option exists: convert the high-touch demand into revenue rather than absorbing it in COGS.

---

## 1. Revised MVP definition

### 1.1 Hero promise

> *"Scan the card in your room, or tap the bubble on your site, and your hotel's concierge answers in seconds, in your language, 24/7 — and when it can't, a real person picks up with the full conversation in front of them. Live in 30 minutes, no PMS project."*

### 1.2 In scope (v1, weeks 1–6)

1. Multi-tenant Supabase schema, RLS, Auth (magic link + Google), roles owner/staff/internal.
2. **Web chat widget**: embeddable script, white-label (logo, colours, name, avatar), mobile-first, persistent; QR generator + printable branded in-room card.
3. **Knowledge**: PDF/text/URL upload with OCR fallback, chunking, embeddings, per-tenant retrieval, manual Q&A fast path, structured services/offers, draft→publish, staleness warnings.
4. **Concierge**: retrieval + last 12 messages + guest profile + hotel tone; ES/EN auto-detect; never state a price or availability that is not in structured data; always offer a human; one tool `escalate_to_staff(reason)`.
5. **Coverage Score + eval harness**: 32 canonical + 25 adversarial cases; visible in onboarding and settings.
6. **Staff dashboard**: live inbox, filters, conversation view with AI/guest/staff attribution and sources, one-click takeover/release, internal notes, suggested replies, per-hotel and per-conversation kill switch.
7. **Escalation**: keyword + model classifier (complaint, refund, safety, medical, VIP, explicit request) → ticket, email + Telegram staff notification with deep link, staffed-hours-aware guest acknowledgement.
8. **Onboarding wizard**: 9 screens, ≤30 min unassisted, with sample content and voice presets.
9. **Analytics v1**: conversations, % AI-resolved, median first response, escalation reasons, top intents, unanswered questions, languages.
10. **Ops**: async webhook pipeline, outbound queue, idempotency, timeout fallback, Sentry, `ai_runs` logging, cost caps, backups, staging + seeded demo hotel.

### 1.3 Out of scope, with the reason (use this in the room)

| Deferred | Why | Revisit when |
|---|---|---|
| PMS/CRM sync | Sales cycle + integration QA dwarf MVP value; also your differentiator | 5+ paying properties ask |
| Live availability/booking | Wrong-answer liability is severe | A booking engine with a clean API is in the partner set |
| WhatsApp marketing campaigns | Template approval + billing complexity | Post-pilot; utility templates first |
| OTA messaging (Booking/Airbnb) | Partner API access and policy constraints | Likely your best v2 wedge — validate now |
| Voice, in-room hardware | Latency + support burden | Probably never |
| Predictive upsells | No data yet | 90 days of conversation data |
| Staff replying from personal phones | Destroys the audit trail | Never |
| Multi-property roll-ups | Not needed to prove value | Chain pilot lands |

### 1.4 Market scope — Americas and Europe (research findings, Oct 2026)

**Verdict: the footprint is big enough that market breadth is not your constraint.** The base case needs **31 properties**; the serviceable footprint is **~23,000**. What the research does change is that "the whole Americas and Europe" is **four different businesses wearing one logo** — different channels, compliance regimes, languages and per-message costs. The decision this forces is: **build global-ready, sell one beachhead at a time.**

**Sizing** (full model in `09_Market_Sizing`; hotel counts are cited public figures, the three filter percentages are estimates to replace with your own pipeline data):

| Market | Hotels (all) | Independent | Target segment (4–5★, 15–250 rooms) | Serviceable | Source |
|---|---|---|---|---|---|
| Europe (28 countries) | 158,819 | 74% | 35,258 | 14,103 | HOTREC 2026: 74% independent, median 39 rooms |
| United States | ~50,000 | ~40% | 5,000 | 1,750 | ~50k hotels/motels; ~40% independent (STR) |
| Mexico | 27,948 | 85% | 8,315 | 3,742 | 27,948 establishments, +3.9% YoY |
| Brazil | ~35,000 | 85% | 7,438 | 2,975 | Low confidence — wide interval, verify |
| Canada | 7,560 | 60% | 1,361 | 476 | ~7,560 hotels / 466,850 rooms |
| **Total** | **279,327** | — | **57,371** | **23,046** | |

At a blended $439.50/month, that is a **$121.5M serviceable ARR pool**. The base case's 31 properties is **0.13% of it**; 1% penetration (~230 properties) is **$1.2M ARR**. Read that as permission to be narrow: you can miss 99.9% of the market and still have a business worth running.

**Channel fit is not uniform — this changes the roadmap:**

| Market | WhatsApp penetration | Primary channel | Consequence |
|---|---|---|---|
| Brazil | ~98% | WhatsApp | Most WhatsApp-dependent market in the footprint |
| Mexico / Spain | ~90% | WhatsApp | Same language and channel: one beachhead, two continents |
| Germany / Italy | ~85–90% | WhatsApp | Highest per-message cost (DE ≈ 6.5× MX) + German/Italian language |
| **United States** | **~25–30%** | **Web + QR** | **Do not sell the US on WhatsApp alone.** Needs SMS/RCS — a separate channel build (+4 dev-days and 10DLC registration) |
| Canada | ~45% | Web + QR | Similar to the US |

The original plan implicitly assumed "WhatsApp, then done." It isn't: **WhatsApp covers LatAm and Europe; North America needs SMS/RCS.** That is now backlog item T69, and it is the reason not to open the US before wave 3.

**Compliance is in force today, not aspirational:**

| Regime | Applies to | Requirement |
|---|---|---|
| **EU AI Act, Art. 50** | Any AI system whose output reaches EU users — **including from outside the EU** | Disclose that the guest is talking to AI **at the start of the interaction**; machine-readable marking of generated output. **In force since 2 Aug 2026**; fines to €15M or 3% of worldwide turnover |
| GDPR | EU/EEA guest data | Lawful basis, DPIA, DPA, **EU data residency option**, retention limits, erasure |
| LGPD | Brazil | Legal basis, DPO expectations, similar to GDPR |
| LFPDPPP | Mexico | Privacy notice, consent, data-subject rights |
| VAT / OSS | Selling B2B SaaS into the EU | VAT registration or merchant-of-record; reverse-charge invoicing |

Art. 50 is also a **sales asset, not just a cost**: "AI disclosure at first contact, audit-ready, EU-hosted" is something a hotel's legal team will ask about, and most independent vendors cannot evidence it cleanly. Build it in Phase 5 (T65) and put it on the website.

**Market demand signals** (so the pitch is grounded): ~37% of hotels use WhatsApp for guest communication and only ~12% embed it in strategy; **~45% of independent hotels report no AI usage at all** while 92% have adopted or plan AI-assisted messaging; **58% of hoteliers name guest communications the top AI impact area for 2026**; 77% of guests say they want it. Demand exists; the gap is specifically **independents' capability**, which is your customer.

### 1.5 Language, compliance and channel requirements — what "global-ready" actually means

Launch languages: **Spanish + English**. Then **Portuguese** (Brazil), then **French / German / Italian**. Do not claim broad language coverage you have not tested — the eval harness only certifies what it has run, and unverified multilingual claims are how you get a hallucination in German that you never see.

| Capability | v1 (wave 1: MX + ES) | Wave 2 (BR) | Wave 3 (US/CA) | Wave 4 (DACH/IT) |
|---|---|---|---|---|
| Languages | ES, EN | + PT | EN (US spelling/tone) | + FR, DE, IT |
| Guest channel | WhatsApp + web/QR | WhatsApp | **SMS/RCS + web** | WhatsApp |
| Data residency | US or EU region | EU region | US region | **EU region mandatory** |
| AI Act Art. 50 disclosure | ✅ (all channels) | ✅ | n/a (no EU users) | ✅ |
| Eval set | 32 Q × ES/EN | + PT | + US-English | + FR/DE/IT |
| Price currency | USD (+MXN) | + BRL | CAD | + EUR, VAT |

**GTM sequencing (the recommendation):**

| Wave | Weeks | Markets | Why |
|---|---|---|---|
| 1 | 1–12 | **Mexico + Spain** | One language pair, WhatsApp-heavy, low per-message cost, and a time-zone spread from UTC-6 to UTC+2 that one person can still cover. Two continents, one playbook |
| 2 | 13–20 | Brazil | ~98% WhatsApp; needs PT + LGPD; highest channel dependence |
| 3 | 21–30 | US + Canada | Requires SMS/RCS and a higher-touch sales cycle; WhatsApp alone will not sell |
| 4 | 31+ | Germany, Italy, France | Highest message cost, extra languages, most compliance scrutiny |

**Why not all at once.** Support across UTC-8 to UTC+2 is ten hours of daily overlap — impossible solo. Compliance surface quadruples. Each language needs native tone QA. Each market needs its own WhatsApp onboarding playbook. Selling four markets in parallel with one founder produces four thin, unsupported accounts instead of twenty good ones.

---

## 2. Anti-hallucination doctrine (mechanical, not aspirational)

1. **Structured facts override prose.** Prices, hours, availability, policies come only from `offers` / `services` / `knowledge_qa`, rendered as an authoritative block. Never from retrieved document text.
2. **Retrieval threshold gate.** Below threshold → do not answer; use the escalation script and log the gap.
3. **No answer without a source.** Model returns `grounded_in` (chunk/QA ids); empty → decline path. Stored in `ai_runs`.
4. **Hard-coded forbidden classes:** rates and availability, medical advice, safety guarantees, legal/visa claims, competitor comparisons, compensation/refunds, staff personal data.
5. **Prompt injection:** guest content is data, never instructions; never reveal the system prompt; strip role-play and "ignore previous instructions".
6. **Eval gate on every change:** 32 canonical + 25 adversarial cases. No publish on regression.
7. **PII redaction** on inbound and outbound: card numbers, passports, door codes → redact, store a placeholder, and reply "please don't send card details here — I'll have the front desk call you."
8. **Kill switches:** hotel-level and conversation-level, verified effective in under 5 seconds in a drill.

### 2.5 Reliability engineering (added in v2.1)

The doctrine above prevents wrong answers. This section prevents wrong *behaviour* — duplicate replies, missed messages, cross-tenant leakage and slow answers, which is how these products actually fail in production.

#### 2.5.1 Webhook concurrency: the mechanism, not the intention

Bursty arrivals are the norm in hospitality — a tour group checks in, twelve guests message within ninety seconds, some send three messages in a row.

```
worker(msg):
  1. INSERT INTO webhook_events(provider, external_id, payload) ON CONFLICT DO NOTHING
     → if 0 rows inserted, return (idempotent; provider retry, not a new event)
  2. SELECT pg_advisory_xact_lock(hashtext(conversation_id))   -- serialise per conversation
  3. IF conversation.processing_since > now() - 45s  → park in outbound_queue, exit
       (a previous reply is still in flight; do not double-answer)
  4. Debounce: wait 1.5s, then claim all unanswered guest messages for that conversation
       → one reply addresses "3pm" + "and is the pool heated?" together
  5. Set processing_since, release the advisory lock, run the LLM call OUTSIDE the lock
  6. On completion: clear processing_since, write message, enqueue send
```

Two rules that prevent 90% of these incidents: **never hold a database lock across an LLM call**, and **coalesce rather than queue** — a guest who sends three short messages should get one good reply, not three.

#### 2.5.2 Latency budget — where the 6 seconds goes

| Stage | p50 | p95 | Note |
|---|---|---|---|
| Webhook accept → 200 | 40ms | 120ms | Return immediately, work is queued |
| Identity + conversation load | 30ms | 90ms | Indexed on `(hotel_id, channel, external_id)` |
| Retrieval (`pgvector`, tenant-filtered, top-k 5) | 70ms | 180ms | HNSW index; filter by `hotel_id` before search |
| Context assembly (history + profile + tone + facts) | 10ms | 25ms | Cached per conversation |
| **Semantic cache hit → send** | **240ms** | **600ms** | Bypasses the model entirely for canonical questions |
| Model — first token (streamed) | 700ms | 1.8s | Streaming is what the guest experiences |
| Model — full reply | 2.4s | 5.0s | Hard timeout 6.0s → escalation script |
| Send + persist | 150ms | 400ms | |
| **Perceived first response** | **0.9s** | **2.4s** | What the guest judges you on |
| **End-to-end completion** | **2.7s** | **5.9s** | Within budget, with no headroom to spare |

Three consequences: **stream to the widget** (perceived latency is what matters, and a typing indicator covers the rest); **semantic-cache the canonical questions** — breakfast hours, wifi, checkout time will be 30–40% of volume and can be answered in ~240ms with no model call at all (this also cuts token cost and, on WhatsApp, message count); and **fold the escalation classifier into the main call** as a structured output field rather than a second round trip, which alone removes ~800ms from p95.

#### 2.5.3 Configuration, not constants

`ai_config(hotel_id nullable, key, value, version, updated_by)`: `similarity_threshold` (default 0.72), `top_k` (5), `max_context_chunks` (6), `model_timeout_ms` (6000), `debounce_ms` (1500), `max_history_messages` (12), `escalation_confidence_floor` (0.55), `provider_primary`/`provider_secondary`. Every value is eval-gated: change it, the 55-case suite re-runs, publish is blocked on regression. No threshold lives in application code.

#### 2.5.4 Provider failover and circuit breaker

A thin `llm.complete()` proxy with a primary/ secondary provider, a circuit breaker (trip on 3 consecutive 429/5xx or any call >5s), and a deterministic degradation ladder: **primary → secondary provider → semantic-cache best match → escalation script**. The fourth rung always works and is never a hallucination. Provider choice is per-hotel config, so one hotel's rate limit cannot degrade another's service.

#### 2.5.5 Object storage is tenant data too

Every upload, OCR text cache and generated QR card lives in a **private** bucket under the path convention `{hotel_id}/{kind}/{uuid}.{ext}`. Access is by short-lived signed URL only (60s), issued server-side after a membership check. Storage RLS policies match on the `hotel_id` path prefix against the caller's JWT claims, and the CI isolation test covers **storage**, not just tables — a staff user from hotel A must not be able to mint a signed URL for any hotel B object, including by guessing paths. OCR text is persisted into `knowledge_documents.ocr_text` (RLS-protected) rather than a public cache object.

#### 2.5.6 Third-party drift and hostile networks

Raw webhook payloads are stored before parsing, and a **contract test** runs daily against recorded fixtures for Telegram/Meta: if a provider adds or renames a field, the fixture diff fails CI before it fails a guest. For hotel networks and ad-blockers, the QR code and the widget's primary path resolve to a **hosted chat page on your own domain** (first-party, no third-party script, no cookies required), with the embeddable script as an enhancement rather than a dependency. This is a reliability argument for the QR-first channel decision in A1, not just a marketing one.

---

## 3. Data model (amended)

```sql
-- tenancy & identity  (replaces v1's global guests table)
hotel_guests(id, hotel_id, channel, external_id, display_name, language, prefs jsonb)
  unique(hotel_id, channel, external_id)

-- knowledge, properly versioned
knowledge_documents(id, hotel_id, title, source_type[pdf|url|text], storage_path,
                    status[draft|published], version, updated_by, published_at, stale_after)
knowledge_chunks(id, document_id, chunk_index, content, embedding vector(1536), token_count, metadata)
knowledge_qa(id, hotel_id, question, answer, approved_by)          -- top-40 FAQ fast path

-- money/services: structured, never embedded
offers(id, hotel_id, name, description, price, currency, active, upsell_eligible)

-- AI observability
ai_runs(id, conversation_id, message_id, prompt_version, model, tokens_in, tokens_out,
        retrieved_chunk_ids uuid[], top_score, latency_ms, escalated, escalate_reason, cost_usd)
prompt_versions(id, hotel_id nullable, body, version, is_active)

-- reliability
webhook_events(provider, external_id UNIQUE, payload, processed_at)
outbound_queue(id, message_id, attempts, status, last_error, next_retry_at)

-- operations
audit_log(hotel_id, actor_type, actor_id, action, entity, entity_id, at)

-- added in v2.1: reliability + configuration
ai_config(hotel_id nullable, key, value jsonb, version, updated_by)   -- thresholds, no magic numbers
conversation_state(conversation_id PK, processing_since timestamptz, next_seq bigint)
webhook_fixtures(provider, captured_at, payload)                       -- contract-test corpus
semantic_cache(hotel_id, question_embedding vector(1536), answer, source_ids, hits, updated_at)
```

Storage is governed too: private buckets, `{hotel_id}/...` path convention, signed URLs only, storage RLS covered by the same isolation test.

`messages` gains `channel_message_id UNIQUE`, `direction`, `role(guest|ai|staff|system)`, `delivery_status`, `hotel_id` (for RLS and query speed), `redacted`, `intent`, `sentiment`.
RLS on every table via staff membership; service role only inside webhook workers. **One CI test asserts a staff user from hotel A reads zero rows of hotel B across every tenant table.**

---

## 4. Goals

### 4.1 Business

| Goal | Target | By |
|---|---|---|
| Design partners signed (LOI + content + 2h/week champion) | 3 | week 3 |
| Properties live with real guests | 2 | week 7 |
| First paying conversion at $349 ARPU | 1 | week 10 |
| Paid properties | 3 | week 14 |
| GM interviews completed ("why not HiJiffy?") | 5 | week 6 |

### 4.2 Product — per property, first 60 days live

| Metric | Target | Floor (below = intervene) |
|---|---|---|
| Conversations resolved with no staff action | ≥55% | 35% |
| Eval groundedness (32 canonical + 25 adversarial) | ≥95%, 0 fabricated prices | any fabricated price = stop-ship |
| Median AI first response | ≤6s | 15s |
| Escalation rate | 20–40% | >60% ⇒ KB/prompt problem |
| Escalation false negatives | ≤2% | 5% |
| Signup → first live guest conversation | ≤45 min unassisted | 90 min |
| Coverage score at go-live | ≥80% of 30 | 65% |
| Card/PII redaction incidents reaching storage | 0 | any = incident review |
| Staff adoption | ≥2 staff/week in the inbox | 1 |

### 4.3 Engineering

p95 reply latency <8s · webhook 200 in <300ms · zero duplicate replies (proven by test) · tenant-isolation test green in CI · every AI answer traceable (prompt version, sources, model, cost) · one-command local env + seeded demo hotel · MTTR <30 min via kill switch.

---

## 5. Development plan — phases, deliverables, gates

Solo full-stack durations. **Do not start a phase until the previous gate passes.**

### Phase 0 — Foundations & design partners (week 1)
**Deliverables:** repo + envs + CI + Sentry + seeded demo hotel · full schema + RLS + isolation test · Auth, roles, invitations · provisioning flow (hotel → owner → widget key → channel config) · 3 design partners signed with raw content in hand · `prompts/v0` written with a GM · 32 canonical + 25 adversarial eval cases · Meta/BSP application submitted.
**Gate:** hotel A's staff provably cannot read hotel B data; two partners' content downloaded and readable.

### Phase 1 — Ingestion, RAG, eval harness (week 2)
**Deliverables:** upload → parse (**managed document-intelligence service behind a thin interface**, custom parsing only for structured/QA paths) → chunk → embed → version · scoped retrieval with threshold gate + Q&A fast path + structured facts block · prompt assembly (tone, profile, 12 messages, context, facts) · `ai_runs` cost/latency logging · eval runner CLI emitting coverage score · internal reply console (question → draft → sources → confidence → approve/edit/reject) · async webhook pipeline + outbound queue.
**Gate:** ≥85% groundedness on partner #1's real questions; every failure classified (retrieval / missing KB / prompt / model); duplicate-provider-delivery test produces exactly one reply; **concurrency test** (10 simultaneous messages to one conversation → exactly one coalesced reply); storage isolation test green.

### Phase 2 — Widget + QR, in shadow mode (week 3)
**Deliverables:** embeddable white-label widget (mobile-first; Supabase Realtime/WebSocket primary, SSE for the hosted page, polling only as fallback) · **hosted first-party chat page** for QR traffic (no third-party script dependency) · QR + printable in-room card PDF · conversation engine (identity, language detect, history, reply, storage) · **shadow mode** with staff approval · escalation script + classifier v1 · LLM timeout fallback · rate limits and injection filtering.
**Gate:** 50 shadowed conversations at partner #1; zero unanswered guests; median staff approve-time <60s; approval-edit rate recorded.

### Phase 3 — Staff console (week 4)
**Deliverables:** inbox (filters, realtime, unread, search, assignment) · conversation view with attribution + sources + internal notes · takeover/release/close + AI pause · suggested-reply composer · tickets + email/Telegram notifications with staffed-hours-aware copy · audit log · kill switches.
**Gate:** a staff member who has never seen the product handles a live escalation end-to-end in <60s with no verbal instruction; kill switch verified in <5s.

### Phase 4 — Onboarding, coverage score, analytics (week 5)
**Deliverables:** the 9 wizard screens, instrumented · coverage score UI with inline add-answer · analytics v1 · weekly knowledge-gap email to the GM · sample knowledge pack + 3 voice presets · settings + team management.
**Gate:** partner #2's GM completes onboarding **unassisted** in ≤45 min with a coverage score ≥80%, no support call.

### Phase 5 — Hardening & pilot go-live (week 6)
**Deliverables:** RLS suite in CI, secrets, rate limits, adversarial pass, live PII redaction, DPA + privacy policy + retention config + deletion endpoint · retries, DLQ, duplicate-reply test, load test at 20× expected volume, backup/restore drill · per-hotel token and message caps · runbook (bad answer, outage, WhatsApp ban, data request, comms) · design-partner kit (GM one-pager, 10-minute staff training, in-room card v2) · autonomy ramp with eval-set gate.
**Gate:** 7 consecutive days live, 0 fabricated-price incidents, ≥40% AI-resolved, MTTR drill passed.

### Phase 6 — WhatsApp (weeks 7–9)
**Deliverables:** BSP/Cloud API (WABA, verification, display name, number strategy incl. coexistence with the WhatsApp Business app) · per-hotel number mapping · 24h window enforcement · utility templates (pre-arrival, arrival-day, post-stay) + approval tracking · opt-out registry · quality-rating monitoring, no unsolicited outbound · **message cost tracking and pass-through billing**.
**Gate:** 1 property live 14 days, quality rating green, message cost ≤$0.15/conversation, no blocked numbers.

### Phase 7 — Post-MVP, in order of evidence
OTA messaging (validate first — it may be the true wedge) → PMS read (Mews/Apaleo) → utility-template lifecycle → upsell attribution on structured offers → multi-property dashboard.

### Schedule — and the staff-count arithmetic

The phase durations above are **person-days of work**, not calendar days. The backlog now totals **90.2 dev-days to a multi-market pilot-ready build** (unaided) and **116.8 to everything including WhatsApp and SMS/RCS**. Every task carries an `ai_leverage_factor` and an `adjusted_days` column, so the AI assumption is auditable rather than asserted:

| Workstream | Retained human effort with AI tools | Why |
|---|---|---|
| Foundations, product UI, channels | **55%** | Boilerplate, CRUD, forms and layouts are where AI leverage is highest |
| Knowledge ingestion, RAG, ops | 60% | Plumbing is fast; correctness is judged by the eval set, not by the tool |
| AI / prompting / eval authoring | **70%** | Domain judgement dominates; AI helps write harness code, not decide what "good" sounds like |
| Billing, integrations | 60–65% | Well-trodden patterns |
| **Security-critical** (RLS, signed URLs, webhook validation, PII redaction) | **80%, with mandatory human review** | See the warning below |
| GTM, partner work, native-language QA | 90–95% | Barely helped at all: this is people talking to people |

**Resulting schedule, multi-market scope:**

| Staffing | Pilot-ready | WhatsApp live |
|---|---|---|
| **Solo + AI-assisted tooling — PLAN OF RECORD** | **~12 weeks** pure build (57.9 ÷ 5) · **~14–15 weeks elapsed** at 4 build-days/week | ~16 weeks elapsed |
| Solo, unaided | ~18 weeks | ~23 weeks |
| Solo + AI, **single market** (defer i18n / Art. 50 / residency / VAT) | ~10 weeks pure build | ~12 weeks elapsed |
| Two people + AI | ~6 weeks | ~8 weeks |
| Three people + AI | ~4–5 weeks | ~6 weeks |

### 5.1 Solo operating cadence (locked 21 Oct 2026)

Building and selling alone means the calendar, not the backlog, is the binding constraint. The plan therefore runs on a fixed weekly rhythm rather than an open-ended sprint:

| Day | Focus | Rule |
|---|---|---|
| Mon–Thu | Build, one phase at a time | Nothing else. No calls booked before 14:00 local. |
| **Fri** | Selling, design partners, content collection | **Never skipped.** This is the only task with no synthetic substitute (§9.1) |
| Fri (end) | Gate check against the current phase, 20 minutes | If the gate fails, next week is a gate week, not a feature week |
| Daily | 30 minutes of eval runs on the day's changes | Cheap, and it stops prompt drift accumulating for a week |

**Elapsed time arithmetic, stated plainly:** 57.9 adjusted build-days at 5 days/week is 11.5 weeks; at 4 days/week (one sales day) it is **14.4 weeks**. Publishing a 12-week promise while also selling would be the same optimism this plan has already corrected twice. **Commit to 14–15 weeks to design partners, and treat 12 as the outcome if the first three partners arrive early enough to free up Fridays.**

**Three solo-specific safeguards** (these exist because there is no second person to catch them):

1. **External security review before the first real guest** — $2,000, two days, scoped to RLS, signed URLs, webhook validation and redaction. Budgeted in §7.5.
2. **Bus-factor discipline** — infrastructure defined in code where possible, a runbook that a contractor could execute, and no undocumented manual console steps. If you are ill for two weeks, the product must keep answering guests.
3. **Single point of failure on judgement** — the eval harness, not your memory, is the authority on whether quality regressed. Run it before every publish, even when you are confident.

**What you must not do solo:** take a fourth design partner before the first two are live. Support load compounds and there is no one to hand it to; the model shows support above ~2× the estimate is what erodes margin (§7.6F).

**Three things AI tooling does not buy you, and one that will bite:**

1. **Design partners and hotel content.** Unchanged — you still have to persuade three GMs and collect their PDFs. The plan's biggest schedule risk is not code.
2. **Native-language tone QA.** A model can translate the eval set; only a native speaker can tell you the reply sounds like a luxury concierge rather than a translation.
3. **The gates themselves.** Concurrency, tenant isolation, eval pass, and prompt quality are judgement calls. AI generates plausible code *and plausible tests that assert your assumptions*.
4. **Security-critical code is where AI-generated code fails silently.** A subtly wrong RLS policy or an unchecked signed-URL path passes every happy-path test and leaks across tenants. Everything in the "Security-critical" row above is **human-reviewed line by line** and covered by a deliberately-broken test that must fail. Set the pace by the gates, not by how fast the tools produce code.

**Three-person week-by-week**

| Week | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|
| Focus | Foundations + partners | RAG + eval | Widget + shadow | Staff console | Onboarding + coverage | Hardening + **pilot live** | WhatsApp setup | WhatsApp + templates | WA pilot + first conversion |
| Split | P1 backend/AI · P2 product/fullstack · P3 design + content ops | | | | | | | | |

**Solo + AI-assisted tooling, multi-market scope — plan of record (~14–15 weeks elapsed at 4 build-days/week)**

| Weeks | 1–3 | 4–6 | 7–8 | 9–10 | 11 | 12–14 | 15–17 |
|---|---|---|---|---|---|---|---|
| Focus | Foundations, partners, schema, **bilingual** eval set | Ingestion + RAG + harness (+ concurrency, failover, i18n) | Widget, hosted page, shadow mode | Staff console + takeover | Onboarding + coverage score + analytics | Hardening + Art. 50 + EU residency + external security review + **pilot live** | WhatsApp (MX + ES), templates, message billing |

---

## 6. Risk register

| # | Risk | L | I | Mitigation |
|---|---|---|---|---|
| R1 | Hallucinated price/hours → brand incident | M | **High** | §2 doctrine, threshold gate, `grounded_in`, shadow mode, eval gate, kill switch |
| R2 | Guest channel mismatch (Telegram-first) | **High** | High | Amended: web+QR, WhatsApp v1.1, Telegram for staff |
| R3 | "Why not HiJiffy?" unanswered | **High** | High | Narrow wedge (A7); 5 GM interviews by week 6 |
| R4 | Hotels won't supply good content | **High** | Med | Coverage score with a visible finish line, inline add-answer, sample packs, done-with-you onboarding |
| R5 | WhatsApp verification/coexistence delays | M | Med | Start week 1; v1.1; document second-number playbook |
| R6 | WhatsApp per-message cost erodes margin | M | Med | Pass-through + allowance; prefer web channel. See §7.3 |
| R7 | Cross-tenant leak | L | **High** | Per-tenant identities, RLS, CI isolation test, audit log |
| R8 | Guest sends card/PII | **High** | Med | Redaction in/out, firm reply, retention policy |
| R9 | 2am escalation, no staff awake | **High** | Med | Staffed-hours-aware copy, on-call rota, ticket SLA in inbox |
| R10 | Solo timeline slip (6→10 weeks) | M | Med | Phase gates, hard cut list, prompts + eval set pre-written in week 1 |
| R11 | **Hotel ROI case doesn't hold at renewal** | **High** | **High** | Instrument value from day one: labour, after-hours, upsell attribution (§7.5). This is the real renewal risk. |
| R12 | Pilot stalls without a paid path | M | Med | LOI + setup fee + paid pilot after 30 days; kill criteria (§7.7) |
| R13 | **Guest data residency / LLM sub-processor objection blocks a chain or a well-advised independent** | **High** | **High** | Answer it before it is asked: zero-retention API terms with the model provider, no training on guest data, Supabase region pinned to the hotel's jurisdiction, named sub-processor list in the DPA, retention window configurable (90/180 days), deletion endpoint. Put this on the website — it is a sales asset, not paperwork |
| R15 | Duplicate replies / race conditions under bursty arrivals | **High** | Med | `pg_advisory_xact_lock` per conversation, 1.5s coalescing, no lock held across LLM calls, CI concurrency test (§2.5.1) |
| R16 | White-glove support demand turns product into services | **High** | High | Paid assisted onboarding; coverage score + gap email as COGS controls; measure real support hours by week 8; §7.6F sets the price floor |
| R17 | Cross-tenant leak via object storage | L | **High** | Private buckets, path convention, signed URLs, storage RLS, storage isolation test in CI (§2.5.5) |
| R18 | LLM provider outage or rate limit degrades all tenants | M | High | Provider proxy + circuit breaker + 4-step degradation ladder ending in the escalation script (§2.5.4) |
| R25 | **Solo bus factor** — illness, burnout or a family event stops everything | M | **High** | Runbook a contractor could execute; infra as code; no undocumented console steps; external security review; keep the eval harness authoritative so quality doesn't depend on memory |
| R26 | **Selling and building on the same calendar** — Fridays quietly sacrificed to features | **High** | High | Fixed 4/1 weekly rhythm (§5.1); gate weeks are non-negotiable; if three consecutive Fridays are lost, the plan is off track and the honest response is a later commitment, not a faster build |
| R20 | **Selling across Americas + Europe in parallel** — support time zones, 4 compliance regimes, 6 languages | **High** | **High** | Wave sequencing (§1.5); global-ready architecture, one beachhead at a time; no phone support; async-first |
| R21 | Selling the US on WhatsApp (guest channel mismatch) | **High** | High | US/Canada wave requires SMS/RCS (T69); do not open wave 3 without it |
| R22 | EU AI Act Art. 50 non-compliance (fines to €15M / 3% worldwide turnover; applies to non-EU providers) | M | **High** | Disclosure at first contact in every channel + provenance metadata (T65), legal sign-off before the first EU tenant |
| R23 | Shipping unverified languages (a bad German answer you never see) | M | High | Eval set per language pair, native QA, no language enabled without a passing eval |
| R24 | AI-generated security code leaks tenants silently | M | **High** | Human line-by-line review of RLS, signed URLs, webhook validation, redaction; tests that fail when deliberately broken |
| R19 | BSP platform fee (≈$50–100 per number/month) plus number portability friction | M | Med | Pick the BSP in week 1 and confirm fees; pass platform fee through in the Pro tier; document the coexistence/porting path before the first WhatsApp sale |

---

## 7. The economics

All figures below are computed live in `financial-model.xlsx`. Inputs: blended contractor labour $32/h; infra pool $260/mo over 25 properties; LLM at the current small-model tier ($0.10/$0.50 per M tokens, ~18.7k tokens in / 700 out per conversation); 5 hotel messages per conversation; WhatsApp at Mexico rates ($0.0085/msg, +20% BSP markup, 1,000 free per number/month); 2.9% card fees.

### 7.1 Unit economics by property size — the core of the plan

| | **T1** Boutique/casita | **T2** Boutique luxury | **T3** City hotel | **T4** Resort | **T5** Flagship | **Blended** |
|---|---|---|---|---|---|---|
| Rooms | 15 | 30 | 60 | 120 | 250 | 54 |
| List price / month | $299 | $349 | $449 | $699 | $1,199 | **$439.50** |
| Price / room / month | $19.93 | $11.63 | $7.48 | $5.83 | $4.80 | $8.15 |
| Conversations / month | 45 | 78 | 132 | 228 | 425 | 116 |
| Business messages / month | 315 | 546 | 1,056 | 1,824 | 3,825 | 909 |
| WhatsApp cost / month | $0.00 | $0.00 | $0.00 | $3.20 | $19.06 | $1.27 |
| LLM + aux / month | $0.19 | $0.32 | $0.55 | $0.95 | $1.76 | $0.48 |
| Infra allocation / month | $11.90 | $11.90 | $11.90 | $11.90 | $11.90 | $11.90 |
| Support labour / month | $28.80 | $35.20 | $44.80 | $60.80 | $89.60 | $41.41 |
| Card fees / month | $8.67 | $10.12 | $13.02 | $20.27 | $34.77 | $12.75 |
| **Total COGS / month** | **$49.56** | **$57.54** | **$70.27** | **$97.11** | **$157.10** | **$67.81** |
| **Gross profit / month** | **$249.44** | **$291.46** | **$378.73** | **$601.89** | **$1,041.90** | **$371.69** |
| **Gross margin** | **83.4%** | **83.5%** | **84.3%** | **86.1%** | **86.9%** | **84.6%** |
| Gross profit / room / month | $16.63 | $9.72 | $6.31 | $5.02 | $4.17 | $6.90 |
| Onboarding cost (labour) | $80 | $96 | $128 | $176 | $240 | $115 |
| Setup fee | $500 | $500 | $500 | $750 | $1,000 | $550 |
| **Onboarding margin** | **$420** | **$404** | **$372** | **$574** | **$760** | **$435** |
| CAC payback (months) | 3.6 | 3.1 | 2.4 | 1.5 | 0.9 | **2.4** |
| LTV / CAC (2.5% churn) | 11.1× | 13.0× | 16.8× | 26.8× | 46.3× | **16.5×** |

*Provenance: prices, setup fees and the 1,000-free-message structure are commitments. Engagement per room (1.7–3.0 conversations/room/month), support hours (0.9–2.8), escalation rate (22–30%), churn (2.5%) and pilot→paid conversion (60%) are **estimates to be measured in weeks 3–6**; they are the first things the model should replace with real data, and the first things a reviewer should challenge.*

**What this table says.**

- **Gross margin is not the problem, and messaging is not the threat.** The whole COGS stack is $50–157 per property. At MVP volumes you are running a ~85% gross-margin business at every size.
- **WhatsApp costs nothing until a property is big.** In Mexico, a property only starts paying after 1,000 business messages/month — which is T4 and above. T1–T3 pay **zero**. The fear that Meta's Oct 2026 pricing breaks the model is wrong at this scale; it matters above ~2,500 messages/month and in high-rate markets (§7.3).
- **Support labour is ~60% of COGS and the only line that scales dangerously.** This is why the onboarding wizard, coverage score, sample packs and weekly gap email are not features — they are COGS controls. Every hour of support you remove adds roughly $32/month of gross profit per property.
- **Price per room falls faster than cost per room, deliberately.** T5 at $4.80/room is still 86.9% margin because a 250-room sale is a single support relationship, while T1 at $19.93/room is the expensive one to serve. Pricing reads correctly to a hotelier *and* protects you.
- **Onboarding is profitable at every size** if you charge the setup fee — and loss-making at T4/T5 if you waive it ($176–240 of labour). Stop waiving above T3.
- **Payback under four months everywhere** means growth funds itself from month one. Capital is not the constraint; founder selling time and support hours are.

### 7.2 Breakeven — how many properties you need

| Metric | Value |
|---|---|
| Blended gross profit per property / month | $371.69 |
| Fixed opex (founder draw + tools + marketing + contractor) | $7,200 / mo |
| **Properties to cover base opex** | **19.4** |
| Properties once the first support hire is triggered (opex $10,800) | 29.1 |
| Properties once the second hire is triggered (opex $14,400) | 38.7 |
| MRR at the 29-property breakeven | ~$12,770 |
| Support hours / month at the 29-property breakeven | 37.6 h (≈8.7 h/week) |
| Support hours / month at the 39-property breakeven | 50.1 h |

Two things follow. First, **~20 paying properties is the first real milestone** — not 5, not 50. Second — and this cuts against the model's own assumption — at the 29-property breakeven you consume only ~38 support hours a month, about 9 hours a week. That is a part-time contractor, not a $3,600/month hire. The opex step is therefore deliberately conservative: it is sized for support *plus* onboarding and CSM work, not tickets alone. If ticket load is all you hire for, the step could be roughly half. Keep it conservative until onboarding hours are measured for real.

One consequence worth stating separately, because it is the biggest decision in the plan: **a three-person build (~$16,700/month opex) raises the breakeven bar from ~19 properties to ~45.** You are trading roughly eight weeks of calendar time for a bar that is 2.3× higher. That trade only makes sense if you can also sell three times faster — see §7.5.

### 7.3 WhatsApp cost by market — the amended line item

Service messages became billable on **1 Oct 2026**, after 1,000 free per business number per month. Rates below are per delivered message; the model adds the 20% BSP markup.

| Market | Service $/msg | Cost per 100 conversations | Monthly cost, T5 (1,869 billable msgs) |
|---|---|---|---|
| **Mexico** | $0.0085 | $5.10 | **$19.06** |
| United States | $0.0034 | $2.04 | $7.63 |
| Brazil | $0.0068 | $4.08 | $15.25 |
| Spain | $0.0200 | $12.00 | $44.85 |
| United Kingdom | $0.0220 | $13.20 | $49.34 |
| **Germany** | $0.0550 | **$33.00** | **$123.34** |

Not included in the model: the BSP's own platform fee (roughly $50–100 per WhatsApp number per month, and it varies by provider). It is a pass-through in the Pro tier, not COGS — but confirm the number with your chosen BSP in week 1, because at T1–T3 scale it is larger than the Meta per-message fees themselves.

Implications: (a) pass messaging through with an allowance — never absorb it in a flat tier; (b) prefer the free web channel for high-volume traffic; (c) if you ever sell into DACH, the WhatsApp line becomes a real cost and must be priced; (d) keep replies *efficient* — message count, not token count, is the unit of WhatsApp cost; (e) messages inside a Click-to-WhatsApp entry-point window are not charged, so route acquisition traffic there.

### 7.4 The 24-month run — three scenarios

Pilots are the only hard input. Conversions land one month later; churn hits the opening base; setup fee realisation is 50%.

| | Conservative | **Base** | Aggressive |
|---|---|---|---|
| Pilot → paid | 55% | **60%** | 70% |
| Monthly churn | 3.0% | **2.5%** | 1.8% |
| Active properties — month 12 | 11 | **18** | 31 |
| Active properties — month 24 | 26 | **31** | 77 |
| MRR — month 12 | $4,835 | **$7,911** | $13,625 |
| MRR — month 24 | $11,427 | **$13,625** | $33,842 |
| ARR — month 24 | $137k | **$163k** | $406k |
| Revenue, 24 months | $142,987 | **$186,300** | $376,487 |
| Gross profit, 24 months | $122,238 | **$159,177** | $321,834 |
| Total opex, 24 months | $180,000 | **$198,000** | $244,800 |
| Net cash, 24 months | −$59,762 | **−$40,823** | **+$75,034** |
| **Peak funding requirement** | **$80,867** | **$63,961** | $54,124 |
| First cash-flow-positive month | 17 | **13** | 9 |
| Cumulative cash recovered | beyond month 24 | beyond month 24 | month 20 |

**Read this honestly:** in the base case the business is *monthly* profitable from month 13 and is generating ~$163k ARR by month 24 — but cumulative cash is still ~$39k below zero at the end of the window, because the first year burns more than the second year earns. That is normal for a solo, bootstrapped SaaS with a $900 CAC and a six-month pre-revenue-ish start; it is not a failure. But it means you need either **~$62–79k of cash buffer** or a slower, unpaid-founder path.

### 7.5 Cash requirement — the ask

| Item | Amount |
|---|---|
| Pre-launch capital (weeks 1–6: 1.5 months opex + legal/DPA/design/BSP + **contracted security review**) | $17,000 |
| Base-case peak funding requirement | $63,961 |
| Conservative peak funding requirement | $80,867 |
| **Recommended cash buffer (conservative peak + 30%)** | **~$105,000** |
| Contingency: if you later add two people (see `08_Cash_Runway`) | ~$187,000 |
| Months of opex that buffer buys at pre-revenue burn | 14.6 |

The $17,000 pre-launch figure now includes **$2,000 for an external security review** of the RLS policies, signed-URL logic, webhook validation and PII redaction. Going solo removes the second pair of eyes that would otherwise catch a silent tenant-isolation bug; buying two days of a specialist is the cheapest possible insurance and is not optional (§2.5.5, R24).

Three ways to avoid or shrink a raise, in order of preference:

1. **Pre-sell.** Three design partners × ($500 setup + 3 months prepaid at $349) ≈ $4.6k in week 6, which covers most of pre-launch burn.
2. **Stay solo and unpaid through month 13.** This is the **plan of record** as of 21 Oct 2026: the base case reaches monthly breakeven without external capital, so the ~$105k is a *worst-case requirement*, not a target raise. Fund it from savings or a small friends-and-family note only if the conservative case starts to look likely.
3. **Raise only after 10+ paying properties**, when churn is a measured number rather than a guess. Raising earlier prices a business you cannot yet describe.

### 7.6 Sensitivities — where the model breaks

**A. Gross margin vs support hours per property per month** (everything else held constant)

| Support h/mo | T1 | T2 | T3 | T4 | T5 |
|---|---|---|---|---|---|
| 0.5 | 87.7% | 89.0% | 90.8% | 92.5% | 93.0% |
| 1.0 | 82.4% | 84.4% | 87.2% | 90.2% | 91.7% |
| **1.5** | 77.0% | 79.8% | 83.6% | 87.9% | 90.4% |
| 2.0 | 71.7% | 75.3% | 80.1% | 85.6% | 89.0% |
| 3.0 | 61.0% | 66.1% | 72.9% | 81.1% | 86.4% |
| 4.0 | **50.2%** | 56.9% | 65.8% | 76.5% | 83.7% |

Support load is the only input that can take a viable product to a marginal one. At 4 hours/property/month the smallest tier drops to 50% margin. **The wizard and coverage score are the difference between 83% and 60%.**

**B. LTV / CAC vs monthly churn** — at 1% churn T1 is 27.7×; at 5% it is 5.5×; at 7% it is 4.0×. Churn is the most dangerous variable and the one the weekly knowledge-gap email improves fastest.

**C. Hotel ROI — the number that actually decides renewal.** This is the honest part of the model, and the one most vendors skip.

| | T1 | T3 | T5 |
|---|---|---|---|
| Conversations / month | 45 | 132 | 425 |
| Resolved by AI (55%) | 25 | 73 | 234 |
| Front-desk minutes saved (5 min/conversation) | 124 | 363 | 1,169 |
| **Labour value saved / month** (at $12/h loaded) | **$25** | **$73** | **$234** |
| Subscription | $299 | $449 | $1,199 |
| **Labour alone covers** | **8%** | **16%** | **19%** |

**This is the single most important finding in the economics, so state it plainly: pure labour deflection cannot justify the price.** At T1 it covers 8% of the subscription. Closing that gap requires the other three value levers — 24/7 and after-hours coverage, language coverage for international guests, and *attributable* upsell/pre-arrival revenue — and those must be instrumented from day one or renewal conversations will be unwinnable.

Concretely, this dictates three product decisions: (1) the monthly report the GM receives must show after-hours conversations handled and languages served, not just "messages answered"; (2) upsell attribution (§Phase 7) is not a nice-to-have, it is the ROI proof — bring it forward if the pilots demand it; (3) consider a **$199 "Lite" tier for T1** (web widget only, no WhatsApp, no upsell module) or sell T1 properties as part of a group deal, because a 15-room property's ROI case is thinnest even though its unit margin is excellent.

**F. Support load × labour rate — the combined stress (v2.1).** Gross margin, with support hours multiplied:

| Support multiplier | T1 @ $32/h | T3 @ $32/h | T5 @ $32/h | T1 @ $60/h | T3 @ $60/h | T5 @ $60/h |
|---|---|---|---|---|---|---|
| 1.0× (model default) | 83.4% | 84.3% | 86.9% | 75.0% | 75.6% | 80.4% |
| 1.5× | 78.6% | 79.4% | 83.2% | 66.0% | 66.3% | 73.4% |
| 2.0× | 73.8% | 74.4% | 79.4% | **56.9%** | **56.9%** | 66.3% |
| 2.5× | 69.0% | 69.4% | 75.7% | **47.9%** | **47.6%** | 59.3% |

This is the review's strongest point, quantified. If the luxury buyer demands true white-glove support *and* you staff it at $60/h, T1 and T3 margins fall to ~57% — still viable, but the business becomes a services business. **Set the labour rate by who actually does the work**, and revisit the support hour estimates with real data by week 8, not week 24.

**G. Onboarding under high-touch multipliers.** Setup fee minus onboarding labour: at 2.5× the estimated hours the setup fee is still positive at every tier (T1 $300, T3 $180, T5 $400). Onboarding is **not** the margin risk the review fears; ongoing support is. This is why assisted onboarding is offered as a **paid** add-on ($750–1,500) rather than absorbed.

**H. Token inflation.** A 20–30% retry/debug overhead adds $0.04–0.53 per property per month; at 50% it is still under $0.90. Immaterial. Do not spend engineering time optimising tokens before support hours.

**D. What breaks the model, ranked**

1. Support above 4 h/property/month (§A).
2. Churn above 5% monthly (§B).
3. No defensible hotel ROI at renewal (§C) — the reason to build the value report early.
4. Waiving setup fees on T4/T5.
5. Nothing else in scope. WhatsApp rates and LLM prices are rounding errors at this scale.

### 7.7b Market sizing — what it changes about the economics

Nothing in the unit economics changes; what changes is the **ceiling and the cost of reaching it** (`09_Market_Sizing`):

| | Value |
|---|---|
| Target-segment properties, Americas + Europe | 57,371 |
| Serviceable (digital presence + messaging-ready) | 23,046 |
| Serviceable ARR pool at blended $439.50/mo | **$121.5M** |
| Base case, 31 properties = **0.13%** of serviceable | $163k ARR |
| 0.5% penetration (~115 properties) | $608k ARR |
| 1% penetration (~230 properties) | **$1.2M ARR** |

**The strategic read:** the market is not what limits you, so expanding to four regions buys you *optionality*, not *revenue* — while costing ~12 dev-days, four compliance regimes and native QA per language. Spend that only when the beachhead is working.

### 7.7 Pricing, packaging, kill criteria

| | Starter | Pro |
|---|---|---|
| Price / month / property | **T1 $299 · T2 $349 · T3 $449** | **T4 $699 · T5 $1,199** |
| Included | Web widget + QR, KB, inbox, takeover, coverage score, analytics v1 | + WhatsApp, upsell catalog, unlimited staff seats |
| Setup | $500 (T4/T5: $750–1,000) | waived only for the first 3 design partners, in exchange for content + weekly feedback |
| Messaging | Web included | Channel fees pass-through at cost + 20% |
| Seats | **Always unlimited** — seats are your adoption path, never a revenue line |
| Optional (validate, do not build) | **$199 "Lite"** — widget + KB + inbox only, for sub-25-room properties, if the T1 ROI conversation fails (§7.6C) |

**Kill criteria, written down now:** after 60 days live at 2+ properties, if (a) AI-handled-without-staff <35%, or (b) any confirmed fabricated price/availability, or (c) the GM will not pay $299, or (d) the value report cannot show a credible ROI story → stop, reposition (most likely toward OTA messaging or the knowledge/coverage tool alone), and do not add features.

---

## 8. Definition of done (pilot-ready)

- [ ] Two hotels, isolated, verified by automated test
- [ ] A GM with three PDFs goes live unassisted in ≤45 min, coverage score ≥80%
- [ ] 57-item eval set ≥95% on both hotels; zero fabricated prices in 7 days live
- [ ] Guest gets a reply in ≤6s, in their language, 24/7, with an honest human handoff
- [ ] One-click takeover; guest never notices; full audit trail
- [ ] Kill switch and autonomy switch proven in a drill
- [ ] AI disclosure shown before the first guest answer, on every channel, in every language (EU AI Act Art. 50)
- [ ] Every enabled language has a passing eval set and native-speaker tone sign-off
- [ ] An EU tenant's data provably stays in the EU region
- [ ] No duplicate replies, no lost messages, DLQ reviewed daily
- [ ] Concurrency test green (10 simultaneous messages → one coalesced reply); storage isolation test green
- [ ] Provider-outage drill: primary disabled mid-conversation → secondary answers, or escalation script fires. No silence, no hallucination
- [ ] Every AI answer traceable to prompt version + sources + cost
- [ ] Runbook, retention/DPA, deletion endpoint, PII redaction live
- [ ] WhatsApp BSP approved, one property ready to switch on
- [ ] Value report (after-hours, languages, labour, upsell) shipping monthly
- [ ] Pricing page, LOI and paid-pilot agreement ready to send

---

## 9. Next five working days

1. **Day 1** — Lock the beachhead: **Mexico + Spain**, Spanish and English. **Start from the shipped eval pack (`eval/`)** — 32 canonical + 25 adversarial items in ES/EN, frequency-weighted from published conversation data, runnable today against two synthetic fixtures. Nothing is blocked on hotel access (§9.1). Submit the Meta/BSP applications for both markets.
2. **Day 2** — Schema v1 with RLS and the tenant-isolation test; provisioning flow for a new hotel.
3. **Day 3** — Ingestion, chunking, retrieval on that one hotel's content; wire `ai_runs`.
4. **Day 4** — Eval runner: get a *number* for groundedness. Iterate the prompt twice.
5. **Day 5** — Sign design partners 1–3 (LOI + content + 2h/week). If you cannot get three hotels to hand over content for free this week, the risk is not in the code.

### 9.1 Working without hotel access — the proxy eval pack (added v3.1)

The original Day 1 assumed a real hotel's documents. We do not have them yet. The fix is a **runnable proxy**, shipped as `eval/`:

| Asset | Contents |
|---|---|
| `eval/eval-set-v0.1.csv` | 32 canonical questions in **ES + EN**, with **per-property expected behaviours** (`behaviour_mx` / `behaviour_es`), weighted by published frequency data, each tagged with expected behaviour and its only acceptable source class (`knowledge_qa` / `offers` / retrieved prose) |
| `eval/adversarial-v0.csv` | 25 hostile cases: prompt injection (3), price/availability bait (4), medical/safety (3), complaints (3), PII (2), competitor (2), policy overreach (2), language (2), out-of-scope (2), distress (2) |
| `eval/fixtures/` | Two **fictional** properties — a 34-room beach boutique in Puerto Peñasco and a 48-room city boutique in Sevilla — with approved Q&A, structured offers, prose and **marked gaps** (EV charging, pool heating, upgrade policy), so the "I don't know" path is testable |
| `eval/score_eval.py` | Runnable scorer: template → results → `eval-report.md` with pass rate, groundedness of answers, refusal correctness, weighted coverage, latency |

**The weights are evidence-based, not invented:** wifi 23% and check-in/early arrival 18% of pre-check-in messages (StayPilot, n=500); early/late check-out the largest single request category with timing flexibility in 11.3% of conversations (Runnr, n=10,000); the top five pre-arrival topics at 60–70% of volume (Viqal); departure logistics 26.6% of departure-day messages and 42% of access messages reporting a fault (Conduit); wifi / breakfast / pool-gym-parking hours as the recurring daily five (front-desk analyses); a top-50 topic ranking from 1.7M conversations across 2,100 hotels (HiJiffy).

**v0.1 correction (21 Oct 2026).** v0 wrongly marked EV charging (C18) and pool heating (C22) as deliberate knowledge gaps, but both fixtures answer them. A *sourced* "we have no charger in the hotel" is a correct **answer**, not a refusal — the v0 expectation would have punished the right behaviour. v0.1 makes both answerable and adds two **genuine** gaps the knowledge base cannot answer (pool water temperature in January; accessible-bathroom dimensions), so the decline path is still tested. It also adds per-property overrides, because whether an item is a gap depends on the property. Set is now **32 canonical + 25 adversarial = 57 items**. v0 is retained, never edited in place.

**What the proxy does and does not prove.** It proves the *machinery*: tenant-scoped retrieval, structured-fact precedence, the decline path, refusal correctness, the latency budget, and that two hotels do not bleed into each other. It does **not** prove the concierge is good for any real property — a Coverage Score measured against fixtures is a baseline, never a number to show a GM.

**Replacement protocol — the part that keeps this honest:**

| Version | When | Source | Proves |
|---|---|---|---|
| **v0** | now | Published frequency data + synthetic fixtures | Pipeline, scorer and gates work |
| **v0.5** | week 2–3 | Shadow-mode production traffic | The real question distribution and language mix |
| v1 | week 5–6 | First partner's documents + 2 weeks of real conversations | That property's coverage |
| v1+ | every publish | v1 + rolling sample of unresolved questions (10/week) | Drift and regression |

At v0.5, rank the top 20 real topics and compare with the v0 weights. **If they disagree, the proxy was wrong** — rewrite the weights that week and show the comparison in the review. Never ship v0 weights into a sales conversation as if they were a property's coverage.

**Knock-on risk, stated plainly.** No hotel access also means no design partners, and the ramp model's month-1 units are *signed properties*, not code. The build can run on fixtures for roughly 6–8 weeks; **beyond that, no signed property means no pilot, no conversion and no revenue**, and the 24-month model in §7.4 stops being conservative and becomes fictional. Partner recruitment runs in parallel from week 1 — it is the only task in this plan with no synthetic substitute.

---

### Appendix — model map

| Sheet | Contains |
|---|---|
| `01_Assumptions` | Every global cost and commercial rate (blue cells) |
| `02_Property_Sizes` | Five archetypes: rooms, engagement, price, mix + derived metrics |
| `03_Unit_Economics` | Per-size P&L, COGS, gross margin, payback, LTV/CAC + blended row |
| `04_Messaging_Costs` | WhatsApp rates by market; cost per size × market; cost per 100 conversations |
| `05_Ramp` | 24 monthly rows × 3 scenarios (pilots in, everything else derived) + summaries |
| `06_Scenarios` | Side-by-side outcome table pulled live from `05` |
| `07_Sensitivity` | Margin vs support load, LTV/CAC vs churn, breakeven count, market cost, break-points |
| `08_Cash_Runway` | Cumulative cash curve by scenario + staffing reality check + funding requirement |
| `09_Market_Sizing` | Hotel counts by market, filters to target segment and serviceable, ARR pool, penetration scenarios, channel fit, compliance matrix |

Companion directory **`eval/`** — eval set v0, adversarial set v0, two synthetic fixtures, runnable scorer (§9.1).
| `07_Sensitivity` F/G/H | Support-load × labour-rate stress, high-touch onboarding, token inflation (added v2.1) |
