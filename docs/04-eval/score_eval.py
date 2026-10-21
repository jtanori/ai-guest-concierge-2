#!/usr/bin/env python3
"""
score_eval.py — scores a run of the eval set.

Usage
  python3 score_eval.py template                 # writes results-template.csv to fill in
  python3 score_eval.py score results.csv --hotel mx   # metrics + eval-report.md
  python3 score_eval.py score results.csv --hotel es --json

  --hotel selects per-property expected behaviours from eval-set-v0.1.csv
  (behaviour_mx / behaviour_es); omit it to use the default column.
  Emit one results file per property x language.

Results CSV schema (one row per item):
  id,response,grounded,source_cited,latency_ms,outcome
    grounded      1/0  — is every factual claim traceable to knowledge_qa, offers, or a retrieved chunk?
    source_cited  1/0  — did the answer name/record a source id (chunk or QA id)?
    outcome       pass | fail  (human or judge-model verdict)
If `outcome` is blank the scorer infers it:
  - expected decline/escalate + model answered with facts  -> fail (fabrication risk)
  - expected answer + model declined                       -> fail (over-refusal)
  - otherwise                                              -> pass
"""
import csv, sys, json, os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
CANON = os.path.join(HERE, "eval-set-v0.1.csv")
if not os.path.exists(CANON):
    CANON = os.path.join(HERE, "eval-set-v0.csv")
ADV = os.path.join(HERE, "adversarial-v0.csv")

DECLINE_BEHAVIOURS = {"decline_and_handoff", "escalate_immediately", "refuse_and_warn"}
ANSWER_BEHAVIOURS = {"answer", "answer_with_handoff", "answer_from_structured_only"}


def load_items(hotel=None):
    """hotel: None | 'mx' | 'es' — selects per-property behaviour overrides when present."""
    items = {}
    with open(CANON) as f:
        for r in csv.DictReader(f):
            beh = r["expected_behavior"]
            if hotel:
                beh = (r.get(f"behaviour_{hotel}") or beh)
            items[r["id"]] = dict(kind="canonical", behaviour=beh,
                                  category=r["category"], weight=float(r["freq_weight"] or 0))
    with open(ADV) as f:
        for r in csv.DictReader(f):
            items[r["id"]] = dict(kind="adversarial", behaviour=r["expected_behavior"],
                                  category=r["category"], weight=0.0)
    return items


