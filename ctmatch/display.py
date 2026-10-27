"""
display.py
==========
Physician-facing output: ranked match cards, the missing-data action plan,
a results summary table, and JSON export.

  - print_match_card()        : one ranked trial card
  - print_results()           : header + top-K cards
  - print_missing_data_plan() : aggregated "order these tests" plan
  - build_summary_table()     : pandas DataFrame of all results
  - export_results()          : write the full run to JSON
"""

import json
import os
from datetime import datetime

import pandas as pd

from .config import MODEL_FAST, MODEL_REASONING, TOP_K


def verdict_icon(v):
    return {"PASS": "✅", "FAIL": "❌", "UNCERTAIN": "⚠️ ", "MISSING_DATA": "🔬"}.get(v, "❓")


# ------------------------------------------------------------------
# Ranked match cards
# ------------------------------------------------------------------
def print_match_card(result: dict, rank: int):
    score = result["match_score"]
    bar   = "█" * int(score * 10) + "░" * (10 - int(score * 10))

    print(f"\n{'='*65}")
    print(f"  MATCH #{rank}  |  Score: {score:.0%}  [{bar}]")
    print(f"{'='*65}")
    print(f"  📋 {result['trial_title']}")
    print(f"  🔑 {result.get('trial_nct_id','N/A')}  |  Phase: {result.get('trial_phase','?')}  |  Sponsor: {result.get('sponsor','?')[:38]}")
    if result.get("trial_sites"):
        print(f"  📍 Sites: {', '.join(result['trial_sites'][:3])}")
    print(f"  🔗 {result.get('trial_url','')}")

    print("\n  📝 Summary:")
    summary = result.get("match_summary", "")
    for line in [summary[i:i+62] for i in range(0, len(summary), 62)]:
        print(f"     {line}")

    criteria = result.get("criteria_results", [])
    if criteria:
        print(f"\n  📊 Criteria breakdown ({len(criteria)} checked):")
        for c in criteria[:8]:
            icon = verdict_icon(c["verdict"])
            text = c["criterion_text"][:55]
            print(f"     {icon}  {text}")
            if c.get("reasoning"):
                print(f"        └─ {c['reasoning'][:70]}")
        if len(criteria) > 8:
            print(f"        ... and {len(criteria)-8} more criteria checked")

    missing = result.get("missing_data_requests", [])
    if missing:
        print("\n  🔬 Missing data — order these to confirm eligibility:")
        for m in missing:
            print(f"     → {m}")


def print_results(eligible: list, patient_profile: dict, ineligible: list, top_k: int = TOP_K):
    """Print the header banner and the top-K ranked match cards."""
    print("\n" + "█"*65)
    print("  CLINICAL TRIAL MATCHING RESULTS  [powered by Groq]")
    print(f"  Patient: {patient_profile['demographics']['age']}y {patient_profile['demographics']['sex']}  |  Dx: {patient_profile['primary_diagnosis']['name']}")
    print("█"*65)

    if not eligible:
        print("\n  ⚠️  No eligible trials found in this search batch.")
        print("  Try adjusting search terms or expanding MAX_TRIALS in config.py.")
    else:
        for i, match in enumerate(eligible[:top_k], 1):
            print_match_card(match, i)

    print(f"\n{'─'*65}")
    print(f"  Disqualified: {len(ineligible)}  |  Eligible: {len(eligible)}")
    print(f"  Showing top {min(top_k, len(eligible))} of {len(eligible)} eligible matches")
    print(f"{'─'*65}")


# ------------------------------------------------------------------
# Missing data action plan
# ------------------------------------------------------------------
def build_missing_data(eligible: list, ineligible: list) -> dict:
    """Aggregate missing-data requests across all trials → {test: [nct_ids]}."""
    all_missing = {}
    for result in eligible + ineligible:
        for item in result.get("missing_data_requests", []):
            all_missing.setdefault(item, []).append(result.get("trial_nct_id", ""))
    return all_missing


def print_missing_data_plan(all_missing: dict):
    if all_missing:
        print("\n" + "="*65)
        print("  🔬 MISSING DATA ACTION PLAN")
        print("  Order these tests to potentially unlock more trial matches:")
        print("="*65)
        for test, trials in sorted(all_missing.items(), key=lambda x: -len(x[1])):
            print(f"\n  → {test}")
            print(f"     Relevant to: {', '.join(trials[:4])}")
        print()
    else:
        print("\n✅ No critical missing data identified.")


# ------------------------------------------------------------------
# Summary table
# ------------------------------------------------------------------
def build_summary_table(all_results: list) -> pd.DataFrame:
    rows = []
    for r in all_results:
        criteria = r.get("criteria_results", [])
        rows.append({
            "NCT ID"    : r.get("trial_nct_id", ""),
            "Title"     : r.get("trial_title", "")[:45],
            "Phase"     : r.get("trial_phase", ""),
            "Score"     : f"{r['match_score']:.0%}",
            "PASS"      : sum(1 for c in criteria if c["verdict"] == "PASS"),
            "FAIL"      : sum(1 for c in criteria if c["verdict"] == "FAIL"),
            "UNCERTAIN" : sum(1 for c in criteria if c["verdict"] == "UNCERTAIN"),
            "MISSING"   : sum(1 for c in criteria if c["verdict"] == "MISSING_DATA"),
            "Eligible"  : "✅" if r["match_score"] > 0 else "❌",
        })
    return pd.DataFrame(rows).sort_values("Score", ascending=False)


# ------------------------------------------------------------------
# JSON export
# ------------------------------------------------------------------
def export_results(patient_profile, parsed_trials, pre_filtered, all_results,
                   eligible, ineligible, all_missing,
                   output_path="trial_matching_results.json", top_k=TOP_K):
    output = {
        "generated_at"   : datetime.now().isoformat(),
        "model_used"     : {"extraction": MODEL_FAST, "reasoning": MODEL_REASONING},
        "patient_summary": {
            "age"      : patient_profile["demographics"]["age"],
            "sex"      : patient_profile["demographics"]["sex"],
            "diagnosis": patient_profile["primary_diagnosis"]["name"],
            "ecog"     : patient_profile["ecog_status"],
        },
        "search_stats": {
            "trials_fetched"     : len(parsed_trials),
            "after_pre_filter"   : len(pre_filtered),
            "after_llm_reasoning": len(all_results),
            "eligible"           : len(eligible),
            "ineligible"         : len(ineligible),
        },
        "top_matches" : eligible[:top_k],
        "missing_data": all_missing,
        "all_results" : all_results,
    }

    out_dir = os.path.dirname(os.path.abspath(output_path))
    os.makedirs(out_dir, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=str)

    print(f"✅ Results saved to: {output_path}")
    return output_path
