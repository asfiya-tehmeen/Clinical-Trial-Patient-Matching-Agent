"""
pipeline.py
===========
End-to-end orchestrator. run_pipeline() calls every stage in order:

    EHR extraction → trial search → parse → pre-filter →
    criteria reasoning → scoring → display + export
"""

from .patients import ACTIVE_PATIENT
from .config import MAX_TRIALS, TOP_K
from .ehr_extraction import extract_patient_profile
from .trial_search import search_clinicaltrials, parse_all_trials, pre_filter
from .criteria_reasoning import reason_over_all_trials
from .scoring import score_and_rank
from .display import (
    print_results,
    build_missing_data,
    print_missing_data_plan,
    build_summary_table,
    export_results,
)


def run_pipeline(ehr_text: str = ACTIVE_PATIENT, max_trials: int = MAX_TRIALS,
                 top_k: int = TOP_K, output_path: str = "trial_matching_results.json",
                 show_table: bool = True):
    # 1. Structured profile from free-text EHR
    patient_profile = extract_patient_profile(ehr_text)

    # 2. Search ClinicalTrials.gov
    condition    = patient_profile["primary_diagnosis"]["name"]
    search_terms = patient_profile.get("key_search_terms", [])
    print(f"\n🔎 Searching trials for: {condition}")
    print(f"   Additional terms: {search_terms}")
    raw_trials = search_clinicaltrials(search_terms, condition, max_results=max_trials)

    # 3. Parse + 4. hard pre-filter
    parsed_trials = parse_all_trials(raw_trials)
    pre_filtered  = pre_filter(parsed_trials, patient_profile)

    # 5. Criteria reasoning
    all_results = reason_over_all_trials(pre_filtered, patient_profile)

    # 6. Score + rank
    eligible, ineligible = score_and_rank(all_results)

    # 7. Output
    print_results(eligible, patient_profile, ineligible, top_k=top_k)
    all_missing = build_missing_data(eligible, ineligible)
    print_missing_data_plan(all_missing)

    if show_table and all_results:
        df = build_summary_table(all_results)
        print("\n📊 Full results table:\n")
        print(df.to_string(index=False))

    export_results(patient_profile, parsed_trials, pre_filtered, all_results,
                   eligible, ineligible, all_missing,
                   output_path=output_path, top_k=top_k)

    return {
        "patient_profile": patient_profile,
        "eligible"       : eligible,
        "ineligible"     : ineligible,
        "missing_data"   : all_missing,
    }
