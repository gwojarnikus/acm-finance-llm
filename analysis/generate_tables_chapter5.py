"""Generate evaluation-summary.csv and Chapter 5 tables from aggregated pilot data.

Outputs to sources/data/evaluation/full/:
  - evaluation-summary.csv (one row per report, all 12)
  - tables-for-chapter-5/table-S_final-ranking.csv
  - tables-for-chapter-5/table-group-means-per-case.csv
  - tables-for-chapter-5/table-dimension-means-per-group.csv
  - tables-for-chapter-5/table-per-criterion-by-group.csv
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from statistics import mean, stdev

REPO_ROOT = Path(__file__).resolve().parents[1]
FULL_DIR = REPO_ROOT / "sources/data/evaluation/full"
TABLES_DIR = FULL_DIR / "tables-for-chapter-5"

DIMS = ["A", "B", "C", "D", "E"]
ALL_CRITERIA = ["A1","A2","A3","A4","A5",
                 "B1","B2","B3","B4","B5","B6",
                 "C1","C2","C3","C4","C5","C6",
                 "D1","D2","D3","D4","D5","D6","D7","D8",
                 "E1","E2","E3","E4","E5"]


def load_aggregates() -> list[dict]:
    return [json.loads(p.read_text()) for p in sorted(FULL_DIR.glob("eval-*-aggregate.json"))]


def write_summary_csv(reports: list[dict]) -> None:
    out = FULL_DIR / "evaluation-summary.csv"
    fieldnames = [
        "report_id", "case_id", "response_type",
        "S_final", "soft_veto_lambda", "soft_veto_triggers",
        "dim_A", "dim_B_with_B6_sub", "dim_C", "dim_D", "dim_E",
        "judge_model",
    ]
    with out.open("w", newline="") as fp:
        w = csv.DictWriter(fp, fieldnames=fieldnames)
        w.writeheader()
        for r in reports:
            dims = r["dimension_means_with_B6_subweight"]
            w.writerow({
                "report_id": r["report_id"],
                "case_id": r["case_id"],
                "response_type": r["response_type"],
                "S_final": f"{r['S_final']:.4f}",
                "soft_veto_lambda": r["soft_veto"]["lambda"],
                "soft_veto_triggers": ",".join(r["soft_veto"]["triggers"]) or "none",
                "dim_A": f"{dims['A']:.4f}",
                "dim_B_with_B6_sub": f"{dims['B']:.4f}",
                "dim_C": f"{dims['C']:.4f}",
                "dim_D": f"{dims['D']:.4f}",
                "dim_E": f"{dims['E']:.4f}",
                "judge_model": r["judge_model"],
            })
    print(f"wrote {out.relative_to(REPO_ROOT)}")


def write_ranking(reports: list[dict]) -> None:
    out = TABLES_DIR / "table-S_final-ranking.csv"
    sorted_r = sorted(reports, key=lambda x: -x["S_final"])
    with out.open("w", newline="") as fp:
        w = csv.writer(fp)
        w.writerow(["rank", "report_id", "response_type", "S_final"])
        for i, r in enumerate(sorted_r, start=1):
            w.writerow([i, r["report_id"], r["response_type"], f"{r['S_final']:.4f}"])
    print(f"wrote {out.relative_to(REPO_ROOT)}")


def write_group_means_per_case(reports: list[dict]) -> None:
    out = TABLES_DIR / "table-group-means-per-case.csv"
    by_case_group: dict[tuple[str, str], list[float]] = {}
    for r in reports:
        key = (r["case_id"], r["response_type"])
        by_case_group.setdefault(key, []).append(r["S_final"])
    cases = sorted({r["case_id"] for r in reports})
    groups = ["AKM", "B1", "R1"]
    with out.open("w", newline="") as fp:
        w = csv.writer(fp)
        w.writerow(["case_id", "AKM_S_final", "B1_S_final", "R1_C_S_final",
                     "R1_G_S_final", "R1_best_S_final", "R1_mean_S_final",
                     "delta_AKM_minus_B1", "delta_AKM_minus_R1_best"])
        for case in cases:
            akm = next(r["S_final"] for r in reports if r["report_id"] == f"{case}-V1")
            b1 = next(r["S_final"] for r in reports if r["report_id"] == f"{case}-B1-D-v1")
            r1c = next(r["S_final"] for r in reports if r["report_id"] == f"{case}-R1-C")
            r1g = next(r["S_final"] for r in reports if r["report_id"] == f"{case}-R1-G")
            r1_best = max(r1c, r1g)
            r1_mean = (r1c + r1g) / 2
            w.writerow([case, f"{akm:.4f}", f"{b1:.4f}", f"{r1c:.4f}", f"{r1g:.4f}",
                         f"{r1_best:.4f}", f"{r1_mean:.4f}",
                         f"{akm - b1:+.4f}", f"{akm - r1_best:+.4f}"])
    print(f"wrote {out.relative_to(REPO_ROOT)}")


def write_dim_means_per_group(reports: list[dict]) -> None:
    out = TABLES_DIR / "table-dimension-means-per-group.csv"
    by_group: dict[str, list[dict]] = {}
    for r in reports:
        by_group.setdefault(r["response_type"], []).append(r)
    with out.open("w", newline="") as fp:
        w = csv.writer(fp)
        w.writerow(["group", "n_reports",
                     "dim_A_mean", "dim_A_sd",
                     "dim_B_mean", "dim_B_sd",
                     "dim_C_mean", "dim_C_sd",
                     "dim_D_mean", "dim_D_sd",
                     "dim_E_mean", "dim_E_sd",
                     "S_final_mean", "S_final_sd"])
        for group in ["AKM", "B1", "R1"]:
            grp = by_group.get(group, [])
            n = len(grp)
            row = [group, n]
            for d in DIMS:
                vals = [r["dimension_means_with_B6_subweight"][d] for r in grp]
                m = mean(vals) if vals else 0.0
                sd = stdev(vals) if len(vals) >= 2 else 0.0
                row += [f"{m:.4f}", f"{sd:.4f}"]
            s_finals = [r["S_final"] for r in grp]
            row += [f"{mean(s_finals):.4f}",
                     f"{stdev(s_finals):.4f}" if len(s_finals) >= 2 else "0.0000"]
            w.writerow(row)
    print(f"wrote {out.relative_to(REPO_ROOT)}")


def write_per_criterion_by_group(reports: list[dict]) -> None:
    """For each of 30 criteria show group means + gap AKM-B1, R1-AKM, R1-B1."""
    out = TABLES_DIR / "table-per-criterion-by-group.csv"
    by_group: dict[str, list[dict]] = {}
    for r in reports:
        by_group.setdefault(r["response_type"], []).append(r)
    with out.open("w", newline="") as fp:
        w = csv.writer(fp)
        w.writerow(["criterion", "dimension",
                     "AKM_mean", "B1_mean", "R1_mean",
                     "gap_AKM_minus_B1", "gap_R1_minus_AKM", "gap_R1_minus_B1"])
        for crit in ALL_CRITERIA:
            dim = crit[0]
            def _extract(entry):
                # per_criterion_scores entries may be {"score": x, "j": ...} or just x
                v = entry["per_criterion_scores"][crit]
                if isinstance(v, dict):
                    return v.get("score")
                return v
            akm_vals = [_extract(r) for r in by_group.get("AKM", []) if _extract(r) is not None]
            b1_vals = [_extract(r) for r in by_group.get("B1", []) if _extract(r) is not None]
            r1_vals = [_extract(r) for r in by_group.get("R1", []) if _extract(r) is not None]
            akm_m = mean(akm_vals) if akm_vals else None
            b1_m = mean(b1_vals) if b1_vals else None
            r1_m = mean(r1_vals) if r1_vals else None
            w.writerow([
                crit, dim,
                f"{akm_m:.3f}" if akm_m is not None else "",
                f"{b1_m:.3f}" if b1_m is not None else "",
                f"{r1_m:.3f}" if r1_m is not None else "",
                f"{akm_m - b1_m:+.3f}" if akm_m is not None and b1_m is not None else "",
                f"{r1_m - akm_m:+.3f}" if r1_m is not None and akm_m is not None else "",
                f"{r1_m - b1_m:+.3f}" if r1_m is not None and b1_m is not None else "",
            ])
    print(f"wrote {out.relative_to(REPO_ROOT)}")


def main() -> None:
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    reports = load_aggregates()
    print(f"Loaded {len(reports)} aggregates.")
    write_summary_csv(reports)
    write_ranking(reports)
    write_group_means_per_case(reports)
    write_dim_means_per_group(reports)
    write_per_criterion_by_group(reports)


if __name__ == "__main__":
    main()
