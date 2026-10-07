---
name: case-report
description: 'De-identified, literature-backed, adversarially-verified medical case reports — a word-limited conference abstract (e.g. a poster) or a full journal manuscript (IMRAD). Use whenever the user is preparing a case report, case series, or clinical vignette for journal/conference submission: drafting from raw records, de-identifying patient data, DOI-verifying literature, writing the abstract/manuscript, or checking a draft against a venue''s requirements. Trigger even on just "write up this case", "turn these records into an abstract", "submit this to [journal]", a named venue (Global Spine Journal, 骨科醫學會, BMJ Case Reports, Cureus), or handing over clinical notes to prepare for publication. For single-patient case reports and small case series — NOT original-research manuscripts (cohort studies, trials), systematic reviews, patient-education/outreach, discharge summaries, or referral letters, even when they share a hospital, de-id, or the same journal. Orthopedics is default; adapts to any specialty/journal.'
---

# Case Report Writer

Turn raw clinical material into a submission-ready case report whose every
sentence is either traceable to the patient's record or backed by a verified
citation — with patient-identifying information stripped before anything leaves
the local machine.

Two output modes share one pipeline:

- **`--abstract`** — a conference/poster abstract under a word limit (Intro /
  Case / Discussion), plus a title and any venue-required classification.
- **`--manuscript`** — a full journal manuscript (IMRAD: Introduction, Case
  Presentation, Discussion, Conclusion, References), with figure/table slots and
  an optional cover letter.

If the user doesn't say which, infer from context (a word count or "poster/會議"
→ abstract; "投稿期刊 / manuscript / full paper" → manuscript) and confirm in one
line before drafting.

## Why this skill exists (the four commitments)

A case report is a factual claim about a real person, submitted under the
authors' names. Three failure modes destroy it — invented clinical detail,
leaked patient identity, and hallucinated citations — and they are exactly the
mistakes a language model makes most naturally. The pipeline below is built to
make each one hard to commit. Hold these four commitments above stylistic
polish; when they conflict with speed or elegance, they win.

1. **Zero fabrication.** Every clinical statement maps to a specific line in the
   source record. If a fact would strengthen the report but isn't in the
   records, you do **not** invent it — you add it to a *clinician-input
   checklist* and leave a visible gap. The physician can supply it; you cannot.

2. **PHI never leaves the machine.** De-identification is the first stage, not a
   cleanup afterthought. Raw records, names, dates, MRNs, and any direct
   identifiers stay local — never in the drafted output, never committed to git,
   never sent to an external service. See `references/deidentification.md`.

3. **Every citation is real and verified.** Support claims with PubMed-indexed
   literature and verify each DOI against real metadata. A plausible-looking
   reference that doesn't resolve is worse than no reference. See Stage 4.

4. **The venue drives the shape.** Word limits, section structure, reference
   style, and classification come from the *target journal or conference* — not
   from a fixed template, and not from memory. Read the venue's record in this
   plugin's corpus (Stage 2) before drafting.

## The pipeline

Run these in order. Stages 1–2 are setup, 3–4 produce the draft, 5–6 harden it.
For a quick first draft the user just wants to see, you may run 3 lightly and
defer 4–5 — but say so, because an unverified draft is not submission-ready.

### Stage 1 — Intake & de-identification

Read whatever the user provides (PDF records, pasted notes, a Telegram dump,
prior drafts). Before writing anything, produce a **de-identified clinical fact
sheet**: the medically relevant facts (age band, sex, mechanism, findings,
imaging, procedure, course, follow-up) with all direct identifiers removed.

Watch for the traps that make "5 files" not equal "5 patients" — duplicate
exports, re-scans, and byte-identical copies. Reconcile how many distinct
patients you actually have and, if ambiguous, ask.

The fact sheet is the single source of truth for every later clinical claim.
Details in `references/deidentification.md` (identifier list, local-only
boundary, how to keep PHI out of git).

### Stage 2 — Venue selection & requirements

Establish the target journal or conference, then read its requirements from
this plugin's venue corpus — the same primary-source records the `submit-to`
skill reads (`${CLAUDE_PLUGIN_ROOT}/venues/**/*.yaml`, each with source URL,
fetch and verification dates, and a content hash). Follow `submit-to`'s rules
for reading a record: quote the provenance date, repeat every `warnings[]`
entry to the user, and treat `status: not_found / not_published` as "the public
source does not say" — never fill it from memory.

- **Venue already in the corpus** — read it. Two records exist for this skill's
  usual targets: `sage/global-spine-journal` and `toa/spring-meeting`
  (中華民國骨科醫學會春季聯合學術研討會).
