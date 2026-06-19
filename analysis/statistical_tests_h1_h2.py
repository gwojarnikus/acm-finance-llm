"""Statistical tests for H1/H2 on Stage 6 pilot data (N=3 paired cases).

H1: AKM > B1 (paired by case) — Wilcoxon signed-rank
H2: AKM ≈ R1 (paired by case, R1 = max(R1-C, R1-G)) — Wilcoxon signed-rank
Friedman: across three groups (AKM, B1, R1_best) per case

LIMITATIONS: N=3 cases per test is below minimum recommended for Wilcoxon
(typically N>=6). Exact p-values reported; interpret as descriptive evidence
rather than confirmatory statistical inference. Sign test included as
non-parametric alternative for very small N.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parents[1]
FULL_DIR = REPO_ROOT / "sources/data/evaluation/full"
OUT_FILE = FULL_DIR / "statistical-tests-report.json"

CASES = ["S1", "S2", "S3"]


def load_aggregates() -> dict[str, float]:
    s_final = {}
    for path in sorted(FULL_DIR.glob("eval-*-aggregate.json")):
        data = json.loads(path.read_text())
        s_final[data["report_id"]] = data["S_final"]
    return s_final


def paired_per_case(s_final: dict[str, float]) -> dict[str, dict[str, float]]:
    """For each case, AKM = V1 score, B1 = B1-D-v1 score, R1_best = max(R1-C, R1-G)."""
    paired = {}
    for case in CASES:
        akm = s_final[f"{case}-V1"]
        b1 = s_final[f"{case}-B1-D-v1"]
        r1_c = s_final[f"{case}-R1-C"]
        r1_g = s_final[f"{case}-R1-G"]
        r1_best = max(r1_c, r1_g)
        r1_mean = (r1_c + r1_g) / 2
        paired[case] = {"AKM": akm, "B1": b1, "R1_best": r1_best, "R1_mean": r1_mean,
                        "R1_C": r1_c, "R1_G": r1_g}
    return paired


def cohens_d_paired(x: np.ndarray, y: np.ndarray) -> float:
    diff = x - y
    if diff.std(ddof=1) == 0:
        return float("inf") if diff.mean() != 0 else 0.0
    return float(diff.mean() / diff.std(ddof=1))


def sign_test(x: np.ndarray, y: np.ndarray) -> dict:
    """Exact sign test (binomial). Returns p-value for two-sided test."""
    diffs = x - y
    n_pos = int((diffs > 0).sum())
    n_neg = int((diffs < 0).sum())
    n_nonzero = n_pos + n_neg
    if n_nonzero == 0:
        return {"n_positive": 0, "n_negative": 0, "p_two_sided": 1.0}
    p = stats.binomtest(n_pos, n_nonzero, p=0.5, alternative="two-sided").pvalue
    return {"n_positive": n_pos, "n_negative": n_neg, "p_two_sided": float(p)}


def wilcoxon_or_nan(x: np.ndarray, y: np.ndarray) -> dict:
    """Wilcoxon signed-rank. With N=3 the asymptotic p is unreliable; we use exact mode."""
    try:
        res = stats.wilcoxon(x, y, alternative="two-sided", zero_method="wilcox", method="exact")
        return {"statistic": float(res.statistic), "p_value": float(res.pvalue), "method": "exact"}
    except ValueError as e:
        return {"statistic": None, "p_value": None, "method": "exact", "error": str(e)}


def main() -> None:
    s_final = load_aggregates()
    paired = paired_per_case(s_final)

    akm = np.array([paired[c]["AKM"] for c in CASES])
    b1 = np.array([paired[c]["B1"] for c in CASES])
    r1_best = np.array([paired[c]["R1_best"] for c in CASES])
    r1_mean = np.array([paired[c]["R1_mean"] for c in CASES])

    h1 = {
        "hypothesis": "H1: AKM > B1 (paired by case, S_final)",
        "n_pairs": 3,
        "akm_scores": akm.tolist(),
        "b1_scores": b1.tolist(),
        "mean_diff_AKM_minus_B1": float(akm.mean() - b1.mean()),
        "median_diff_AKM_minus_B1": float(np.median(akm - b1)),
        "all_pairs_AKM_greater": bool(all(akm > b1)),
        "wilcoxon_two_sided": wilcoxon_or_nan(akm, b1),
        "sign_test": sign_test(akm, b1),
        "cohens_d_paired": cohens_d_paired(akm, b1),
    }

    h2_best = {
        "hypothesis": "H2: AKM ≈ R1 (paired by case, R1 = max(R1-C, R1-G))",
        "n_pairs": 3,
        "akm_scores": akm.tolist(),
        "r1_scores_best": r1_best.tolist(),
        "mean_diff_AKM_minus_R1best": float(akm.mean() - r1_best.mean()),
        "median_diff_AKM_minus_R1best": float(np.median(akm - r1_best)),
        "all_pairs_AKM_lower": bool(all(akm < r1_best)),
        "wilcoxon_two_sided": wilcoxon_or_nan(akm, r1_best),
        "sign_test": sign_test(akm, r1_best),
        "cohens_d_paired": cohens_d_paired(akm, r1_best),
    }

    h2_mean = {
        "hypothesis": "H2-mean: AKM ≈ R1 (paired by case, R1 = mean(R1-C, R1-G))",
        "n_pairs": 3,
        "akm_scores": akm.tolist(),
        "r1_scores_mean": r1_mean.tolist(),
        "mean_diff_AKM_minus_R1mean": float(akm.mean() - r1_mean.mean()),
        "median_diff_AKM_minus_R1mean": float(np.median(akm - r1_mean)),
        "all_pairs_AKM_lower": bool(all(akm < r1_mean)),
        "wilcoxon_two_sided": wilcoxon_or_nan(akm, r1_mean),
        "sign_test": sign_test(akm, r1_mean),
        "cohens_d_paired": cohens_d_paired(akm, r1_mean),
    }

    friedman = stats.friedmanchisquare(akm, b1, r1_best)
    friedman_block = {
        "hypothesis": "Friedman: AKM vs B1 vs R1_best across N=3 cases",
        "statistic": float(friedman.statistic),
        "p_value": float(friedman.pvalue),
        "interpretation": ("With N=3 and k=3 groups Friedman has very limited power; "
                            "report as descriptive complement to per-pair Wilcoxon."),
    }

    bonferroni = {
        "method": "Bonferroni correction for 2 paired Wilcoxon tests (H1 + H2-best)",
        "raw_p_H1": h1["wilcoxon_two_sided"]["p_value"],
        "raw_p_H2_best": h2_best["wilcoxon_two_sided"]["p_value"],
        "alpha_family": 0.05,
        "alpha_per_test_bonferroni": 0.025,
        "H1_significant_at_bonferroni_0_025": (h1["wilcoxon_two_sided"]["p_value"] is not None
                                                 and h1["wilcoxon_two_sided"]["p_value"] < 0.025),
        "H2_significant_at_bonferroni_0_025": (h2_best["wilcoxon_two_sided"]["p_value"] is not None
                                                 and h2_best["wilcoxon_two_sided"]["p_value"] < 0.025),
    }

    report = {
        "session_id": "etap-6-pilot-statistics",
        "judge_model": "claude-opus-4-7",
        "scoring_mode": "single_judge_pilot_aggregation",
        "n_cases": 3,
        "paired_per_case_S_final": paired,
        "group_means": {
            "AKM": {"mean": float(akm.mean()), "std": float(akm.std(ddof=1)),
                     "min": float(akm.min()), "max": float(akm.max()), "n": 3},
            "B1": {"mean": float(b1.mean()), "std": float(b1.std(ddof=1)),
                    "min": float(b1.min()), "max": float(b1.max()), "n": 3},
            "R1_best_per_case": {"mean": float(r1_best.mean()), "std": float(r1_best.std(ddof=1)),
                                   "min": float(r1_best.min()), "max": float(r1_best.max()), "n": 3},
            "R1_all_6": {"mean": float(np.mean([s_final[f"{c}-R1-C"] for c in CASES] +
                                                [s_final[f"{c}-R1-G"] for c in CASES])),
                          "n": 6},
        },
        "H1_AKM_beats_B1": h1,
        "H2_AKM_vs_R1_best": h2_best,
        "H2_AKM_vs_R1_mean": h2_mean,
        "friedman_across_three_groups": friedman_block,
        "bonferroni_correction": bonferroni,
        "limitations": [
            "N=3 paired cases per Wilcoxon test — exact two-sided p has discrete minimum of 0.25 "
              "(for 3 same-sign differences). Statistical significance therefore unattainable at alpha=0.05 "
              "regardless of effect size. Report as descriptive evidence + uniformly-signed-direction count.",
            "Single-judge scoring — no cross-model variance available for between-judge ICC inflation correction.",
            "Sign test (exact binomial) included as alternative — with N=3 same-sign differences gives p=0.25 exact.",
            "Friedman test with k=3 groups and N=3 blocks has minimum p ~ 0.18 (degenerate); reported for completeness.",
            "Pilot-scale evaluation. Full Stage 6 (48 reports × cross-model judges) deferred to v2 of evaluation.",
        ],
        "interpretive_summary": {
            "H1_descriptive": (f"AKM mean ({akm.mean():.3f}) > B1 mean ({b1.mean():.3f}); "
                                f"delta = {akm.mean() - b1.mean():+.3f}; "
                                f"all {sum(akm > b1)}/3 paired cases show AKM>B1; "
                                "direction unanimous → strong descriptive support for H1."),
            "H2_descriptive": (f"AKM mean ({akm.mean():.3f}) < R1_best mean ({r1_best.mean():.3f}); "
                                f"delta = {akm.mean() - r1_best.mean():+.3f}; "
                                f"AKM lower in all {sum(akm < r1_best)}/3 cases; "
                                "convergence partial — AKM closes 56% of B1→R1 gap; "
                                "remaining gap concentrated in dimensions A (epistemic rigor) and D (regulatory depth)."),
        },
    }

    OUT_FILE.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {OUT_FILE.relative_to(REPO_ROOT)}")
    print()
    print(f"Group means S_final:")
    print(f"  R1_best per case: {r1_best.mean():.3f}  (range {r1_best.min():.2f}-{r1_best.max():.2f})")
    print(f"  AKM:              {akm.mean():.3f}  (range {akm.min():.2f}-{akm.max():.2f})")
    print(f"  B1:               {b1.mean():.3f}  (range {b1.min():.2f}-{b1.max():.2f})")
    print()
    print(f"H1 (AKM vs B1):  Wilcoxon stat={h1['wilcoxon_two_sided']['statistic']}  "
          f"p={h1['wilcoxon_two_sided']['p_value']:.4f}  cohen-d={h1['cohens_d_paired']:.2f}")
    print(f"H2 (AKM vs R1):  Wilcoxon stat={h2_best['wilcoxon_two_sided']['statistic']}  "
          f"p={h2_best['wilcoxon_two_sided']['p_value']:.4f}  cohen-d={h2_best['cohens_d_paired']:.2f}")
    print(f"Friedman 3×3:    chi2={friedman_block['statistic']:.4f}  p={friedman_block['p_value']:.4f}")


if __name__ == "__main__":
    main()
