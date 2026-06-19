# Judge templates

LLM-judge prompt templates and per-criterion scoring guides used to evaluate the
reports in `data/runs/`. They operate on the rubric defined in
`evaluation/rubric/akm-eval-pro-v1.json` (criteria and dimensions) and
`evaluation/rubric/akm-eval-pro-v1-anchors.json` (scoring anchors).

## Contents

- `criteria/` — one file per criterion (A1–E5, 30 files) with the level anchors
  (0–10) the judge uses to score that single criterion.
- `grounding-spec.md` — shared grounding specification included verbatim at the top
  of every per-criterion prompt: role, scale, bias mitigations, output schema, and
  soft-veto rules.
- `judge-pairwise-template.md` — blind pairwise comparison template (Stage 3a): two
  reports compared head-to-head across the five dimensions.
- `judge-rubric-process-template.md` — process-level rubric template (Stage 3b, P1):
  scores dimensions B and C from the multi-agent dialogue trace (step-JSON), for ACM
  reports only.
- `etap6_judge_prompt.md` — Stage 6 judge prompt for the full rubric evaluation.

## Architecture in one line

Each report is scored by 30 independent per-criterion prompts, each prefixed by the
shared `grounding-spec.md`. This decomposed-with-grounding design mitigates halo and
verbosity biases documented in LLM-as-Judge research, while keeping a single source of
truth for the evaluation rules. A fuller methodology write-up (with the architecture
comparison and the APA 7 bibliography) ships in a later version of this package
alongside the evaluation outputs.

## Naming note

ACM (Analyst–Critic–Moderator) is the system under study. Record identifiers kept
verbatim for traceability still use the original token `AKM` (e.g.,
`response_type: "AKM"`, report IDs like `S1-V3`). `AKM` and `ACM` denote the same
system; see the top-level `README.md` for the full equivalence note.
