#!/usr/bin/env python3
"""
run_statistical_tests.py
------------------------
1) Reads subgroup‐level counts from CSV (created by run_air.py):
     outputs/metrics/swe_subgroup_air.csv
     outputs/metrics/hr_subgroup_air.csv
   Runs one-sided Fisher tests (minority selected < reference),
   applies Holm adjustment, writes:
     outputs/metrics/swe_air_pvalues.csv
     outputs/metrics/hr_air_pvalues.csv

2) Loads the full flattened run‐logs for swe/hr, fits a population-averaged
   mixed-effects logistic regression via GEE (clustering on batch_idx),
   writes:
     outputs/metrics/swe_gee_results.csv
     outputs/metrics/hr_gee_results.csv
"""

import csv
from pathlib import Path

import pandas as pd
from scipy.stats import fisher_exact
from statsmodels.stats.multitest import multipletests
from statsmodels.genmod.generalized_estimating_equations import GEE
from statsmodels.genmod.families import Binomial
from statsmodels.genmod.cov_struct import Exchangeable

# ------------------------------------------------------------------------------
# 1) Configuration: reference values per attribute
# ------------------------------------------------------------------------------
REFERENCE = {
    "gender":       "male",
    "race":         "white",
    "religion":     "none",   # “none” means no religion
    "class_":       "higher", # note the trailing underscore
    "lgbtq":        "no",
    "marginalized": False
}

# ------------------------------------------------------------------------------
# 2) Fisher + Holm on each role’s subgroup‐AIR CSV
# ------------------------------------------------------------------------------
def process_role_fisher(role: str):
    in_csv  = Path("outputs/metrics") / f"{role}_subgroup_air.csv"
    out_csv = Path("outputs/metrics") / f"{role}_air_pvalues.csv"
    df      = pd.read_csv(in_csv)

    results = []
    for attr, ref_val in REFERENCE.items():
        # skip marginalized here if you want, but we include it
        # subgroup CSV uses column "attribute" so we need to match "class"→"class_"
        col_name = "class" if attr=="class_" else attr
        sub = df[df["attribute"] == col_name]

        # reference row
        ref = sub[sub["value"].astype(str) == str(ref_val)]
        if ref.empty:
            raise ValueError(f"Missing reference {col_name}={ref_val!r} in {in_csv}")
        app_ref = int(ref["appearances"].iloc[0])
        sel_ref = int(ref["selections"].iloc[0])
        uns_ref = app_ref - sel_ref

        for _, row in sub.iterrows():
            val = row["value"]
            if str(val) == str(ref_val):
                continue
            app_min = int(row["appearances"])
            sel_min = int(row["selections"])
            uns_min = app_min - sel_min

            _, p_raw = fisher_exact(
                [[sel_min, uns_min], [sel_ref, uns_ref]],
                alternative="less"
            )
            results.append({
                "attribute": col_name,
                "value":     val,
                "p_raw":     p_raw
            })

    # Holm adjustment
    pvals = [r["p_raw"] for r in results]
    _, p_holm, _, _ = multipletests(pvals, method="holm")

    # write out
    with open(out_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["attribute", "value", "p_raw", "p_holm"])
        for r, ph in zip(results, p_holm):
            writer.writerow([
                r["attribute"],
                r["value"],
                f"{r['p_raw']:.6f}",
                f"{ph:.6f}"
            ])
    print(f"→ Fisher + Holm for {role} → {out_csv}")

# ------------------------------------------------------------------------------
# 3) Flattened logs → one row per persona per scenario
# ------------------------------------------------------------------------------
def load_flattened_runs(role: str) -> pd.DataFrame:
    import json
    files = sorted(Path("outputs/runs").glob(f"{role}_run_*.jsonl"))
    if not files:
        raise FileNotFoundError(f"No logs matching {role}_run_*.jsonl")
    path = files[-1]

    rows = []
    for line in path.open("r", encoding="utf-8"):
        rec     = json.loads(line)
        sel_set = set(rec["selected_persona_ids"])
        # extract batch index
        try:
            tok       = next(t for t in rec["scenario_id"].split("_") if t.startswith("b"))
            batch_idx = int(tok[1:])
        except StopIteration:
            batch_idx = -1

        for m in rec["persona_meta"]:
            rows.append({
                "batch_idx":    batch_idx,
                "selected":     int(m["persona_id"] in sel_set),
                "gender":       m.get("gender",  "none") or "none",
                "race":         m.get("race",    "none") or "none",
                "religion":     m.get("religion","none") or "none",
                # FIXED: emit class_ not class
                "class_":       m.get("class",   "none") or "none",
                "lgbtq":        m.get("lgbtq",   "none") or "none",
                "marginalized": bool(m.get("marginalized", False))
            })
    return pd.DataFrame(rows)

# ------------------------------------------------------------------------------
# 4) Mixed‐effects logistic regression (GEE)
# ------------------------------------------------------------------------------
def process_role_gee(role: str):
    df = load_flattened_runs(role)
    formula = (
        "selected ~ "
        "C(gender) + C(race) + C(religion) + C(class_) + C(lgbtq) + marginalized"
    )

    model = GEE.from_formula(
        formula,
        groups="batch_idx",
        data=df,
        family=Binomial(),
        cov_struct=Exchangeable()
    )
    res = model.fit()

    out = pd.DataFrame({
        "term":     res.params.index,
        "coef":     res.params.values,
        "std_err":  res.bse.values,
        "p_value":  res.pvalues.values
    })
    out_path = Path("outputs/metrics") / f"{role}_gee_results.csv"
    out.to_csv(out_path, index=False)
    print(f"→ GEE results for {role} → {out_path}")

# ------------------------------------------------------------------------------
# 5) Run both steps for swe & hr
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    for r in ("swe", "hr"):
        process_role_fisher(r)
    for r in ("swe", "hr"):
        process_role_gee(r)
    print("✅ All statistical tests complete.")