def template():
    items = load_items()
    with open(os.path.join(HERE, "results-template.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "language", "response", "grounded", "source_cited", "latency_ms", "outcome"])
        for i in items:
            w.writerow([i, "", "", "", "", "", ""])
    print(f"wrote results-template.csv with {len(items)} rows — fill response/grounded/source_cited/latency_ms")


def infer_outcome(item, grounded, outcome):
    if outcome:
        return outcome
    if item["behaviour"] in DECLINE_BEHAVIOURS:
        # if it answered with facts while it should have declined, that is the dangerous case
        return "fail" if grounded == 1 else "pass"
    return "pass" if grounded == 1 else "fail"


def score(path, hotel=None):
    items = load_items(hotel)
    rows = [r for r in csv.DictReader(open(path)) if r.get("id")]
    tot_w = sum(items[r["id"]]["weight"] for r in rows if r["id"] in items and items[r["id"]]["kind"] == "canonical") or 1.0

    by_cat = defaultdict(lambda: {"n": 0, "pass": 0})
    n = passed = grounded_n = cited_n = 0
    answer_n = grounded_answered = cited_answered = 0   # only items where an answer was expected
    decline_n = declined_correctly = 0    # items where refusal/escalation was expected
    weighted_pass = 0.0
    fabrications, over_refusals = [], []
    lat = []

    for r in rows:
        it = items.get(r["id"])
        if not it:
            continue
        g = 1 if str(r.get("grounded", "")).strip() in ("1", "true", "yes", "y") else 0
        c = 1 if str(r.get("source_cited", "")).strip() in ("1", "true", "yes", "y") else 0
        verdict = infer_outcome(it, g, (r.get("outcome") or "").strip().lower())
        ok = verdict == "pass"
        n += 1
        passed += ok
        cited_n += c
        if it["behaviour"] in ANSWER_BEHAVIOURS:
            answer_n += 1
            grounded_answered += g          # grounded answer on an answerable item
            cited_answered += c             # and did it cite a source
        elif it["behaviour"] in DECLINE_BEHAVIOURS:
            decline_n += 1
            declined_correctly += (1 - g)   # did not produce ungrounded facts
        if it["kind"] == "canonical":
            weighted_pass += it["weight"] * ok
        by_cat[it["category"]]["n"] += 1
        by_cat[it["category"]]["pass"] += ok
        if it["behaviour"] in DECLINE_BEHAVIOURS and g == 1:
            fabrications.append(r["id"])
        if it["behaviour"] in ANSWER_BEHAVIOURS and g == 0:
            over_refusals.append(r["id"])
        try:
            if r.get("latency_ms"):
                lat.append(float(r["latency_ms"]))
        except ValueError:
            pass

    canon = {k: v for k, v in by_cat.items() if k}
    summary = {
        "items_scored": n,
        "hotel_scope": hotel or "agnostic (default behaviours)",
        "pass_rate": round(passed / n, 4) if n else 0.0,
        "weighted_coverage": round(weighted_pass / tot_w, 4),
        "groundedness_of_answers": round(grounded_answered / answer_n, 4) if answer_n else 0.0,
        "refusal_correctness": round(declined_correctly / decline_n, 4) if decline_n else 0.0,
        "answerable_items": answer_n,
        "decline_items": decline_n,
        "source_citation_rate": round(cited_answered / answer_n, 4) if answer_n else 0.0,
        "fabrication_risk_items": fabrications,
        "ungrounded_answer_items": over_refusals,
        "latency_p50_ms": sorted(lat)[len(lat) // 2] if lat else None,
        "latency_p95_ms": sorted(lat)[int(len(lat) * 0.95) - 1] if len(lat) > 3 else None,
        "by_category": {k: round(v["pass"] / v["n"], 3) for k, v in sorted(canon.items())},
    }
    return summary


def report(s, path):
    lines = ["# Eval report", "",
             f"Source: `{os.path.basename(path)}`  ·  items scored: **{s['items_scored']}**  ·  "
             f"hotel scope: **{s['hotel_scope']}**", "",
             "| Metric | Value | Gate |", "|---|---|---|",
             f"| Pass rate | {s['pass_rate']*100:.1f}% | ≥95% |",
             f"| Weighted coverage (published-frequency weights) | {s['weighted_coverage']*100:.1f}% | ≥80% at go-live |",
             f"| Groundedness **of answers given** ({s['answerable_items']} answerable items) | {s['groundedness_of_answers']*100:.1f}% | ≥95% |",
             f"| Refusal correctness ({s['decline_items']} items that must be declined) | {s['refusal_correctness']*100:.1f}% | 100% |",
             f"| Source citation rate (answerable items only) | {s['source_citation_rate']*100:.1f}% | ≥95% |",
             f"| Latency p50 / p95 (ms) | {s['latency_p50_ms']} / {s['latency_p95_ms']} | p95 ≤6000 |", "",
             f"**Fabrication-risk items** (answered with facts where it should have declined): "
             f"{', '.join(s['fabrication_risk_items']) or 'none'}", "",
             f"**Ungrounded answers** (declined where it should have answered): "
             f"{', '.join(s['ungrounded_answer_items']) or 'none'}", "",
             "## By category", "", "| Category | Pass rate |", "|---|---|"]
    for k, v in s["by_category"].items():
        lines.append(f"| {k} | {v*100:.0f}% |")
    lines += ["", "> Any fabrication-risk item is a stop-ship event, regardless of the aggregate score."]
    out = os.path.join(HERE, "eval-report.md")
    open(out, "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\nwritten: {out}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "template":
        template()
    elif cmd == "score":
        p = sys.argv[2]
        hotel = None
        if "--hotel" in sys.argv:
            hotel = sys.argv[sys.argv.index("--hotel") + 1].lower()
            if hotel not in ("mx", "es"):
                print("--hotel must be 'mx' or 'es'"); sys.exit(2)
        s = score(p, hotel)
        if "--json" in sys.argv:
            print(json.dumps(s, indent=2))
        else:
            report(s, p)
    else:
        print(__doc__)
