# Judge Template: Full Rubric Evaluation — Process (Stage 3b phase P1, AKM only)

> Prompt template for the LLM judge — scoring of process-level criteria (Dimension B + C)
> from the A↔K↔M dialogue logs (step-JSON). Used exclusively for AKM
> in phase P1 of Stage 3b. B1 and R1 have no dialogue → P2 only.

**Version:** v1.0 (2026-05-16)
**Rubric source:** `evaluation/rubric/akm-eval-pro-v1.json` (criteria B + C in process mode)
**Anchor source:** `evaluation/rubric/akm-eval-pro-v1-anchors.json`
**Material:** step-JSON files from `data/runs/acm/{case}/run-{case}-{variant}-step{N}.json`
**Output:** `eval-llm-process-{case_id}-{variant_id}.json`

---

## Dynamic fields to substitute

| Field | Source | Example |
|-------|--------|---------|
| `{case_id}` | case name | `S1` |
| `{variant_id}` | AKM variant | `V3` |
| `{step_jsons_concat}` | concatenation of all step-JSON files per variant | step1 + step2 + step3... |
| `{step_count}` | number of steps | `7` |
| `{anchors_BC_process}` | anchors for criteria B and C in process mode | see below |

**Note:** Dimension C is scored **twice**: once functionally from the product (P2, in the product-rubric template) and once at the process level from the dialogue (P1, in this template). Two separate output files. Triangulation: if C process ≠ C product → a signal that the product hides or misrepresents the dialogue dynamics.

---

## PROMPT TEMPLATE (to send to the API)

```
You are an expert judge evaluating a multi-agent dialogue trace from an AKM (Analyst-Critic-Moderator) system. Score process-level criteria from dimensions B (Analytical Process) and C (Multi-Agent Dynamics) based on the dialogue logs.

# Context
Case ID: {case_id}
AKM variant: {variant_id}
Number of iteration steps: {step_count}

# Materials: full dialogue trace

The following are sequential step-JSON files capturing the Analyst (A), Critic (K), and Moderator (M) interactions across {step_count} iteration steps.

{step_jsons_concat}

For each step, key fields are:
- `last_answer` — Analyst's response at this step
- `last_critics` — list of Critic's notes raised at this step
- `_dbg_analyst` — Analyst's reasoning trace (tool calls, searches)
- `searches_analyst`, `searches_critic` — number of web searches per agent
- `tokens_analyst_*`, `tokens_critic_*`, `tokens_moderator_*` — token usage

# Your task

Score the following criteria 0-10 based ONLY on the process (dialogue dynamics, agent behavior, iteration patterns), NOT on the final product (which is evaluated separately in P2).

## Criteria for P1 (Process) evaluation

### Dimension B — process-level criteria

#### B2. Causal Chain Robustness (process angle)
Did the Analyst's reasoning chain improve across iterations? Did Critic's notes target specific causal gaps?
**Anchors:**
- Level 2: Analyst's reasoning identical across steps; Critic raises only stylistic issues.
- Level 5: Some causal refinement; 1-2 logical gaps addressed.
- Level 8: Each step adds verified causal links; Critic targets specific weak inferences.
- Level 10: Explicit "because of X, therefore Y" chains evolve with traceable improvements.

#### B3. Cognitive Bias Mitigation (process angle)
Did the dialogue surface biases (confirmation, anchoring, recency) and address them iteratively?
**Anchors:**
- Level 2: Both agents reinforce initial framing; no bias detection.
- Level 5: One bias surfaced by Critic, partially addressed.
- Level 8: ≥2 biases surfaced, with concrete debiasing moves (alternative sources, counterexamples).
- Level 10: Explicit meta-cognitive reflection ("we are anchoring on X — let's reconsider").

### Dimension C — process-level criteria (full dimension here, complementary to P2)

#### C1_process. Integrated Counter-Argumentation (dialogue intensity)
Strength and substantive depth of Critic's notes; degree to which Analyst integrated them.
**Anchors:**
- Level 2: Critic returns "decision=done, notes=[]" most steps; weak adversarial pressure.
- Level 5: 3-5 substantive critic notes per step on average; partial integration.
- Level 8: ≥5 substantive notes per critical step; Analyst visibly restructures response.
- Level 10: Critic forces fundamental reframings (e.g., changes core thesis after step 2).

**Auxiliary metric (auto-extracted):** mean(len(last_critics)) across steps.

#### C2_process. Multiperspectival Synthesis (dialogue diversity)
Did the dialogue introduce genuinely diverse perspectives (not just refinements of one view)?
**Anchors:**
- Level 2: Single perspective deepened.
- Level 5: 2 perspectives surfaced via Critic.
- Level 8: 3+ perspectives integrated by step {step_count}.
- Level 10: Dialectical synthesis (thesis-antithesis-synthesis pattern visible).

#### C3_process. Objectivity & Sycophancy Mitigation (Analyst behavior)
Did Analyst sycophantically agree with Critic ("you raise an excellent point") or substantively engage/push back?
**Anchors:**
- Level 2: Analyst capitulates without analysis ("Critic is right, removed").
- Level 5: Mixed — some substantive engagement, some quick agreement.
- Level 8: Each critic note triggers analysis; Analyst pushes back when justified.
- Level 10: Analyst occasionally disagrees with Critic with documented reasoning.

#### C4_process. Insight Density Growth
Did insight density per response grow across iterations, or did Analyst add length without substance?
**Anchors:**
- Level 2: Final answer is mostly verbose padding of step 1.
- Level 5: Some new insights per step, some redundancy.
- Level 8: Each step adds ≥2 new substantive insights.
- Level 10: Final answer dramatically denser than step 1; eliminated padding.

#### C5_process. Process Auditability (trace quality)
Are the step-JSON files self-explanatory? Could a researcher reconstruct decision-making from trace alone?
**Anchors:**
- Level 2: Trace is opaque; need external context to understand.
- Level 5: Major decisions visible, minor ones implicit.
- Level 8: All metadata fields populated; dialogue self-explanatory.
- Level 10: Plus _dbg_* fields show tool calls and reasoning explicitly.

#### C6_process. Dialectical Resolution Quality (how contradictions resolved)
When Critic raised contradictions in Analyst's reasoning, were they explicitly resolved (vs ignored)?
**Anchors:**
- Level 2: Contradictions persist or are silently dropped.
- Level 5: Some resolved, some silently fixed.
- Level 8: Each critic-raised contradiction explicitly addressed in next answer.
- Level 10: Plus meta-resolution ("Critic is correct on X, but here's why we keep Y...").

# Process metrics (auto-extracted, for triangulation)

The following should be extracted programmatically and included in output:

- `iterations_count`: {step_count}
- `mean_critics_per_step`: avg(len(last_critics))
- `total_critics_notes`: sum(len(last_critics))
- `total_searches_critic`: sum(searches_critic)
- `total_searches_analyst`: sum(searches_analyst)
- `convergence_type`: monotonic_improvement | plateau | regression | irregular
- `critic_coverage_pct`: % of critic notes addressed in next answer (heuristic)

# Output format (STRICT JSON)

{
  "case_id": "{case_id}",
  "variant_id": "{variant_id}",
  "evaluation_phase": "P1_process",
  "judge_model": "claude-opus-4-7|gpt-4o|...",
  "judge_temperature": 0.0,
  "scores": {
    "B2_process": {"score": 7, "justification": "..."},
    "B3_process": {...},
    "C1_process": {...},
    "C2_process": {...},
    "C3_process": {...},
    "C4_process": {...},
    "C5_process": {...},
    "C6_process": {...}
  },
  "process_metrics": {
    "iterations_count": 7,
    "mean_critics_per_step": 5.4,
    "total_critics_notes": 38,
    "total_searches_critic": 13,
    "total_searches_analyst": 21,
    "convergence_type": "monotonic_improvement",
    "critic_coverage_pct": 78
  }
}

# Critical output rules

1. Score ONLY process-level criteria (B2, B3, C1-C6 with _process suffix). Do NOT score A, D, E (these are P2-only).
2. Process_metrics auto-extract from step-JSON files BEFORE scoring (use them as evidence in justifications).
3. Output ONLY JSON. No prose before or after.
```

