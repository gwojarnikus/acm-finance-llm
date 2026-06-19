# Stage 6 Single-Judge Scoring Prompt — Agent Instructions

You are acting as **claude-opus-4-7 judge** evaluating finance/policy reports for the us-akm research project (multi-agent LLM systems in finance — monograph).

## Your task

For each report assigned to you below, perform a **full AKM Eval Pro rubric scoring** (30 criteria, 5 dimensions) and save a per-report aggregate JSON.

## Mandatory context to load (load each file ONCE at start)

1. **Rubric** (30 criteria + Soft Veto): `evaluation/rubric/akm-eval-pro-v1.json`
2. **BARS anchors**: `evaluation/rubric/akm-eval-pro-v1-anchors.json`
3. **Grounding spec**: `evaluation/judge-templates/grounding-spec.md`
4. **Per-case briefings** (load all 6, one-time):
   - `evaluation/rubric/per-case-briefings/briefing-S1-D2.md`
   - `evaluation/rubric/per-case-briefings/briefing-S1-D5.md`
   - `evaluation/rubric/per-case-briefings/briefing-S2-D2.md`
   - `evaluation/rubric/per-case-briefings/briefing-S2-D5.md`
   - `evaluation/rubric/per-case-briefings/briefing-S3-D2.md`
   - `evaluation/rubric/per-case-briefings/briefing-S3-D5.md`

## Per-report procedure

For each report in your assigned list:

1. Read the report MD file from `data/runs/`:
   - **AKM**: `data/runs/acm/{S1|S2|S3}/run-{report_id}.md`
   - **B1**: `data/runs/baseline/B1/run-{report_id}.md`
   - **R1**: `data/runs/reference/R1/run-{report_id}.md`

2. Score all 30 criteria (A1..A5, B1..B6, C1..C6, D1..D8, E1..E5) on 0-10 scale, 0.5 increments. For each criterion:
   - Compare report text to BARS anchors (levels 2/5/8/10)
   - Apply asymmetry rules per response_type (AKM/B1/R1)
   - For D2: use the relevant per-case briefing
   - For D5: use the relevant per-case briefing
   - For D4: verify arithmetic at text level (no Python tool); cap honest score at 9 without tool
   - For A2: cap at 6 without WebFetch (Level 1 formal only); set `fabrication_detected` boolean
   - For E4: apply verbosity self-warning (you tend to prefer longer responses — penalize length without substance)

3. Compute aggregates:
   - `dim_A = mean(A1..A5)`
   - `dim_B = (B1+B2+B3+B4+B5 + 0.5*B6) / 6` (B6 halved per README §7.1)
   - `dim_C = mean(C1..C6)`
   - `dim_D = mean(D1..D8)`
   - `dim_E = mean(E1..E5)`
   - `weighted_sum = 0.25*dim_A + 0.20*dim_B + 0.20*dim_C + 0.25*dim_D + 0.10*dim_E`
   - Soft Veto λ: 0.5 if (A1<3.0) OR (A2<2.0 AND fabrication_detected) OR (D4<2.0); else 1.0
   - `S_final = λ × weighted_sum`

4. Write aggregate to `data/evaluation/full/eval-{report_id}-aggregate.json` using the schema shown below. **Read the file first** if it exists (it may from prior pilot) — you are OVERWRITING for full uniformity.

## Output JSON schema (per report)

```json
{
  "report_id": "<report_id>",
  "case_id": "<S1|S2|S3>",
  "variant_id": "<V1..V9 | B1-D-v1 etc | R1-C | R1-G>",
  "response_type": "<AKM|B1|R1>",
  "judge_model": "claude-opus-4-7",
  "judge_temperature": 0.0,
  "evaluation_mode": "single_judge_full_etap6_uniform",
  "evaluation_session": "etap6-full-60-reports-20260516",
  "rubric": "akm-eval-pro-v1.json",
  "anchors": "akm-eval-pro-v1-anchors.json v1-pilot",
  "grounding_spec": "grounding-spec.md v1.0",
  "briefings_loaded": ["briefing-S<case>-D2.md v1.0", "briefing-S<case>-D5.md v1.0"],
  "per_criterion_scores": {
    "A1": {"score": <0-10>, "j": "<≤25 words rationale citing report features>", "anchor_ref": <matched BARS level>},
    "A2": {"score": ..., "j": "...", "anchor_ref": ..., "fabrication_detected": <bool>},
    ...
    "E5": {"score": ..., "j": "...", "anchor_ref": ...}
  },
  "dimension_means_with_B6_subweight": {"A": ..., "B": ..., "C": ..., "D": ..., "E": ...},
  "dimension_weights": {"A": 0.25, "B": 0.20, "C": 0.20, "D": 0.25, "E": 0.10},
  "weighted_sum": <float>,
  "soft_veto": {
    "lambda": <0.5 or 1.0>,
    "triggers": [<list of triggered rule ids>],
    "fabrication_detected_A2": <bool>,
    "A1_above_threshold_3.0": <bool>,
    "A2_above_threshold_2.0_or_no_fabrication": <bool>,
    "D4_above_threshold_2.0": <bool>
  },
  "S_final": <float>,
  "judge_observations": {
    "weakest_dimension": "<A|B|C|D|E (value)>",
    "strongest_dimension": "<A|B|C|D|E (value)>",
    "notable_strengths": ["..."],
    "notable_gaps": ["..."],
    "AKM_only_critic_effect_visible": "<Yes/No/Partial — only for AKM>",
    "AKM_only_moderator_effect_visible": "<Yes/No/Partial — only for AKM>"
  },
  "limitations": [
    "Single-judge (claude-opus-4-7) — no cross-model ICC.",
    "D4 verified at text level only.",
    "A2 capped Level 1 (max 6 without WebFetch).",
    "Compact justifications (≤25 words per criterion)."
  ]
}
```

## Reference: 3 already-scored AKM S1 (use as benchmark consistency check)

- S1-V1: S_final = 6.755 (dim_A 6.80, B 6.00, C 7.17, D 6.56, E 7.80)
- S1-V2: S_final = 6.879 (multiple Critic markers → low D8/E2)
- S1-V3: S_final = 7.045 (full References APA 7, design solutions)

Already-existing files: `data/evaluation/full/eval-S1-V1-aggregate.json`, V2, V3. Do NOT re-score these unless explicitly listed in your assignment.

## Important consistency rules

- **Be strict on D8/E2 for AKM** if you see "The Critic correctly...", "Critic noted...", "as the Critic suggested" → these are MAS-seam violations (E2) and break single-author voice (D8). Mark explicitly in justification.
- **Be strict on E1** if **Sources:** APA 7 section is missing for AKM (mandatory per AKM schema); R1 schema instead requires Research Process Metadata.
- For B1 (single-shot baseline): E1 expects "no header, free sections, citations in body"; E2 checklist relaxed (only language match + author+year citations).
- For R1: ignore self-reported confidence_reported_pct, key_data_limitations in scoring per asymmetry rule.

## Final action

After scoring all assigned reports, return ONLY a short summary (≤300 words):
- List of reports scored with S_final
- Any reports you flagged for human review (Soft Veto triggered, ICC concerns, ambiguous scoring)
- Any prompt/anchor issues observed
- Total reports completed

Do not return full per-criterion details — they are in the saved JSONs.
