# De-identification & the local-only boundary

De-identification is Stage 1 because a case report is a factual claim about a
real person. Once an identifier reaches a draft, a git commit, or an external
service, you cannot fully recall it — so strip identity *before* writing, not
after.

## Two things happen in Stage 1

1. **Strip identifiers** from the source material.
2. **Distill** the medically relevant facts into a de-identified *fact sheet*
   that becomes the single source of truth for every later clinical claim.

## Direct identifiers to remove

Based on the HIPAA Safe Harbor 18 identifiers, adapted for Taiwan clinical
records:

- Names (patient, family, treating staff when personally identifying)
- Dates tied to the individual: birth date, admission/discharge/procedure dates,
  death date. Keep **relative** timing instead ("two months prior", "post-op
  day 1") and **age bands** rather than exact age when the venue is fine with it
  (a 92-year-old is better written "a nonagenarian" in prose).
- Medical record number (病歷號), 身分證字號, national health ID, accession /
  study numbers
- Geographic detail finer than region; the specific hospital when it could
  identify the patient (the *authors'* institution on the title page is fine —
  that's an author affiliation, not patient PHI)
- Phone, email, address, IP, device IDs, biometric identifiers
- Photographs/imaging with identifying features (faces, tattoos, unique
  hardware) unless separately consented — and even then, not in the working
  draft

## What to keep (the fact sheet)

The clinically load-bearing facts, de-identified:

- Age band, sex
- Relevant history / comorbidities (stated at the level the case needs — e.g.
  "well-controlled HIV on antiretroviral therapy", not a full social history)
- Mechanism / presentation
- Examination and imaging findings
- Diagnosis
- Intervention (procedure, implants, technique)
- Post-operative course and follow-up (with relative timing)

Write each fact so you can point back to the source line. If a fact isn't in the
records, it does **not** go on the fact sheet — it goes on the clinician-input
checklist (Stage 6).

## Reconcile how many patients you actually have

Raw exports lie about their own count. Duplicate PDFs, re-scans, and
byte-identical copies routinely make "5 files" turn out to be 2 patients. Before
drafting, confirm the number of distinct patients; if the grouping is ambiguous,
ask rather than guess. (This trap has occurred in real use of this skill.)

## The local-only boundary

- Raw records, PHI, and any audio/original exports stay on the local machine and
  in Dropbox backup — **never** committed to a git remote, per the project's
  privacy rule. `*.srt`, audio, and raw-notes patterns are git-ignored for this
  reason.
- The **drafted output** (fact sheet, abstract, manuscript, background review)
  is a de-identified derivative — it may be shared and version-controlled *only
  if* the PHI scan (Stage 5) confirms it carries no identifiers.
- Never paste raw records into an external web service. PubMed lookups use the
  medical concepts, not the patient's data.

## Quick self-check before leaving Stage 1

- Could a reader of the fact sheet identify the individual? If yes, keep
  stripping.
- Is every fact sheet line backed by a source line?
- Do I actually know how many distinct patients this is?
