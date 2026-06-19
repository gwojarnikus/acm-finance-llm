# ACM Finance LLM — Replication Package

This repository is the public replication package for the monograph **_Generative
Artificial Intelligence in Finance: A Dialogue Architecture for Large Language
Models_** (Wojarnik, 2026). It accompanies the empirical study of the
**Analyst–Critic–Moderator (ACM)** dialogue architecture and is released so that the
prompts, evaluation instrument, raw run traces, and analysis code can be inspected and
reproduced independently of the book.

The work is situated in the **Design Science Research (DSR)** paradigm: its scientific
contribution is *design knowledge* — the agent roles, the dialogue protocol, and the
evaluation rubric. Publishing those artifacts is therefore a natural extension of the
monograph itself.

> **ACM ≡ AKM.** The system is named **ACM (Analyst–Critic–Moderator)** in English and
> **AKM (Analityk–Krytyk–Moderator)** in the original Polish work. Folder and label names
> in this package use `acm`. Internal record identifiers kept verbatim for traceability
> still use the original token `AKM` (e.g., `response_type: "AKM"`, report IDs such as
> `S1-V3`). The two are the same system.

---

## What ACM is

ACM is a structured, iterative dialogue between three specialized LLM agents:

- **Analyst (A)** — generates and refines the analytical answer.
- **Critic (K)** — adversarially challenges assumptions, evidence, and reasoning.
- **Moderator (M)** — manages the iteration loop and decides on convergence.

The protocol was implemented as a prototype in n8n (the `ACM Orchestrator` and
`ACM Iteration` workflows) and evaluated empirically on three financial-policy scenarios.
The central research hypothesis is the **dialogue premium (ΔMAS)** — a measurable quality
advantage of the multi-agent system over a single model.

---

## Package contents

```
acm-finance-llm/
├── README.md                      ← this file
├── LICENSE                        ← CC BY 4.0
├── CITATION.cff                   ← machine-readable citation metadata
├── prompts/
│   ├── agents/                    ← Analyst / Critic / Moderator prompts
│   ├── cases/                     ← the three financial scenarios (S1–S3)
│   └── reference/                 ← reference-model (R1) prompt template
├── evaluation/
│   ├── rubric/                    ← AKM-Eval Pro v1: rubric JSON + scoring anchors
│   └── judge-templates/           ← LLM-judge prompts: 30 per-criterion guides (A1–E5),
│                                     grounding spec, pairwise & process templates
├── data/
│   ├── runs/
│   │   ├── acm/                   ← ACM dialogue runs (V1–V9 × S1–S3): final .md + step-JSON
│   │   ├── baseline/              ← single-LLM baseline runs (B1)
│   │   └── reference/             ← commercial deep-research runs (R1)
│   └── tables/                    ← summary result tables (rankings, group/dimension means)
└── analysis/                      ← Python: H1/H2 statistical tests, table/CSV generators
```

---

## Experimental design

**Three cases (S1–S3)** — financial / economic-policy questions. For example, S1 asks for an
analysis of replacing Poland's PIT and CIT with a single universal turnover tax at a
budget-neutral rate.

**ACM variants (V1–V9)** — the same three-role protocol run over different assignments of
three open-weight / independent models (chosen for data-privacy reasons relevant to financial
institutions): **DeepSeek-V3.2**, **Kimi K2.5 (Moonshot)**, and **MiniMax**. V1 is the
reference assignment (A=DeepSeek, K=Kimi, M=MiniMax); V7–V9 are homogeneous (all three roles on
one model). → 9 variants × 3 cases = **27 ACM runs**.

**Baseline (B1)** — a single-step answer *with* web search from each ACM model
(`B1-D` DeepSeek, `B1-Ki` Kimi, `B1-Mi` MiniMax), repeated across runs. → **27 baseline runs**.

**Reference (R1)** — commercial deep-research systems as a strong external reference:
`R1-C` (OpenAI / ChatGPT Deep Research) and `R1-G` (Google / Gemini Deep Research).
→ 2 × 3 = **6 reference runs**.

Each ACM run stores the full dialogue: a final report (`run-<case>-<variant>.md`) plus the
per-iteration trace (`...-step1.json … -stepN.json`). Baseline and reference runs are
single-step and store the report plus metadata.

---

## Evaluation: AKM-Eval Pro

Reports are scored with a purpose-built rubric, **AKM-Eval Pro v1** — **30 criteria across
5 dimensions**:

