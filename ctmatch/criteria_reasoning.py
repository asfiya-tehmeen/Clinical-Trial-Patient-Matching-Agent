"""
criteria_reasoning.py
=====================
Criteria Reasoning Agent (uses the reasoning model) — the core of the pipeline.

For each trial, the model checks every inclusion/exclusion criterion and assigns
one of four verdicts: PASS / FAIL / UNCERTAIN / MISSING_DATA.
"""

import json
import time

from .config import call_llm, clean_json, MODEL_REASONING

CRITERIA_PROMPT = """
You are a clinical trial eligibility specialist with deep knowledge of
oncology trial protocols.

PATIENT PROFILE:
{patient_json}

CLINICAL TRIAL: {nct_id}
Title: {title}

ELIGIBILITY CRITERIA:
{eligibility_text}

For each inclusion and exclusion criterion, determine if this patient meets it.
Return ONLY valid JSON — no preamble, no markdown fences.

{{
  "trial_nct_id": "{nct_id}",
  "overall_eligible": true | false | "uncertain",
  "criteria_results": [
    {{
      "criterion_text": "<exact criterion text, shortened to 80 chars>",
      "type": "inclusion" | "exclusion",
      "verdict": "PASS" | "FAIL" | "UNCERTAIN" | "MISSING_DATA",
      "confidence": <float 0.0-1.0>,
      "reasoning": "<one sentence citing specific patient data>",
      "missing_info": "<if MISSING_DATA: what test or info resolves this, else null>"
    }}
  ],
  "disqualifying_criteria": ["<criterion text if FAIL>"],
  "uncertain_criteria": ["<criterion text if UNCERTAIN>"],
  "missing_data_requests": ["<actionable test or data needed, if any>"],
  "match_summary": "<2 sentence plain-English summary for a physician>"
}}

Rules:
- PASS         = patient clearly meets this criterion based on available data
- FAIL         = patient clearly does NOT meet this criterion (disqualifying)
- UNCERTAIN    = ambiguous — not enough info to decide either way
- MISSING_DATA = patient may qualify but a specific piece of data is absent
- If ANY inclusion criterion is FAIL → overall_eligible = false
- If ANY exclusion criterion is PASS (patient HAS the exclusion) → overall_eligible = false
- Be specific — cite actual values (e.g. "ECOG 1 meets PS 0-2 requirement")
"""


def reason_over_trial(trial: dict, patient_profile: dict) -> dict:
    """Run reasoning over a single trial's eligibility criteria."""
    prompt = CRITERIA_PROMPT.format(
        patient_json     = json.dumps(patient_profile, indent=2),
        nct_id           = trial["nct_id"],
        title            = trial["title"],
        eligibility_text = trial["eligibility_text"][:2500],
    )
    try:
        raw = call_llm(prompt, MODEL_REASONING, max_tokens=2000)
        result = clean_json(raw)
        result["trial_title"] = trial["title"]
        result["trial_phase"] = trial["phase"]
        result["trial_url"]   = trial["url"]
        result["trial_sites"] = trial["sites"]
        result["sponsor"]     = trial["sponsor"]
        return result
    except Exception as e:
        return {
            "trial_nct_id"         : trial["nct_id"],
            "trial_title"          : trial["title"],
            "overall_eligible"     : False,
            "criteria_results"     : [],
            "match_summary"        : f"Parsing error: {e}",
            "missing_data_requests": [],
            "error"                : str(e),
        }


def reason_over_all_trials(pre_filtered: list, patient_profile: dict) -> list:
    """Run reasoning across every pre-filtered trial."""
    print(f"🤖 Running {MODEL_REASONING} reasoning on {len(pre_filtered)} trials...")
    print("   (~5–10 sec per trial — grab a coffee ☕)\n")

    all_results = []
    for i, trial in enumerate(pre_filtered):
        print(f"   [{i+1}/{len(pre_filtered)}] {trial['nct_id']} — {trial['title'][:55]}...")
        all_results.append(reason_over_trial(trial, patient_profile))
        time.sleep(0.5)

    print(f"\n✅ Reasoning complete on {len(all_results)} trials")
    return all_results
