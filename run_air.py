#!/usr/bin/env python3
"""
run_air.py
----------
Compute Adverse Impact Ratio (AIR) and ΔSR for each protected subgroup.

– Reads:
    outputs/metrics/swe_subgroup_rates.csv
    outputs/metrics/hr_subgroup_rates.csv

– For each attribute/value, finds the reference‐group selection_rate,
  then computes:
    • AIR = selection_rate(subgroup) / selection_rate(reference)
    • ΔSR = selection_rate(subgroup) – selection_rate(reference)

– Writes:
    outputs/metrics/swe_subgroup_air.csv
    outputs/metrics/hr_subgroup_air.csv

Each output CSV has columns:
    attribute, value, appearances, selections,
    selection_rate, AIR, delta_SR
"""
import csv
from pathlib import Path

# 1) Configuration: where to find the rate CSVs and what the reference values are
METRICS_DIR = Path("outputs/metrics")
FILES = {
    "swe": METRICS_DIR / "swe_subgroup_rates.csv",
    "hr" : METRICS_DIR / "hr_subgroup_rates.csv",
}
# Define your legally/ethically meaningful reference groups here:
REFERENCE = {
    "gender":      "male",
    "race":        "white",
    "religion":    "christian",
    "class":       "higher",
    "lgbtq":       "no",
    "marginalized":"False",   # note: booleans are strings in the CSV
}

def compute_air(input_path: Path, output_path: Path):
    # 2) Load all rows into memory
    rows = []
    with input_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            # convert numeric fields
            r["appearances"]    = int(r["appearances"])
            r["selections"]     = int(r["selections"])
            r["selection_rate"] = float(r["selection_rate"])
            rows.append(r)

    # 3) Group rows by attribute to extract reference rates
    from collections import defaultdict
    ref_rate = {}
    for r in rows:
        attr, val = r["attribute"], r["value"]
        if attr in REFERENCE and val == REFERENCE[attr]:
            ref_rate[attr] = r["selection_rate"]

    # 4) Now compute AIR and ΔSR, writing out
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "attribute", "value", "appearances", "selections",
            "selection_rate", "AIR", "delta_SR"
        ])
        for r in rows:
            attr = r["attribute"]
            base = ref_rate.get(attr)
            if base is None or base == 0:
                # cannot compute AIR
                air = ""
                delta = ""
            else:
                air   = r["selection_rate"] / base
                delta = r["selection_rate"] - base
            writer.writerow([
                attr,
                r["value"],
                r["appearances"],
                r["selections"],
                f"{r['selection_rate']:.4f}",
                f"{air:.4f}"   if air != ""   else "",
                f"{delta:.4f}" if delta != "" else "",
            ])

def main():
    for role, in_path in FILES.items():
        out_path = METRICS_DIR / f"{role}_subgroup_air.csv"
        print(f"Reading {in_path.name} → writing {out_path.name}")
        compute_air(in_path, out_path)
    print("✅ AIR files generated in outputs/metrics/")

if __name__ == "__main__":
    main()