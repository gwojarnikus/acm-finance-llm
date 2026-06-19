"""Stage 6 (pilot-scale) aggregation.

Single-judge Claude Opus 4.7 scoring on 12 reports (3 AKM + 3 B1 + 6 R1).
No new API calls. Reads existing per-criterion scores from:
  - sources/data/evaluation/llm-judge/rubric/eval-llm-etap3b-pilot-12reports.json
    (3 AKM + 3 B1 with full per-criterion scores)
  - sources/data/evaluation/llm-judge/rubric/eval-llm-pilot-6r1-second-judge.json
    (6 R1 with full per-criterion scores — same Claude judge)

Computes per-report:
  - dimension means (with B6 subweight 0.5 per README §7.1)
  - S_final = lambda * sum(weight_d * dim_mean_d)
  - Soft Veto lambda per akm-eval-pro-v1.json

Writes 12 aggregate JSON files to sources/data/evaluation/full/.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
EVAL_DIR = REPO_ROOT / "sources/data/evaluation"
PILOT_FILE = EVAL_DIR / "llm-judge/rubric/eval-llm-etap3b-pilot-12reports.json"
R1_FILE = EVAL_DIR / "llm-judge/rubric/eval-llm-pilot-6r1-second-judge.json"
RUBRIC_FILE = REPO_ROOT / "sources/data/benchmarks/akm-eval-pro-v1.json"
OUT_DIR = EVAL_DIR / "full"

DIM_WEIGHTS = {"A": 0.25, "B": 0.20, "C": 0.20, "D": 0.25, "E": 0.10}
DIM_CRITERIA = {
    "A": ["A1", "A2", "A3", "A4", "A5"],
    "B": ["B1", "B2", "B3", "B4", "B5", "B6"],
    "C": ["C1", "C2", "C3", "C4", "C5", "C6"],
    "D": ["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8"],
    "E": ["E1", "E2", "E3", "E4", "E5"],
}


def dimension_mean(dim: str, scores: dict[str, float]) -> float:
    """Mean of dimension criteria. B6 halved per subweight rule, divided by N."""
    crits = DIM_CRITERIA[dim]
    total = 0.0
    for c in crits:
        s = scores[c]
        if c == "B6":
            s = s * 0.5
        total += s
    return total / len(crits)


def soft_veto_lambda(scores: dict[str, float], fabrication_detected: bool) -> tuple[float, list[str]]:
    """Return (lambda, list of triggered rules)."""
    triggers = []
    if scores["A1"] < 3.0:
        triggers.append("A1<3.0")
    if scores["A2"] < 2.0 and fabrication_detected:
        triggers.append("A2<2.0+fabrication")
    if scores["D4"] < 2.0:
        triggers.append("D4<2.0")
    return (0.5 if triggers else 1.0), triggers


def aggregate_report(report_id: str, scores: dict[str, float], response_type: str,
                     fabrication_detected: bool = False) -> dict:
    dim_means = {d: round(dimension_mean(d, scores), 4) for d in DIM_WEIGHTS}
    weighted_sum = sum(DIM_WEIGHTS[d] * dim_means[d] for d in DIM_WEIGHTS)
    lam, triggers = soft_veto_lambda(scores, fabrication_detected)
    s_final = round(lam * weighted_sum, 4)

    case_id, variant_id = report_id.split("-", 1)

    return {
        "report_id": report_id,
        "case_id": case_id,
        "variant_id": variant_id,
        "response_type": response_type,
        "judge_model": "claude-opus-4-7",
        "judge_temperature": 0.0,
        "evaluation_mode": "single_judge_pilot_aggregation",
        "scoring_source": {
            "AKM_B1_primary": str(PILOT_FILE.relative_to(REPO_ROOT)),
            "R1_primary": str(R1_FILE.relative_to(REPO_ROOT)),
        },
        "per_criterion_scores": {c: scores[c] for d in DIM_CRITERIA.values() for c in d},
        "dimension_means_with_B6_subweight": dim_means,
        "dimension_weights": DIM_WEIGHTS,
        "weighted_sum": round(weighted_sum, 4),
        "soft_veto": {
            "lambda": lam,
            "triggers": triggers,
            "fabrication_detected_A2": fabrication_detected,
        },
        "S_final": s_final,
        "limitations": [
            "Single-judge (claude-opus-4-7) — no cross-model ICC available in pilot.",
            "Compact pilot scoring (no full per-criterion diagnostic JSON).",
            "D4 verified at text level only (no Python tool execution).",
            "A2 capped via Level 1 (formal) verification only.",
        ],
    }


def extract_scores(report_block: dict) -> tuple[dict[str, float], bool]:
    scores = {}
    fabrication = False
    for crit_id in [c for d in DIM_CRITERIA.values() for c in d]:
        entry = report_block[crit_id]
        scores[crit_id] = entry["score"]
        if crit_id == "A2" and entry.get("fabrication_detected"):
            fabrication = True
    return scores, fabrication


def main() -> None:
    pilot = json.loads(PILOT_FILE.read_text())
    r1 = json.loads(R1_FILE.read_text())

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    reports_to_aggregate = [
        ("S1-V1", "AKM", pilot["scorings_per_report"]["S1-V1"]),
        ("S2-V1", "AKM", pilot["scorings_per_report"]["S2-V1"]),
        ("S3-V1", "AKM", pilot["scorings_per_report"]["S3-V1"]),
        ("S1-B1-D-v1", "B1", pilot["scorings_per_report"]["S1-B1-D-v1"]),
        ("S2-B1-D-v1", "B1", pilot["scorings_per_report"]["S2-B1-D-v1"]),
        ("S3-B1-D-v1", "B1", pilot["scorings_per_report"]["S3-B1-D-v1"]),
        ("S1-R1-C", "R1", r1["scorings"]["S1-R1-C"]),
        ("S1-R1-G", "R1", r1["scorings"]["S1-R1-G"]),
        ("S2-R1-C", "R1", r1["scorings"]["S2-R1-C"]),
        ("S2-R1-G", "R1", r1["scorings"]["S2-R1-G"]),
        ("S3-R1-C", "R1", r1["scorings"]["S3-R1-C"]),
        ("S3-R1-G", "R1", r1["scorings"]["S3-R1-G"]),
    ]

    summary_rows = []
    for report_id, rtype, block in reports_to_aggregate:
        scores, fab = extract_scores(block)
        agg = aggregate_report(report_id, scores, rtype, fabrication_detected=fab)
        out_path = OUT_DIR / f"eval-{report_id}-aggregate.json"
        out_path.write_text(json.dumps(agg, indent=2, ensure_ascii=False) + "\n")
        summary_rows.append({
            "report_id": report_id,
            "response_type": rtype,
            "S_final": agg["S_final"],
            "lambda": agg["soft_veto"]["lambda"],
            "veto_triggers": ",".join(agg["soft_veto"]["triggers"]) or "none",
            **{f"dim_{d}": agg["dimension_means_with_B6_subweight"][d] for d in DIM_WEIGHTS},
        })
        print(f"wrote {out_path.name}  S_final={agg['S_final']:.3f}  lambda={agg['soft_veto']['lambda']}")

    # Quick validation vs existing aggregates in input files (Delta acceptable < 0.30)
    print("\n=== validation vs existing aggregates ===")
    existing_pilot = pilot.get("aggregates", {})
    existing_r1 = r1.get("aggregates", {})
    for row in summary_rows:
        rid = row["report_id"]
        ref = existing_pilot.get(rid) or existing_r1.get(rid)
        if ref and "S_final" in ref:
            delta = abs(row["S_final"] - ref["S_final"])
            note = "OK" if delta < 0.30 else "WARN"
            print(f"  {rid}: computed={row['S_final']:.3f} ref={ref['S_final']:.3f} delta={delta:.3f} [{note}]")

    print(f"\nTotal aggregated: {len(summary_rows)} reports.")


if __name__ == "__main__":
    main()
