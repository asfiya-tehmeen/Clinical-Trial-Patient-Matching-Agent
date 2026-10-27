"""
trial_search.py
===============
Trial retrieval and cheap filtering.

  - search_clinicaltrials() : multi-strategy query against ClinicalTrials.gov v2 API
  - parse_trial()           : flatten one raw protocolSection into a clean dict
  - parse_all_trials()      : parse + keep only trials that have eligibility text
  - pre_filter()            : hard age/sex elimination (no LLM cost)
"""

import time
import requests

from .config import CTGOV_URL, MAX_TRIALS


# ------------------------------------------------------------------
# Search
# ------------------------------------------------------------------
def search_clinicaltrials(query_terms: list, condition: str, max_results: int = MAX_TRIALS) -> list:
    """Query ClinicalTrials.gov v2 API with multiple strategies, deduplicate results."""
    all_trials = {}
    search_queries = [condition] + query_terms[:3]

    for query in search_queries:
        params = {
            "query.cond"          : query,
            "filter.overallStatus": "RECRUITING",
            "fields"              : ",".join([
                "NCTId", "BriefTitle", "OfficialTitle",
                "EligibilityCriteria", "OverallStatus",
                "Phase", "LocationCity", "LocationCountry",
                "LeadSponsorName", "BriefSummary",
                "MinimumAge", "MaximumAge", "Sex",
                "PointOfContactOrganization", "PointOfContactEMail"
            ]),
            "pageSize"   : 15,
            "countTotal" : "true"
        }
        try:
            resp = requests.get(CTGOV_URL, params=params, timeout=15)
            resp.raise_for_status()
            data    = resp.json()
            studies = data.get("studies", [])
            for s in studies:
                proto  = s.get("protocolSection", {})
                id_mod = proto.get("identificationModule", {})
                nct_id = id_mod.get("nctId", "")
                if nct_id and nct_id not in all_trials:
                    all_trials[nct_id] = proto
            print(f"   Query '{query[:45]}' → {len(studies)} trials")
        except Exception as e:
            print(f"   ⚠ Query failed: {e}")
        time.sleep(0.3)

    print(f"✅ Total unique trials fetched: {len(all_trials)}")
    return list(all_trials.values())[:max_results]


# ------------------------------------------------------------------
# Parse
# ------------------------------------------------------------------
def parse_trial(proto: dict) -> dict:
    """Flatten a ClinicalTrials.gov protocolSection into a clean usable dict."""
    id_mod      = proto.get("identificationModule", {})
    status_mod  = proto.get("statusModule", {})
    desc_mod    = proto.get("descriptionModule", {})
    elig_mod    = proto.get("eligibilityModule", {})
    design_mod  = proto.get("designModule", {})
    sponsor_mod = proto.get("sponsorCollaboratorsModule", {})
    contact_mod = proto.get("contactsLocationsModule", {})

    locations = contact_mod.get("locations", [])
    cities = list({
        loc.get("city", "") + ", " + loc.get("country", "")
        for loc in locations[:5] if loc.get("city")
    })

    phases = design_mod.get("phases", ["N/A"])
    phase  = phases[0] if phases else "N/A"

    return {
        "nct_id"          : id_mod.get("nctId", ""),
        "title"           : id_mod.get("briefTitle", ""),
        "official_title"  : id_mod.get("officialTitle", ""),
        "status"          : status_mod.get("overallStatus", ""),
        "phase"           : phase,
        "sponsor"         : sponsor_mod.get("leadSponsor", {}).get("name", ""),
        "brief_summary"   : desc_mod.get("briefSummary", "")[:500],
        "eligibility_text": elig_mod.get("eligibilityCriteria", "")[:3000],
        "min_age"         : elig_mod.get("minimumAge", ""),
        "max_age"         : elig_mod.get("maximumAge", ""),
        "sex"             : elig_mod.get("sex", "ALL"),
        "sites"           : cities,
        "url"             : f"https://clinicaltrials.gov/study/{id_mod.get('nctId', '')}"
    }


def parse_all_trials(raw_trials: list) -> list:
    """Parse all raw trials and keep only those that carry eligibility text."""
    parsed = [parse_trial(t) for t in raw_trials]
    parsed = [t for t in parsed if t["eligibility_text"]]
    print(f"✅ Parsed {len(parsed)} trials with eligibility text")
    return parsed


# ------------------------------------------------------------------
# Hard pre-filter (no LLM)
# ------------------------------------------------------------------
def age_passes(age: int, min_age_str: str, max_age_str: str) -> bool:
    def parse_age(s):
        if not s:
            return None
        digits = ''.join(filter(str.isdigit, s.split()[0]))
        return int(digits) if digits else None
    lo = parse_age(min_age_str)
    hi = parse_age(max_age_str)
    if lo and age < lo:
        return False
    if hi and age > hi:
        return False
    return True


def sex_passes(patient_sex: str, trial_sex: str) -> bool:
    if trial_sex.upper() in ("ALL", ""):
        return True
    return patient_sex.upper()[0] == trial_sex.upper()[0]


def pre_filter(parsed_trials: list, patient_profile: dict) -> list:
    """Remove obvious age/sex mismatches before expensive LLM reasoning."""
    patient_age = patient_profile["demographics"]["age"]
    patient_sex = patient_profile["demographics"]["sex"]

    pre_filtered = []
    removed      = []
    for trial in parsed_trials:
        age_ok = age_passes(patient_age, trial["min_age"], trial["max_age"])
        sex_ok = sex_passes(patient_sex, trial["sex"])
        if age_ok and sex_ok:
            pre_filtered.append(trial)
        else:
            reason = []
            if not age_ok:
                reason.append(f"age {patient_age} outside {trial['min_age']}–{trial['max_age']}")
            if not sex_ok:
                reason.append(f"sex {patient_sex} vs {trial['sex']}")
            removed.append((trial["nct_id"], ", ".join(reason)))

    print(f"✅ Pre-filter: {len(parsed_trials)} → {len(pre_filtered)} trials")
    if removed:
        print(f"   Removed {len(removed)} trials:")
        for nct, reason in removed[:5]:
            print(f"   ✗ {nct}: {reason}")
    return pre_filtered
