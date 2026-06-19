# Judge Template: Pairwise per Dimension (Stage 3a)

> Prompt template for the LLM judge — blind pairwise comparison across 5 dimensions.
> Filled in per report pair (variant_A vs variant_B) per case (S1/S2/S3).
> Used in Stage 3a of the evaluation procedure.

**Version:** v1.0 (2026-05-16)
**Dimension source:** `evaluation/rubric/akm-eval-pro-v1.json` (fields `dimensions[].id/name_en/rationale`)
**Judge output:** `judge-pairwise-{case_id}-{variant_A}-vs-{variant_B}.json`

---

## Dynamic fields to substitute

| Field | Source | Example |
|-------|--------|---------|
| `{case_id}` | case name | `S1` |
| `{case_question}` | prompt from `prompts/cases/case-N-en.md` | "Create an analysis of introducing a universal turnover tax..." |
| `{variant_A_id}` | report A identifier | `V3` (= AKM S1-V3) |
| `{variant_B_id}` | report B identifier | `R1-C` |
| `{report_A_md}` | report A content (full final MD) | `# Universal Turnover Tax...` |
| `{report_B_md}` | report B content | `# Universal Turnover Tax...` |
| `{dimension_definitions}` | 5 dimensions from the rubric JSON | see the "Dimensions" section below |

**Anonymization:** the judge does NOT receive information about which report is AKM/B1/R1. Labels A and B are assigned at random per call (random seed stored in the output JSON for reproducibility).

---

## PROMPT TEMPLATE (to send to the API)

```
You are an expert judge evaluating two analytical reports on a financial/economic policy question. This is a BLIND PAIRWISE COMPARISON across five evaluation dimensions.

# Context
Case ID: {case_id}
Original question:
{case_question}

# Reports to compare

## Report A ({variant_A_id})
{report_A_md}

---

## Report B ({variant_B_id})
{report_B_md}

---

# Your task

For EACH of the 5 dimensions below, answer:
- Which report better addresses this dimension? Answer: A / B / tie
- Brief justification (max 2 sentences, anchored in observable text features)

## Dimensions

### Dimension A — Epistemic Rigor
{dimension_A_rationale}
Criteria included: A1 Data Grounding, A2 Source Auditability, A3 Uncertainty Calibration, A4 Temporal Awareness, A5 Common Sense Robustness.

### Dimension B — Analytical Process Quality
{dimension_B_rationale}
Criteria included: B1 Multi-dim Decomposition, B2 Causal Chain, B3 Cognitive Bias Mitigation, B4 Second-Order Thinking, B5 Scenario Modeling, B6 Solution Novelty.

### Dimension C — Multi-Agent Dynamics (functional)
{dimension_C_rationale}
Criteria included: C1 Counter-Argumentation, C2 Multiperspectival Synthesis, C3 Sycophancy Mitigation, C4 Insight Density, C5 Process Auditability, C6 Dialectical Resolution.

### Dimension D — Financial Domain Specificity
{dimension_D_rationale}
Criteria included: D1 Actionability, D2 Regulatory Compliance, D3 Risk/Asymmetry, D4 Numerical Consistency, D5 Methodical Suitability, D6 Market Regime, D7 Info Density, D8 Coherence.

### Dimension E — Technical Parameters
{dimension_E_rationale}
Criteria included: E1 Format Compliance, E2 Negative Constraints, E3 Tone, E4 Length Discipline, E5 Reproducibility Signals.

# Output format (STRICT JSON, single line per dimension)

Return exactly this JSON object:

{
  "case_id": "{case_id}",
  "variant_A": "{variant_A_id}",
  "variant_B": "{variant_B_id}",
  "judgments": {
    "A": {"winner": "A|B|tie", "justification": "..."},
    "B": {"winner": "A|B|tie", "justification": "..."},
    "C": {"winner": "A|B|tie", "justification": "..."},
    "D": {"winner": "A|B|tie", "justification": "..."},
    "E": {"winner": "A|B|tie", "justification": "..."}
  },
  "judge_model": "claude-opus-4-7|gpt-4o|...",
  "judge_temperature": 0.0
}

# Critical rules

1. You do NOT know which report is AKM, B1, or R1. Treat A and B as anonymous.
2. Use "tie" only when reports are genuinely indistinguishable in this dimension. Do not default to "tie" — force a judgment when difference exists.
3. Justifications must reference observable text features (e.g., "Report A cites X sources with APA 7, Report B uses inline citations only"). Do not say "Report A is better-written" without specifics.
4. WARNING: You tend to prefer longer responses (verbosity bias). If Report B is materially longer than A, do not let length alone determine the winner. Penalize length without substance.
5. Output ONLY the JSON object above. No prose before or after.
```

---

## Implementation notes

- **Number of calls:** for the S1 pilot, selected pairs AKM↔R1-C (9), B1↔R1-C (3), AKM↔B1 (selected) were planned. In total ~15-20 calls × 5 dimensions = 75-100 judgments.
- **A/B randomization:** for each pair, randomize the assignment A=AKM or A=R1 (record the seed). Without randomization the LLM tends to favor position A (position bias).
- **Output validation:** the parser checks for the presence of all 5 dimensions + a value ∈ {A, B, tie} + a non-empty justification. Failures are retried at T=0.
- **Aggregation:** win/tie/lose matrix per dimension (sums across all pairs) → `judge-pairwise-{case_id}-winmatrix.csv`.
- **Calibration:** Spearman correlation with 3 expert samples (Stage 6) → `judge-pairwise-calibration.json`.

## Dependencies

- `evaluation/rubric/akm-eval-pro-v1.json` — definitions of the 5 dimensions (field `dimensions[].rationale`)
- `prompts/cases/case-{N}-en.md` — original case question
- `data/runs/{type}/{case}/run-*.md` — content of reports A and B

## Changes relative to v1

- v1: first version. After Stage 3a it may require a v2 iteration (e.g., adjusting the verbosity warning if results show that longer reports win systematically).
