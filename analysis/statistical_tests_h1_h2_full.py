"""Statistical tests H1/H2 for Stage 6 FULL cohort (60 reports, N=27 per AKM/B1).

H1: AKM > B1
  - Mann-Whitney U unpaired (n=27 vs n=27) — primary test, highest power
  - Wilcoxon paired by case (3 cases): best-of-AKM per case vs best-of-B1 per case
  - Wilcoxon paired by case: mean-of-AKM per case vs mean-of-B1 per case

H2: AKM ≈ R1
  - Mann-Whitney U unpaired (n=27 vs n=6)
  - Wilcoxon paired by case: mean-of-AKM per case vs mean-of-R1 per case (N=3)
  - Per-case best-of comparisons

Friedman test across three groups per case (best-of comparison).

Effect sizes: rank-biserial correlation (r_rb) for Mann-Whitney; Cohen's d for paired.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parents[1]
FULL_DIR = REPO_ROOT / "sources/data/evaluation/full"
OUT_FILE = FULL_DIR / "statistical-tests-report-full.json"

CASES = ["S1", "S2", "S3"]


def load_all() -> list[dict]:
    out = []
    for path in sorted(FULL_DIR.glob("eval-*-aggregate.json")):
        out.append(json.loads(path.read_text()))
    return out


def rank_biserial_from_U(U: float, n1: int, n2: int) -> float:
    """r_rb = 2U/(n1*n2) - 1. Range [-1, 1]; positive = group1 (first sample) > group2.

    scipy.stats.mannwhitneyu returns U for first sample (sum of its ranks - n1*(n1+1)/2).
    U_max = n1*n2; U at tie = n1*n2/2. So r_rb = 2*U/(n1*n2) - 1 puts midpoint at 0.
    """
    return (2.0 * U) / (n1 * n2) - 1.0


def cohens_d_paired(x: np.ndarray, y: np.ndarray) -> float:
    diff = x - y
    if diff.std(ddof=1) == 0:
        return float("inf") if diff.mean() != 0 else 0.0
    return float(diff.mean() / diff.std(ddof=1))


def main() -> None:
    reports = load_all()

    by_group_case: dict[tuple[str, str], list[float]] = defaultdict(list)
    by_group: dict[str, list[float]] = defaultdict(list)
    by_id: dict[str, float] = {}
    for r in reports:
        by_id[r["report_id"]] = r["S_final"]
        by_group_case[(r["response_type"], r["case_id"])].append(r["S_final"])
        by_group[r["response_type"]].append(r["S_final"])

    akm_all = np.array(by_group["AKM"])
    b1_all = np.array(by_group["B1"])
    r1_all = np.array(by_group["R1"])

    # Per-case aggregates
    per_case_summary = {}
    for case in CASES:
        akm_case = by_group_case[("AKM", case)]
        b1_case = by_group_case[("B1", case)]
        r1_case = by_group_case[("R1", case)]
        per_case_summary[case] = {
            "AKM": {"n": len(akm_case), "mean": float(np.mean(akm_case)),
                     "median": float(np.median(akm_case)), "best": float(max(akm_case))},
            "B1": {"n": len(b1_case), "mean": float(np.mean(b1_case)),
                    "median": float(np.median(b1_case)), "best": float(max(b1_case))},
            "R1": {"n": len(r1_case), "mean": float(np.mean(r1_case)),
                    "median": float(np.median(r1_case)), "best": float(max(r1_case))},
        }

    # H1: AKM > B1
    # Primary: Mann-Whitney unpaired n=27 vs n=27
    mw_h1 = stats.mannwhitneyu(akm_all, b1_all, alternative="two-sided")
    mw_h1_oneside = stats.mannwhitneyu(akm_all, b1_all, alternative="greater")
    r_rb_h1 = rank_biserial_from_U(mw_h1.statistic, len(akm_all), len(b1_all))

    # Paired by case (best-of)
    akm_best = np.array([per_case_summary[c]["AKM"]["best"] for c in CASES])
    b1_best = np.array([per_case_summary[c]["B1"]["best"] for c in CASES])
    r1_best = np.array([per_case_summary[c]["R1"]["best"] for c in CASES])
    akm_mean_pc = np.array([per_case_summary[c]["AKM"]["mean"] for c in CASES])
    b1_mean_pc = np.array([per_case_summary[c]["B1"]["mean"] for c in CASES])
    r1_mean_pc = np.array([per_case_summary[c]["R1"]["mean"] for c in CASES])

    try:
        wsr_best_h1 = stats.wilcoxon(akm_best, b1_best, method="exact")
    except ValueError as e:
        wsr_best_h1 = type("X", (), {"statistic": None, "pvalue": None})()
    try:
        wsr_mean_h1 = stats.wilcoxon(akm_mean_pc, b1_mean_pc, method="exact")
    except ValueError:
        wsr_mean_h1 = type("X", (), {"statistic": None, "pvalue": None})()

    h1 = {
        "hypothesis": "H1: AKM > B1 (S_final)",
        "primary_test": {
            "test": "Mann-Whitney U (unpaired, AKM n=27 vs B1 n=27)",
            "U_statistic": float(mw_h1.statistic),
            "p_two_sided": float(mw_h1.pvalue),
            "p_one_sided_AKM_greater": float(mw_h1_oneside.pvalue),
            "rank_biserial_r": r_rb_h1,
            "effect_size_interpretation": (
                "small" if abs(r_rb_h1) < 0.3 else
                "medium" if abs(r_rb_h1) < 0.5 else "large"
            ),
            "mean_AKM": float(akm_all.mean()),
            "mean_B1": float(b1_all.mean()),
            "delta": float(akm_all.mean() - b1_all.mean()),
        },
        "secondary_paired_best_per_case": {
            "n_pairs": 3,
            "akm_best_per_case": akm_best.tolist(),
            "b1_best_per_case": b1_best.tolist(),
            "wilcoxon_statistic": float(wsr_best_h1.statistic) if wsr_best_h1.statistic is not None else None,
            "wilcoxon_p_two_sided": float(wsr_best_h1.pvalue) if wsr_best_h1.pvalue is not None else None,
            "cohens_d_paired": cohens_d_paired(akm_best, b1_best),
            "all_pairs_AKM_greater": bool(all(akm_best > b1_best)),
        },
        "secondary_paired_mean_per_case": {
            "n_pairs": 3,
            "akm_mean_per_case": akm_mean_pc.tolist(),
            "b1_mean_per_case": b1_mean_pc.tolist(),
            "wilcoxon_statistic": float(wsr_mean_h1.statistic) if wsr_mean_h1.statistic is not None else None,
            "wilcoxon_p_two_sided": float(wsr_mean_h1.pvalue) if wsr_mean_h1.pvalue is not None else None,
            "cohens_d_paired": cohens_d_paired(akm_mean_pc, b1_mean_pc),
            "all_pairs_AKM_greater": bool(all(akm_mean_pc > b1_mean_pc)),
        },
    }

    # H2: AKM vs R1
    mw_h2 = stats.mannwhitneyu(akm_all, r1_all, alternative="two-sided")
    mw_h2_oneside_less = stats.mannwhitneyu(akm_all, r1_all, alternative="less")
    r_rb_h2 = rank_biserial_from_U(mw_h2.statistic, len(akm_all), len(r1_all))

    try:
        wsr_best_h2 = stats.wilcoxon(akm_best, r1_best, method="exact")
    except ValueError:
        wsr_best_h2 = type("X", (), {"statistic": None, "pvalue": None})()
    try:
        wsr_mean_h2 = stats.wilcoxon(akm_mean_pc, r1_mean_pc, method="exact")
    except ValueError:
        wsr_mean_h2 = type("X", (), {"statistic": None, "pvalue": None})()

    h2 = {
        "hypothesis": "H2: AKM ≈ R1 (or AKM < R1) (S_final)",
        "primary_test": {
            "test": "Mann-Whitney U (unpaired, AKM n=27 vs R1 n=6)",
            "U_statistic": float(mw_h2.statistic),
            "p_two_sided": float(mw_h2.pvalue),
            "p_one_sided_AKM_less": float(mw_h2_oneside_less.pvalue),
            "rank_biserial_r": r_rb_h2,
            "mean_AKM": float(akm_all.mean()),
            "mean_R1": float(r1_all.mean()),
            "delta": float(akm_all.mean() - r1_all.mean()),
            "gap_closure_pct_vs_B1": float(
                (akm_all.mean() - b1_all.mean()) / (r1_all.mean() - b1_all.mean()) * 100
            ),
        },
        "secondary_paired_best_per_case": {
            "n_pairs": 3,
            "akm_best_per_case": akm_best.tolist(),
            "r1_best_per_case": r1_best.tolist(),
            "wilcoxon_statistic": float(wsr_best_h2.statistic) if wsr_best_h2.statistic is not None else None,
            "wilcoxon_p_two_sided": float(wsr_best_h2.pvalue) if wsr_best_h2.pvalue is not None else None,
            "cohens_d_paired": cohens_d_paired(akm_best, r1_best),
            "all_pairs_AKM_less": bool(all(akm_best < r1_best)),
        },
        "secondary_paired_mean_per_case": {
            "n_pairs": 3,
            "akm_mean_per_case": akm_mean_pc.tolist(),
            "r1_mean_per_case": r1_mean_pc.tolist(),
            "wilcoxon_statistic": float(wsr_mean_h2.statistic) if wsr_mean_h2.statistic is not None else None,
            "wilcoxon_p_two_sided": float(wsr_mean_h2.pvalue) if wsr_mean_h2.pvalue is not None else None,
            "cohens_d_paired": cohens_d_paired(akm_mean_pc, r1_mean_pc),
            "all_pairs_AKM_less": bool(all(akm_mean_pc < r1_mean_pc)),
        },
    }

    # Friedman across 3 groups, paired by case (best-of)
    friedman_best = stats.friedmanchisquare(akm_best, b1_best, r1_best)
    friedman_mean = stats.friedmanchisquare(akm_mean_pc, b1_mean_pc, r1_mean_pc)
    friedman_block = {
        "hypothesis": "Friedman: AKM vs B1 vs R1 across cases",
        "best_per_case": {
            "chi_square": float(friedman_best.statistic),
            "p_value": float(friedman_best.pvalue),
        },
        "mean_per_case": {
            "chi_square": float(friedman_mean.statistic),
            "p_value": float(friedman_mean.pvalue),
        },
    }

    # Bonferroni for primary Mann-Whitney H1 + H2 (2 tests)
    bonferroni = {
        "method": "Bonferroni for 2 primary Mann-Whitney tests (H1 + H2 unpaired)",
        "alpha_family": 0.05,
        "alpha_per_test": 0.025,
        "raw_p_H1_MW": float(mw_h1.pvalue),
        "raw_p_H2_MW": float(mw_h2.pvalue),
        "H1_significant_at_bonferroni_0_025": float(mw_h1.pvalue) < 0.025,
        "H2_significant_at_bonferroni_0_025": float(mw_h2.pvalue) < 0.025,
    }

    report = {
        "session_id": "etap-6-full-statistics-N60",
        "judge_model": "claude-opus-4-7",
        "evaluation_session": "etap6-full-60-reports-20260516",
        "cohort": {
            "AKM_n": 27, "B1_n": 27, "R1_n": 6, "total": 60,
            "AKM_composition": "3 cases × 9 variants V1-V9",
            "B1_composition": "3 cases × 3 models (D/Ki/Mi) × 3 versions (v1/v2/v3)",
            "R1_composition": "3 cases × 2 sources (C=ChatGPT DR, G=Gemini DR)",
        },
        "group_summary": {
            "AKM": {"n": 27, "mean": float(akm_all.mean()), "sd": float(akm_all.std(ddof=1)),
                     "median": float(np.median(akm_all)), "min": float(akm_all.min()),
                     "max": float(akm_all.max()), "q25": float(np.percentile(akm_all, 25)),
                     "q75": float(np.percentile(akm_all, 75))},
            "B1": {"n": 27, "mean": float(b1_all.mean()), "sd": float(b1_all.std(ddof=1)),
                    "median": float(np.median(b1_all)), "min": float(b1_all.min()),
                    "max": float(b1_all.max()), "q25": float(np.percentile(b1_all, 25)),
                    "q75": float(np.percentile(b1_all, 75))},
            "R1": {"n": 6, "mean": float(r1_all.mean()), "sd": float(r1_all.std(ddof=1)),
                    "median": float(np.median(r1_all)), "min": float(r1_all.min()),
                    "max": float(r1_all.max()), "q25": float(np.percentile(r1_all, 25)),
                    "q75": float(np.percentile(r1_all, 75))},
        },
        "per_case_summary": per_case_summary,
        "H1_AKM_beats_B1": h1,
        "H2_AKM_vs_R1": h2,
        "friedman_across_three_groups": friedman_block,
        "bonferroni_correction": bonferroni,
        "limitations": [
            "Single-judge (claude-opus-4-7) — no cross-model ICC.",
            "No human expert validation (decision 2026-05-17).",
            "D4 verified at text level only (no Python tool execution).",
            "A2 capped at Level 1 (max 6 without WebFetch).",
            "R1 n=6 limits statistical power for H2 paired tests (Wilcoxon exact min p=0.25 for 3 pairs).",
            "Mann-Whitney unpaired AKM vs B1 (n=27 vs 27) provides high power for H1; H2 (n=27 vs n=6) has asymmetric power.",
        ],
        "interpretive_summary": {
            "H1": (f"AKM mean ({akm_all.mean():.3f}) > B1 mean ({b1_all.mean():.3f}); "
                    f"delta = {akm_all.mean() - b1_all.mean():+.3f}; "
                    f"Mann-Whitney U={mw_h1.statistic:.0f}, p_two_sided={mw_h1.pvalue:.4f}; "
                    f"r_rb={r_rb_h1:.3f} ({h1['primary_test']['effect_size_interpretation']} effect)"),
            "H2": (f"AKM mean ({akm_all.mean():.3f}) < R1 mean ({r1_all.mean():.3f}); "
                    f"delta = {akm_all.mean() - r1_all.mean():+.3f}; "
                    f"AKM closes {h2['primary_test']['gap_closure_pct_vs_B1']:.1f}% of gap B1→R1; "
                    f"Mann-Whitney p_two_sided={mw_h2.pvalue:.4f}"),
        },
    }

    OUT_FILE.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {OUT_FILE.relative_to(REPO_ROOT)}")
    print()
    print(f"=== Group means (N=60 cohort) ===")
    print(f"  R1: mean={r1_all.mean():.3f}  sd={r1_all.std(ddof=1):.3f}  (n=6)")
    print(f"  AKM: mean={akm_all.mean():.3f}  sd={akm_all.std(ddof=1):.3f}  (n=27)")
    print(f"  B1: mean={b1_all.mean():.3f}  sd={b1_all.std(ddof=1):.3f}  (n=27)")
    print()
    print(f"=== H1 (AKM > B1, primary Mann-Whitney unpaired n=27 vs n=27) ===")
    print(f"  U = {mw_h1.statistic:.0f}, p_two_sided = {mw_h1.pvalue:.5f}, p_one_sided = {mw_h1_oneside.pvalue:.5f}")
    print(f"  rank-biserial r = {r_rb_h1:+.3f} ({h1['primary_test']['effect_size_interpretation']} effect)")
    print(f"  ⇒ H1 {'SUPPORTED' if mw_h1.pvalue < 0.05 else 'NOT SIGNIFICANT'} at α=0.05")
    print()
    print(f"=== H2 (AKM vs R1, primary Mann-Whitney unpaired n=27 vs n=6) ===")
    print(f"  U = {mw_h2.statistic:.0f}, p_two_sided = {mw_h2.pvalue:.5f}, p_one_sided_less = {mw_h2_oneside_less.pvalue:.5f}")
    print(f"  rank-biserial r = {r_rb_h2:+.3f}")
    print(f"  AKM closes {h2['primary_test']['gap_closure_pct_vs_B1']:.1f}% of B1→R1 gap")
    print(f"  ⇒ H2 (AKM<R1) {'SUPPORTED' if mw_h2.pvalue < 0.05 else 'NOT SIGNIFICANT'} at α=0.05")
    print()
    print(f"=== Friedman 3×3 (best per case) ===")
    print(f"  χ² = {friedman_best.statistic:.3f}, p = {friedman_best.pvalue:.4f}")


if __name__ == "__main__":
    main()
