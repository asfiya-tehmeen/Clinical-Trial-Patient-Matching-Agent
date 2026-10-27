# 🏥 Clinical Trial Patient Matching Agent

> An agentic AI pipeline that matches patients to recruiting clinical trials by reasoning over eligibility criteria — returning ranked matches with per-criterion verdicts, confidence scores, and an actionable missing-data plan for physicians.

---

## 📌 Table of Contents

- [Overview](#-overview)
- [The Problem](#-the-problem)
- [How It Works](#-how-it-works)
- [Novel Contribution](#-novel-contribution)
- [Pipeline Architecture](#-pipeline-architecture)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
- [Running the Notebook](#-running-the-notebook)
- [Example Output](#-example-output)
- [Project Structure](#-project-structure)
- [Future Work](#-future-work)
- [Research & Publication](#-research--publication)
- [License](#-license)

---

## 🔍 Overview

Clinical trial recruitment is one of the most critical bottlenecks in drug development. This project builds an end-to-end **agentic AI pipeline** that:

1. Reads a patient's de-identified EHR summary in plain text
2. Extracts a structured clinical profile using LLM-based NLP
3. Searches 400,000+ recruiting trials on ClinicalTrials.gov in real time
4. Reasons over every inclusion and exclusion criterion per trial
5. Returns a ranked shortlist with plain-English explanations and an actionable missing-data plan

Runs as a command-line tool (`ctmatch`) or a notebook — one free API key.

---

## 🚨 The Problem

| Stat | Source |
|------|--------|
| 85% of clinical trials are delayed due to recruitment problems | Tufts CSDD |
| 70%+ of eligible patients never enroll in a trial they qualify for | NIH |
| Average trial recruitment takes 2–3x longer than planned | FDA |

The core issue is a **matching gap** — not a patient shortage. Patients exist. Trials exist. But manually screening eligibility criteria across hundreds of trials per patient is clinically infeasible. Existing tools do keyword search. This system does **criterion-level reasoning**.

---

## ⚙️ How It Works

```
Free-text EHR note
        ↓
[ EHR Extraction Agent ]  →  Structured patient profile (JSON)
        ↓
[ ClinicalTrials.gov Search ]  →  Multi-strategy API search (400k+ trials)
        ↓
[ Hard Pre-filter ]  →  Age / sex / status elimination (no LLM cost)
        ↓
[ Criteria Reasoning Agent ]  →  Per-criterion PASS / FAIL / UNCERTAIN / MISSING_DATA
        ↓
[ Scoring & Ranking ]  →  Composite match score (0–100%)
        ↓
[ Ranked Output ]  →  Match cards + explanations + missing data action plan
```

---

## 💡 Novel Contribution

Most trial matching systems return a list based on keyword overlap. This system introduces a **4-verdict reasoning schema** applied at the criterion level:

| Verdict | Meaning | Clinical Value |
|---------|---------|----------------|
| ✅ `PASS` | Patient clearly meets this criterion | Confirms eligibility |
| ❌ `FAIL` | Patient is disqualified on this criterion | Hard exclusion |
| ⚠️ `UNCERTAIN` | Ambiguous — not enough data to decide | Flags for physician review |
| 🔬 `MISSING_DATA` | Patient may qualify but a specific test is absent | **Generates an actionable test order** |

The `MISSING_DATA` verdict is the key innovation. Instead of silently excluding a patient when data is absent, the system tells the physician **exactly what test to order** to resolve eligibility. No existing open-source tool does this.

---

## 🏗️ Pipeline Architecture

```
┌─────────────────────────────────────────┐
│          De-identified EHR Input         │
│  Age, Dx, Labs, Meds, History, ECOG     │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│          EHR Extraction Agent            │
│  LLaMA-3.1-8b → Structured JSON Profile │
│  (demographics, biomarkers, labs, meds) │
└──────────────────┬──────────────────────┘
                   ↓
        ┌──────────┴──────────┐
        ↓                     ↓
┌───────────────┐   ┌──────────────────────┐
│  Condition    │   │  Semantic Search     │
│  API Search   │   │  (ChromaDB embeddings│
│  ClinTrials   │   │  over eligibility)   │
└───────┬───────┘   └──────────┬───────────┘
        └──────────┬───────────┘
                   ↓
┌─────────────────────────────────────────┐
│           Hard Pre-filter                │
│     Age range / Sex / Status check      │
│         (no LLM — instant)              │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│       Criteria Reasoning Agent           │
│  LLaMA-3.3-70b → Per-criterion verdicts │
│  PASS / FAIL / UNCERTAIN / MISSING_DATA │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│         Scoring & Ranking                │
│  Pass rate + Phase bonus + Uncertainty  │
│  penalty → Composite match score        │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│       Physician-facing Output            │
│  Ranked matches + Evidence + Actions    │
└─────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Agent framework | LangGraph |
| LLM — fast tasks | LLaMA 3.1 8B (via Groq) |
| LLM — reasoning | LLaMA 3.3 70B (via Groq) |
| Vector search | ChromaDB |
| Trial database | ClinicalTrials.gov v2 API |
| Backend | FastAPI |
| Notebook | Google Colab |
| Language | Python 3.10+ |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- A free Groq API key → [console.groq.com](https://console.groq.com)

### API Keys

| Service | Key Required | Cost | Get It |
|---------|-------------|------|--------|
| Groq | ✅ Yes | Free tier | [console.groq.com](https://console.groq.com) |
| ClinicalTrials.gov | ❌ No | Free | — |

### Install

```bash
git clone <your-repo-url>
cd clinicaltrialagent
pip install .          # or `pip install -e .` for development
ctmatch init           # paste your Groq key (saved to ~/.ctmatch.env)
ctmatch check          # verify the key works
```

You can instead set `GROQ_API_KEY` as an environment variable or put it in a `.env` file (see `.env.example`).

## 💻 Usage

```bash
ctmatch samples                         # list built-in sample patients
ctmatch match --sample A_nsclc          # run on a sample patient
ctmatch match --file my_note.txt        # run on your own de-identified EHR note
cat note.txt | ctmatch match -          # read the note from stdin
ctmatch match -f note.txt --max-trials 40 --top-k 10 -o results.json
```

`python -m ctmatch ...` works too. Results are printed and saved to JSON
(default `trial_matching_results.json`).

Optional env vars: `CTMATCH_MODEL_FAST`, `CTMATCH_MODEL_REASONING`, `CTMATCH_DEBUG=1` (full tracebacks).

A notebook entry point (`ClinicalTrialMatching.ipynb`) is still included for Colab use.

> ⚠️ Only use de-identified data. Note text is sent to Groq's API.

---

## 📊 Example Output

```
═══════════════════════════════════════════════════════════════
  MATCH #1  |  Score: 87%  [████████░░]
═══════════════════════════════════════════════════════════════
  📋 Osimertinib + Pemetrexed for EGFR-mutant NSCLC
  🔑 NCT05123456  |  Phase: PHASE3  |  Sponsor: AstraZeneca
  📍 Sites: Boston, MA  |  New York, NY  |  Houston, TX
  🔗 https://clinicaltrials.gov/study/NCT05123456

  📝 Summary:
     Strong candidate. EGFR exon 19 deletion and NSCLC
     adenocarcinoma histology directly match primary criteria.
     Prior platinum-based therapy fulfils treatment history
     requirement. PD-L1 score absent but not disqualifying.

  📊 Criteria breakdown (11 checked):
     ✅  Histologically confirmed NSCLC adenocarcinoma
        └─ Biopsy-confirmed adenocarcinoma matches requirement
     ✅  EGFR exon 19 deletion or exon 21 L858R mutation
        └─ EGFR exon 19 deletion positive confirmed
     ✅  ECOG performance status 0-1
        └─ ECOG 1 meets PS 0-1 requirement
     ✅  No prior EGFR-targeted therapy
        └─ No prior EGFR TKI documented in chart
     ⚠️  Adequate hepatic function (ALT ≤ 3x ULN)
        └─ ALT 32 U/L — within normal, but ULN not specified
     🔬  PD-L1 TPS score required for stratification
        └─ PD-L1 TPS not recorded in chart

  🔬 Missing data — order these to confirm eligibility:
     → PD-L1 IHC (22C3 assay) — required for trial stratification

═══════════════════════════════════════════════════════════════
  MISSING DATA ACTION PLAN
═══════════════════════════════════════════════════════════════
  → PD-L1 IHC (22C3 assay)
     Relevant to: NCT05123456, NCT04987654

  → Repeat eGFR within 30 days
     Relevant to: NCT05234567
```

---

## 📁 Project Structure

```
clinicaltrialagent/
├── pyproject.toml          ← packaging; installs the `ctmatch` command
├── requirements.txt
├── .env.example
├── ctmatch/
│   ├── cli.py              ← `ctmatch` command (init / check / samples / match)
│   ├── pipeline.py         ← run_pipeline() — calls everything in order
│   ├── config.py           ← API key loading, models, call_llm, clean_json
│   ├── patients.py         ← sample patients
│   ├── ehr_extraction.py   ← extract_patient_profile()
│   ├── trial_search.py     ← search_clinicaltrials(), parse_all_trials(), pre_filter()
│   ├── criteria_reasoning.py ← reason_over_all_trials()
│   ├── scoring.py          ← score_trial(), score_and_rank()
│   └── display.py          ← match cards, missing-data plan, JSON export
├── ClinicalTrialMatching.ipynb
└── legacy/                 ← original monolithic notebook
```

---

## 🔭 Future Work

- **EHR integration** — direct FHIR API connection to hospital systems (Epic, Cerner)
- **Geographic expansion** — international trial registries (EU CTR, ISRCTN)
- **Longitudinal tracking** — re-match patient as their chart updates over time
- **Multi-patient batch mode** — screen an entire oncology clinic's roster overnight
- **Federated deployment** — run locally within hospital firewall for PHI compliance
- **Clinician feedback loop** — physician accepts/rejects matches to fine-tune scoring
- **Drug interaction layer** — flag trials whose investigational drugs conflict with current meds

---

## 📄 Research & Publication

This project targets the following venues:

| Venue | Type | Focus |
|-------|------|-------|
| AMIA Annual Symposium | Conference | Clinical informatics |
| CHIL (ACM) | Conference | ML for health |
| npj Digital Medicine | Journal | Digital health systems |
| JAMIA | Journal | Medical informatics |
| NeurIPS ML4H Workshop | Workshop | ML for healthcare |

**Key research contributions:**
1. PASS/FAIL/UNCERTAIN/MISSING_DATA schema for structured eligibility reasoning
2. Missing data as an actionable clinical signal rather than a silent exclusion
3. Multi-strategy search combining keyword, semantic, and biomarker matching
4. End-to-end evaluation framework using MIMIC-IV + MedQA benchmarks

---

## 👤 Author

**Asfiya Tehmeen**
4th Year Computer Science | Healthcare AI Research

- 🔗 LinkedIn: [[Linkedin](https://www.linkedin.com/in/asfiya-tehmeen/)]
- 📧 Email: [asfiyatehmeen@gmail.com]

---

## 🙏 Acknowledgements

- [ClinicalTrials.gov](https://clinicaltrials.gov) — public trial registry API
- [Groq](https://groq.com) — free LLM inference infrastructure
- [Meta AI](https://ai.meta.com) — LLaMA open-source model family
- [PhysioNet / MIMIC-IV](https://physionet.org) — clinical benchmark dataset

---

> ⭐ If this project is useful to you, please star the repo — it helps with research visibility.
