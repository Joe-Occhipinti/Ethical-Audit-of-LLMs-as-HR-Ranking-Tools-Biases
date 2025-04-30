#!/usr/bin/env python3
"""
run_pooled_rates.py
-------------------
Compute pooled selection rates for each protected subgroup
and output exactly two CSVs (one per role).

– Finds the newest swe_run_*.jsonl and hr_run_*.jsonl in outputs/runs/
– For each JSONL record:
    • Every candidate’s metadata contributes one appearance to each of
      their protected attributes.
    • If that candidate was selected, one selection is credited likewise.
– For each attribute/value combination, computes:
      selection_rate = total_selections / total_appearances
– Writes:
    • outputs/metrics/swe_subgroup_rates.csv
    • outputs/metrics/hr_subgroup_rates.csv
Each CSV has columns:
    attribute, value, appearances, selections, selection_rate
"""
import json
import csv
from pathlib import Path
from collections import Counter

# 1) Locate latest run‐log files
RUN_DIR     = Path("outputs/runs")
METRICS_DIR = Path("outputs/metrics")
METRICS_DIR.mkdir(parents=True, exist_ok=True)

def latest_log(role: str) -> Path:
    pattern = f"{role}_run_*.jsonl"
    files = sorted(RUN_DIR.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No run logs found for role={role}")
    return files[-1]

swe_log = latest_log("swe")
hr_log  = latest_log("hr")

# 2) Attributes to pool over
ATTRIBUTES = ["gender", "race", "religion", "class", "lgbtq", "marginalized"]

def compute_pooled_counts(log_path: Path):
    """
    Count appearances and selections per attribute/value.
    Returns two dicts: appearances[attr][val], selections[attr][val]
    """
    appearances = {attr: Counter() for attr in ATTRIBUTES}
    selections  = {attr: Counter() for attr in ATTRIBUTES}

    with log_path.open("r", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            sel_set = set(rec.get("selected_persona_ids", []))
            for meta in rec.get("persona_meta", []):
                pid = meta["persona_id"]
                is_sel = (pid in sel_set)
                for attr in ATTRIBUTES:
                    val = meta.get(attr)
                    appearances[attr][val] += 1
                    if is_sel:
                        selections[attr][val] += 1

    return appearances, selections

def write_subgroup_csv(role: str, appearances, selections):
    """
    Write a single CSV for one role, with one row per attribute-value.
    """
    out_file = METRICS_DIR / f"{role}_subgroup_rates.csv"
    with out_file.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["attribute", "value", "appearances", "selections", "selection_rate"])
        for attr in ATTRIBUTES:
            for val, app in sorted(appearances[attr].items(), key=lambda x: (str(x[0]))):
                sel = selections[attr].get(val, 0)
                rate = sel / app if app else 0.0
                writer.writerow([attr, val, app, sel, f"{rate:.4f}"])
    print(f"Wrote {out_file.name}")

def main():
    for role, log in [("swe", swe_log), ("hr", hr_log)]:
        print(f"Processing {role.upper()} log: {log.name}")
        apps, sels = compute_pooled_counts(log)
        write_subgroup_csv(role, apps, sels)
    print("✅ Done. Check outputs/metrics/ for the two CSVs.")

if __name__ == "__main__":
    main()