- **A — Epistemic Rigor** (grounding, source auditability, uncertainty, …)
- **B — Analytical Process Quality** (decomposition, causal chains, bias mitigation, …)
- **C — Multi-Agent Dynamics** (counter-argumentation, synthesis, sycophancy mitigation, …)
- **D — Financial Domain Specificity** (actionability, regulatory compliance, numerical
  consistency, …)
- **E — Technical Parameters** (format, constraints, tone, length, reproducibility signals)

Criteria use **behaviorally anchored rating scales (BARS)** and a **soft-veto** multiplier for
critical failures. Scoring is performed by an LLM judge using the templates in
`evaluation/judge-templates/`: a shared `grounding-spec.md` plus one prompt per criterion (a
decomposed-with-grounding design that mitigates halo and verbosity biases). The rubric
definition lives in `evaluation/rubric/akm-eval-pro-v1.json` with anchors in
`akm-eval-pro-v1-anchors.json`.

---

## Reproducing the study

1. **Prompts** — load the Analyst/Critic/Moderator prompts (`prompts/agents/`) and a case
   (`prompts/cases/`).
2. **Run ACM** — drive the three-agent loop (the prototype used n8n) over the chosen model
   assignment (V1–V9). Baselines (B1) and references (R1) use their own single-step prompts.
3. **Evaluate** — apply the rubric (`evaluation/rubric/`) via the judge templates
   (`evaluation/judge-templates/`), one criterion per call.
4. **Analyze** — the scripts in `analysis/` compute the H1/H2 statistical tests and generate
   the result tables.

The raw run traces in `data/runs/` let you re-evaluate or re-analyze without re-running the
models.

---

## Language policy

This package separates an **authored layer** from a **primary-data layer**:

- **Authored layer — English.** All prompts, judge templates, scripts (comments/docstrings),
  and documentation are in English.
- **Primary data (`data/runs/`) — verbatim.** The runs are the unaltered research record.
  Because the cases concern Polish fiscal policy, the systems cited Polish-language government
  sources and some dialogue traces contain Polish text. **These are intentionally not
  translated**, to preserve the integrity of the empirical record. Bibliographic citations of
  Polish-language sources are likewise kept in the original (APA 7 keeps original titles; an
  English gloss is added where a title appears as an illustrative example in the rubric).
- **Rubric JSON (`evaluation/rubric/`) — bilingual.** Criterion names carry both `name_en`
  and `name_pl`, and some anchor text is still Polish. The instrument is fully usable in
  English via `name_en`; a fully English-curated rubric is planned (see roadmap).

---

## Scope of this version, and roadmap

**Included now (v1):** agent prompts, cases, reference prompt; the rubric JSON + anchors; the
full judge-template set (30 per-criterion guides, grounding spec, pairwise and process
templates); all raw runs (ACM / baseline / reference); summary result tables; and the analysis
scripts.

**Planned for a later version:**

- `data/evaluation/` — the per-report, per-criterion scores, aggregates, and judge
  justifications, plus the full statistical-test reports.
- The rubric **methodology specifications** (`akm-eval-pro-v1-spec.md`, `-readme.md`,
  `-anchors-spec.md`) and a full English curation of the rubric JSON (removing `name_pl`,
  translating anchors).
- An extended judge-templates methodology write-up (architecture rationale + bibliography).
- The **n8n workflow exports** (`ACM Orchestrator`, `ACM Iteration`) for full implementation
  reproducibility.

The analysis scripts reference the complete evaluation pipeline; they become runnable end-to-end
once the evaluation layer above is published.

---

## Naming and identifiers

- **`AKM`** appears throughout the data as an internal identifier (e.g., `response_type`,
  report IDs). It denotes the same system as **ACM** — kept verbatim for traceability with the
  monograph.
- A few internal identifiers and file names retain the token **`etap`** (Polish for "stage",
  e.g., `etap6_judge_prompt.md`, `session_id: "etap-6-pilot"`). These are stable record
  identifiers, not prose, and are kept unchanged for traceability. Human-readable text uses
  "Stage".

---

## How to cite

Please cite both the monograph and this package. Machine-readable metadata is in
`CITATION.cff`. Suggested form:

> Wojarnik, G. (2026). *Generative Artificial Intelligence in Finance: A Dialogue Architecture
> for Large Language Models.* Replication package: https://github.com/gwojarnikus/acm-finance-llm

---

## License

Released under the **Creative Commons Attribution 4.0 International (CC BY 4.0)** license —
code, data, prompts, and text alike. You may share and adapt the material, including
commercially, with appropriate credit. See `LICENSE` and
https://creativecommons.org/licenses/by/4.0/.
