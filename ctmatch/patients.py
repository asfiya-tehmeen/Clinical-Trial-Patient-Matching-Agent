"""
patients.py
===========
Synthetic, de-identified EHR summaries used to drive the pipeline.

Each patient is a plain-text clinical vignette. Set ACTIVE_PATIENT to the
one you want to run, or assign your own clinical note to it.
"""

# --- Patient A: NSCLC (default) ---
PATIENT_A = """
Patient: 61-year-old female
Primary diagnosis: Stage IIIB non-small cell lung cancer (NSCLC),
  adenocarcinoma histology, confirmed by biopsy 4 months ago.
Molecular: EGFR exon 19 deletion positive. ALK negative. PD-L1 TPS 45%.
Performance status: ECOG 1
Comorbidities: Type 2 diabetes (well-controlled, HbA1c 7.1%),
  mild hypertension on lisinopril 10mg daily.
Current medications: Metformin 1000mg BID, Lisinopril 10mg QD,
  Ondansetron PRN.
Prior treatments: Completed 4 cycles carboplatin + pemetrexed (first-line).
  No prior EGFR-targeted therapy. No prior immunotherapy.
Recent labs: eGFR 68 mL/min, ALT 32 U/L, ANC 1.9 x10^9/L,
  Hgb 11.2 g/dL, platelets 210 x10^9/L.
Brain MRI: No intracranial metastases detected.
Location: Boston, MA, USA
"""

# --- Patient B: Breast cancer ---
PATIENT_B = """
45-year-old female. Stage II HER2-positive breast cancer, diagnosed 3 months ago.
ER negative, PR negative, HER2 3+ by IHC. BRCA1/2 negative.
ECOG 0. No prior systemic therapy. No significant comorbidities.
Current meds: None. Labs: normal CBC, LFTs, renal function.
Location: Houston, TX, USA.
"""

# --- Patient C: Colorectal cancer ---
PATIENT_C = """
72-year-old male. Stage IV colorectal adenocarcinoma with liver metastases.
KRAS wild-type. MSI-H / dMMR confirmed. ECOG 2.
Prior therapy: FOLFOX x6 cycles (completed 2 months ago), bevacizumab.
Comorbidities: Atrial fibrillation on warfarin, CKD stage 3 (eGFR 38).
Location: Chicago, IL, USA.
"""

# --- Patient D: Healthy volunteer ---
PATIENT_D = """
28-year-old male, healthy volunteer. No chronic conditions. No medications.
BMI 23. Non-smoker. No known allergies. ECOG 0.
Location: New York, NY, USA.
"""

# All available sample patients, keyed by short label.
SAMPLE_PATIENTS = {
    "A_nsclc":      PATIENT_A,
    "B_breast":     PATIENT_B,
    "C_colorectal": PATIENT_C,
    "D_healthy":    PATIENT_D,
}

# ------------------------------------------------------------------
# Active patient — change this to test a different case, or paste
# your own clinical note here.
# ------------------------------------------------------------------
ACTIVE_PATIENT = PATIENT_A