---

## Implementation notes

- **Number of calls:** Stage 3b — 3 AKM reports from the calibration sample × 1 call each. Stage 6 — 27 AKM reports × 1 call each (if the expert also scores the process; optional, decided per Stage 6).
- **Triangulation with P2:** for each AKM report we have 2 scores of the C dimension — from the dialogue (P1) and from the product (P2). Pearson correlation between them → a "faithfulness" metric (how faithfully the product reflects the process).
- **Material:** all step-JSON files per variant concatenated into `{step_jsons_concat}`. For a 7-step AKM-V1 this is ~50-100 KB of text — fits within the Claude Opus 4.x context.
- **Process metrics auto-extraction:** a Python script `analysis/extract_process_metrics.py` (TBD) computes `iterations_count`, `mean_critics_per_step`, etc. before sending to the judge. The judge uses them as evidence.
- **`critic_coverage_pct`:** heuristic — semantic comparison (embeddings) of the critic notes from step N vs the analysis content in step N+1. An approximate value.

## Dependencies

- `data/runs/acm/{case}/run-{case}-{variant}/run-{case}-{variant}-step{N}.json` — input material
- `evaluation/rubric/akm-eval-pro-v1.json` — definitions of criteria B and C
- `evaluation/rubric/akm-eval-pro-v1-anchors.json` — anchors (note: anchors in the spec are for P2; here we use adapted anchors for P1 — written directly into the template)

## Changes relative to v1

- v1: first version. P1 anchors adapted directly in the template (not in `akm-eval-pro-v1-anchors.json`, which concerns P2). After Stage 3b, P1 anchors may optionally be split into a separate file `akm-eval-pro-v1-anchors-process.json`.
