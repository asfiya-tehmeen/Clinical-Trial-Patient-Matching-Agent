"""
ehr_extraction.py
=================
EHR Extraction Agent (uses the fast model).

Converts a free-text clinical note into a structured JSON patient profile
(demographics, biomarkers, labs, meds, ECOG, prior treatments, search terms).
"""

import json

from .config import call_llm, clean_json, MODEL_FAST

EXTRACTION_PROMPT = """
You are a clinical NLP specialist. Extract structured information from
this clinical note. Return ONLY valid JSON — no preamble, no markdown fences.

Extract exactly this schema:
{{
  "demographics": {{
    "age": <int>,
    "sex": "<M or F>",
    "location": "<city, state, country>"
  }},
  "primary_diagnosis": {{
    "name": "<full diagnosis name>",
    "icd10_guess": "<best ICD-10 code>",
    "stage": "<stage if available>",
    "histology": "<histology if available>"
  }},
  "biomarkers": [
    {{"name": "<biomarker>", "value": "<result>", "status": "<positive/negative/numeric>"}}
  ],
  "medications": [
    {{"name": "<drug name>", "dose": "<dose>", "frequency": "<frequency>"}}
  ],
  "labs": [
    {{"name": "<lab name>", "value": "<value>", "unit": "<unit>"}}
  ],
  "ecog_status": <int 0-4>,
  "prior_treatments": ["<treatment 1>", "<treatment 2>"],
  "comorbidities": ["<condition 1>", "<condition 2>"],
  "exclusion_flags": ["<anything that commonly excludes patients from trials>"],
  "key_search_terms": ["<3-6 best search terms for finding relevant trials>"]
}}

Clinical note:
\"\"\"
{ehr_text}
\"\"\"
"""


def extract_patient_profile(ehr_text: str) -> dict:
    """Run EHR extraction with the fast model → structured patient profile dict."""
    print("🔍 Running EHR extraction with %s (Groq)..." % MODEL_FAST)
    raw = call_llm(EXTRACTION_PROMPT.format(ehr_text=ehr_text), MODEL_FAST)
    return clean_json(raw)


if __name__ == "__main__":
    from .patients import ACTIVE_PATIENT
    profile = extract_patient_profile(ACTIVE_PATIENT)
    print("\n📋 Structured patient profile:")
    print(json.dumps(profile, indent=2))