- **Venue not in the corpus** — run the `add-venue` skill to build the record
  from the venue's own pages. Do not write ad-hoc venue notes inside this skill.
- **Actually preparing to submit** — follow `submit-to`'s strict path and run
  `scripts/verify.py <venue-id>` so a stale record is caught before you draft to it.

From the record take: whether the venue accepts case reports at all (check this
first — `sage/global-spine-journal` records that GSJ no longer does), article
type, word/character limits, required headings, reference style, title and
classification rules, and consent/ethics statements. Nail these down *now*;
retrofitting a word limit onto a longer draft wastes effort. If a limit is
`not_found` in the record (e.g. the TOA spring meeting publishes its abstract
limits only inside the logged-in submission form), ask the user for the number
from the form instead of assuming one.

The reference docs below call this record "the venue file".

### Stage 3 — Structured drafting

Draft against the venue's structure and the CARE reporting backbone (the
international standard for case-report content — see
`references/care-guideline.md`, so the report is complete regardless of venue).

- **Abstract mode:** Introduction (why this case matters, 2–4 sentences) → Case
  Presentation (the de-identified course: presentation, findings, intervention,
  outcome) → Discussion & Conclusions (what the literature says + the take-home).
  Add a title (bilingual if the venue or user wants it) and any required
  classification. Stay under the word limit — check the count explicitly.

- **Manuscript mode:** full IMRAD with figure/table placeholders keyed to what
  the records actually contain, plus a cover letter if submitting. Match the
  venue's section hierarchy (some journals forbid ultra-short subsections).

Write in the register real journals use: past tense, largely passive voice in
Methods/Case, **no hedging in factual statements** ("demonstrated", not "may
suggest"), precise numbers. Each drafted clinical sentence should trace back to
a fact-sheet line — if you can't point to the source, it doesn't belong.

### Stage 4 — Literature grounding

For each interpretive or comparative claim (epidemiology, why this management,
what outcome is expected), find supporting literature via PubMed (the PubMed MCP
tools, or WebSearch as fallback) and **verify every DOI resolves to the cited
article**. Prefer primary studies and recent reviews over textbook assertion.

Produce a companion `background_review.md` — a literature-only file (no PHI)
that both grounds the Discussion and doubles as Q&A prep for a poster session.
Keep it structured by claim so a reviewer question maps straight to a citation.

### Stage 5 — Adversarial verification

Before calling it done, attack the draft from independent angles rather than
re-reading it once. Spawn parallel verification subagents (Agent tool), each
carrying **one lens**, then reconcile their findings:

- clinical fidelity (every claim vs. the fact sheet — any fabrication?)
- venue/format compliance (word limit, structure, reference style)
- citation accuracy (does each DOI resolve to what's claimed?)
- PHI leak scan (any identifier survived into the output?)
- devil's-advocate reviewer (what would a hostile reviewer reject?)

Scale the effort to the stakes: a couple of lenses for a rough draft, the full
ensemble for a submission-ready one. Fix what you can verify; escalate what you
can't. Lens prompts and the scaling guidance live in
`references/verification-lenses.md`.

### Stage 6 — Clinician confirmation gate & output

Some things only the treating clinician can decide or supply: facts not in the
records, whether to disclose a complication, exact anatomic diagnoses,
publication consent. Collect these into a short **clinician-input checklist** and
surface it prominently — never paper over a gap by guessing.

Then produce the output the user asked for. Markdown is the working format;
export to `.docx` (che-word-mcp for programmatic builds, or `pandoc` for
rich markdown with inline links/citations — see the two tools' trade-offs) or
LaTeX for manuscript submission. Keep word counts and the checklist visible in
your report back to the user.

## Reference map

Read these as each stage needs them (progressive disclosure — don't front-load):

| File | When |
|------|------|
| `references/deidentification.md` | Stage 1 — identifier list, local-only boundary |
| `${CLAUDE_PLUGIN_ROOT}/venues/**/*.yaml` (via `submit-to`) | Stage 2 — the target venue's requirements, with provenance |
| `add-venue` skill | Stage 2 — when the target venue is not in the corpus yet |
| `references/care-guideline.md` | Stage 3 — CARE content backbone (venue-agnostic) |
| `references/verification-lenses.md` | Stage 5 — lens prompts + how to scale |

## What "done" looks like

A report where: the word count fits the venue, the structure matches it, every
clinical sentence traces to the fact sheet, every citation resolves, no
identifier leaked, and a clinician-input checklist names exactly what the
physician still has to confirm. Report these back explicitly — they are how the
user (and the physician) trusts the draft.
