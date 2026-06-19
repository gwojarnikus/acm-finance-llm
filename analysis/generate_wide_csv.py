"""Generate wide CSV: one row per report, columns = all 30 criteria + meta + tokens.

Outputs sources/data/evaluation/full/evaluation-summary-wide.csv with:
  - report_id, case_id, response_type
  - 30 per-criterion scores (A1..E5)
  - dim_A..dim_E (with B6 subweight 0.5), S_final, lambda, soft_veto_triggers
  - tokens for report GENERATION (sum across AKM steps; single file for B1; null for R1 DR)
  - searches, iterations, judge_model

Token source map (generation, NOT judge scoring):
  AKM: sum sources/data/runs/akm/{case}/run-{case}-V1/run-{case}-V1-step*.json
  B1:  sources/data/runs/baseline/B1/run-{case}-B1-D-v1.json
  R1:  sources/data/runs/reference/R1/run-{case}-R1-{C,G}.json (tokens usually null for Deep Research)
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FULL_DIR = REPO_ROOT / "sources/data/evaluation/full"
RUNS_DIR = REPO_ROOT / "sources/data/runs"
OUT = FULL_DIR / "evaluation-summary-wide.csv"

ALL_CRITERIA = ["A1","A2","A3","A4","A5",
                 "B1","B2","B3","B4","B5","B6",
                 "C1","C2","C3","C4","C5","C6",
                 "D1","D2","D3","D4","D5","D6","D7","D8",
                 "E1","E2","E3","E4","E5"]

DIMS = ["A", "B", "C", "D", "E"]


def load_generation_tokens(report_id: str, response_type: str) -> dict:
    """Return token / iteration / search totals for the report's GENERATION phase."""
    out = {"tokens_in": None, "tokens_out": None, "tokens_total": None,
           "iterations": None, "searches": None, "duration_sec": None,
           "generation_model": None, "token_source_path": None}

    case = report_id.split("-")[0]  # S1/S2/S3

    if response_type == "AKM":
        # run-{case}-V1 directory with step JSONs
        variant = report_id.split("-", 1)[1]  # e.g. V1
        run_dir = RUNS_DIR / f"akm/{case}/run-{case}-{variant}"
        if not run_dir.is_dir():
            return out
        step_files = sorted(run_dir.glob(f"run-{case}-{variant}-step*.json"))
        if not step_files:
            return out
        t_in = t_out = total = searches = 0
        for sf in step_files:
            data = json.loads(sf.read_text())
            t_in += (data.get("tokens_analyst_in") or 0) + \
                     (data.get("tokens_critic_in") or 0) + \
                     (data.get("tokens_moderator_in") or 0)
            t_out += (data.get("tokens_analyst_out") or 0) + \
                       (data.get("tokens_critic_out") or 0) + \
                       (data.get("tokens_moderator_out") or 0)
            total += data.get("total_llm_tokens") or 0
            searches += data.get("total_searches") or 0
        out.update({
            "tokens_in": t_in or None,
            "tokens_out": t_out or None,
            "tokens_total": total or (t_in + t_out) or None,
            "iterations": len(step_files),
            "searches": searches or None,
            "generation_model": "AKM (DeepSeek analyst + critic + moderator)",
            "token_source_path": str(run_dir.relative_to(REPO_ROOT)),
        })

    elif response_type == "B1":
        # report_id like S1-B1-D-v1 / S1-B1-Ki-v2 / S1-B1-Mi-v3
        run_file = RUNS_DIR / f"baseline/B1/run-{report_id}.json"
        if not run_file.exists():
            return out
        data = json.loads(run_file.read_text())
        t_in = (data.get("tokens_analyst_in") or 0) + \
                (data.get("tokens_critic_in") or 0) + \
                (data.get("tokens_moderator_in") or 0)
        t_out = (data.get("tokens_analyst_out") or 0) + \
                  (data.get("tokens_critic_out") or 0) + \
                  (data.get("tokens_moderator_out") or 0)
        searches = (data.get("searches_analyst") or 0) + (data.get("searches_critic") or 0)
        out.update({
            "tokens_in": t_in or None,
            "tokens_out": t_out or None,
            "tokens_total": (t_in + t_out) or None,
            "iterations": data.get("step"),
            "searches": searches or None,
            "generation_model": "B1-DeepSeek (single-shot)",
            "token_source_path": str(run_file.relative_to(REPO_ROOT)),
        })

    elif response_type == "R1":
        # report_id like S1-R1-C or S1-R1-G → file is run-{case}-R1-{C|G}.json
        suffix = report_id.split("-")[-1]  # C or G
        run_file = RUNS_DIR / f"reference/R1/run-{case}-R1-{suffix}.json"
        if not run_file.exists():
            return out
        data = json.loads(run_file.read_text())
        out.update({
            "tokens_in": data.get("tokens_input"),
            "tokens_out": data.get("tokens_output"),
            "tokens_total": ((data.get("tokens_input") or 0) +
                              (data.get("tokens_output") or 0)) or None,
            "iterations": data.get("search_calls"),
            "searches": data.get("search_calls"),
            "duration_sec": data.get("duration_sec"),
            "generation_model": data.get("models"),
            "token_source_path": str(run_file.relative_to(REPO_ROOT)),
        })

    return out


