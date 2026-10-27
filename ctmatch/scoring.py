"""
scoring.py
==========
Composite match scoring and ranking.

  - score_trial()   : turn one reasoning result into a 0.0–1.0 score
  - score_and_rank() : score all results, split into eligible / ineligible
"""


def score_trial(result: dict) -> float:
    """
    Composite match score (0.0 – 1.0).
    Any hard FAIL → 0.0. Otherwise: pass rate minus uncertainty penalty + phase bonus.
    """
    if result.get("overall_eligible") == False:
        return 0.0

    criteria = result.get("criteria_results", [])
    if not criteria:
        return 0.0

    total     = len(criteria)
    passes    = sum(1 for c in criteria if c["verdict"] == "PASS")
    fails     = sum(1 for c in criteria if c["verdict"] == "FAIL")
    uncertain = sum(1 for c in criteria if c["verdict"] in ("UNCERTAIN", "MISSING_DATA"))

    if fails > 0:
        return 0.0

    pass_rate       = passes / total
    uncertainty_pen = (uncertain / total) * 0.25

    phase_map   = {"PHASE3": 0.10, "PHASE2": 0.05, "PHASE1": 0.0, "N/A": 0.0}
    phase_str   = result.get("trial_phase", "N/A").replace(" ", "").upper()
    phase_bonus = phase_map.get(phase_str, 0.0)

    return round(min(1.0, pass_rate - uncertainty_pen + phase_bonus), 3)


def score_and_rank(all_results: list):
    """Score every result, then return (eligible_sorted, ineligible)."""
    for r in all_results:
        r["match_score"] = score_trial(r)

    eligible = sorted(
        [r for r in all_results if r["match_score"] > 0],
        key=lambda x: x["match_score"],
        reverse=True,
    )
    ineligible = [r for r in all_results if r["match_score"] == 0]

    print("✅ Scoring complete")
    print(f"   Eligible / uncertain : {len(eligible)}")
    print(f"   Disqualified         : {len(ineligible)}")
    return eligible, ineligible
