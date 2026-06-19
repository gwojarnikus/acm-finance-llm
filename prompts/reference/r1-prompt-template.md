# R1 Reference Run — Prompt Template

Used for: `R1-C` (OpenAI Deep Research) and `R1-G` (Gemini Deep Research)
Case placeholder: replace `{{ CASE_PROBLEM }}` with the contents of `cases/case-N-en.md`

---

## Problem

{{ CASE_PROBLEM }}

---

## Output Requirements

Provide a single, coherent document in Markdown format. Apply the following rules without exception:

- **Language:** Respond in the same language as the problem statement above.
- **Style:** Write fluid, engaging prose with professional flair. Avoid overly schematic, robotic structures. Use bullet points only for actual enumerations or lists, not as a substitute for paragraph-based narrative analysis. Ensure natural narrative flow.
- Cite all sources in **APA 7** format.
- Keep the total response within **10 000 words**.
- Write a complete, self-contained response. Do not use back-references such as "as before" or "as stated earlier."

Structure your response using the following sections:

### 1. Problem Diagnosis
A one-sentence definition of the essence of the challenge.

### 2. Data Verification (Grounding)
List the specific numerical data and facts on which you base your analysis, together with their source and date. Example: "US CPI inflation: 3.2% (source: BLS, date: ...)". Format each citation in APA 7.

### 3. In-Depth Analysis
A logical cause-and-effect chain. Write as cohesive, fluid text with paragraphs, avoiding excessive bulleting.

### 4. Recommended Strategy or Key Conclusions
If the question calls for action, provide a clear, actionable proposal. If the question is explanatory, comparative, diagnostic, or interpretive, provide the key conclusions, implications, and decision-relevant takeaways. Do not force a strategy when it is not warranted.

---

### 5. Research Process Metadata (self-reported)

After completing the analysis above, report your own research process in the following structured block. Be as accurate as possible about your actual process.

```
sources_consulted_estimated: [integer]
search_queries_used:
  - "[query 1]"
  - "[query 2]"
  - ...
confidence_level_pct: [0–100]
confidence_justification: "[one sentence]"
key_data_limitations:
  - "[limitation 1]"
  - "[limitation 2]"
output_word_count_estimated: [integer]
```

Do not skip this section. If you are uncertain about a value, provide your best estimate and note it with `(estimated)`.