def main() -> None:
    aggregates = [json.loads(p.read_text()) for p in sorted(FULL_DIR.glob("eval-*-aggregate.json"))]

    fieldnames = (
        ["report_id", "case_id", "response_type", "S_final",
          "soft_veto_lambda", "soft_veto_triggers",
          "dim_A", "dim_B_with_B6_sub", "dim_C", "dim_D", "dim_E"] +
        ALL_CRITERIA +
        ["generation_model", "generation_tokens_in", "generation_tokens_out",
          "generation_tokens_total", "generation_iterations",
          "generation_searches", "generation_duration_sec", "generation_source_path",
          "judge_model"]
    )

    rows = []
    for r in aggregates:
        gen = load_generation_tokens(r["report_id"], r["response_type"])
        row = {
            "report_id": r["report_id"],
            "case_id": r["case_id"],
            "response_type": r["response_type"],
            "S_final": f"{r['S_final']:.4f}",
            "soft_veto_lambda": r["soft_veto"]["lambda"],
            "soft_veto_triggers": ",".join(r["soft_veto"]["triggers"]) or "none",
            "dim_A": f"{r['dimension_means_with_B6_subweight']['A']:.4f}",
            "dim_B_with_B6_sub": f"{r['dimension_means_with_B6_subweight']['B']:.4f}",
            "dim_C": f"{r['dimension_means_with_B6_subweight']['C']:.4f}",
            "dim_D": f"{r['dimension_means_with_B6_subweight']['D']:.4f}",
            "dim_E": f"{r['dimension_means_with_B6_subweight']['E']:.4f}",
            "generation_model": gen["generation_model"] or "",
            "generation_tokens_in": gen["tokens_in"] if gen["tokens_in"] is not None else "",
            "generation_tokens_out": gen["tokens_out"] if gen["tokens_out"] is not None else "",
            "generation_tokens_total": gen["tokens_total"] if gen["tokens_total"] is not None else "",
            "generation_iterations": gen["iterations"] if gen["iterations"] is not None else "",
            "generation_searches": gen["searches"] if gen["searches"] is not None else "",
            "generation_duration_sec": gen["duration_sec"] if gen["duration_sec"] is not None else "",
            "generation_source_path": gen["token_source_path"] or "",
            "judge_model": r["judge_model"],
        }
        for c in ALL_CRITERIA:
            v = r["per_criterion_scores"][c]
            row[c] = v["score"] if isinstance(v, dict) else v
        rows.append(row)

    with OUT.open("w", newline="") as fp:
        w = csv.DictWriter(fp, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow(row)

    print(f"wrote {OUT.relative_to(REPO_ROOT)}  ({len(rows)} rows, {len(fieldnames)} columns)")

    # quick summary
    print("\n=== generation tokens summary ===")
    for r in rows:
        tt = r["generation_tokens_total"]
        it = r["generation_iterations"]
        s = r["generation_searches"]
        print(f"  {r['report_id']:14}  type={r['response_type']:3}  "
              f"tokens_total={tt!s:<8}  iters={it!s:<3}  searches={s!s}")


if __name__ == "__main__":
    main()
