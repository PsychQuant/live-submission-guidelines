# Adversarial verification — lenses & scaling

Re-reading your own draft once catches little; it shares the blind spots that
produced the draft. Instead, attack it from independent angles, each blind to
the others, and reconcile. In Claude Code, spawn each lens as its own subagent
(Agent tool) so the perspectives are genuinely separate — a lens that also wrote
the draft is not an independent check.

## The lenses

Each lens gets the draft + the fact sheet + the venue file, and one job.

### 1. Clinical fidelity (the most important)
> Compare every clinical statement in the draft against the de-identified fact
> sheet. Flag anything that is not directly supported: invented findings,
> upgraded certainty ("suspected" → "confirmed"), timeline claims the records
> don't establish, mechanisms not documented. Default to flagging when unsure.
> Output: a list of unsupported statements, each with what the fact sheet
> actually says.

### 2. Venue / format compliance
> Check the draft against the venue file: word/character count (state the actual
> number), required section headings present and correctly named, reference
> style correct, title/classification rules met, any banned constructs absent.
> Output: each requirement with pass/fail and the fix.

### 3. Citation accuracy
> For every citation, verify the DOI resolves to an article whose content
> actually supports the claim it's attached to. Flag DOIs that don't resolve,
> resolve to a different article, or are cited for a claim the article doesn't
> make. Output: per-citation verdict.

### 4. PHI leak scan
> Scan the draft (and the background review, and any output file) for surviving
> identifiers: names, exact dates, MRN/ID numbers, identifying institution or
> geography, anything from the direct-identifier list. This is often best done
> as a regex/script pass in addition to reading. Output: any identifier found,
> with location — zero is the only acceptable result.

### 5. Devil's-advocate reviewer
> Play a hostile peer reviewer. What is the weakest claim? What would you reject
> or demand revised? Is the "novelty" actually novel? Are outcomes overstated
> relative to follow-up? Is the discussion balanced or cherry-picked? Output:
> the objections a real reviewer would raise, ranked by severity.

## Scaling to the stakes

The pipeline should cost what the moment is worth.

| Situation | Lenses to run |
|-----------|---------------|
| Rough first draft the user just wants to see | 1 (clinical fidelity) + 4 (PHI) |
| Internal review before sending to the clinician | 1, 2, 4 |
| Submission-ready | all five, in parallel |
| High-sensitivity case (e.g. HIV, minors) | all five; PHI lens twice, once as a script pass |

## Reconciling findings

- **Fix** what you can verify against the fact sheet, the venue file, or PubMed.
- **Escalate** what only the clinician can resolve → clinician-input checklist
  (Stage 6). Never resolve a clinical-fact question by guessing.
- A finding that two lenses raise independently is high-signal; prioritize it.
- Re-run the affected lens after a fix, not the whole ensemble.

In real use, a six-model ensemble on a two-abstract batch surfaced 13 findings
(a timeline self-contradiction, a hallucinated clinical detail, an uncited
"selling point", an internal inconsistency between sections) — all fixed or
escalated to the clinician before the report was considered done. That is the bar.
