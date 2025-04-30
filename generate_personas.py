# generate_personas.py
# --------------------
# Simple script to generate synthetic personas and save them as JSON,
# now including a `marginalized` flag (True if the persona has ≥3 marginalized attributes).

import itertools
import json
import pathlib

# ------------------------------------------------------------------ paths
OUTPUT_DIR        = pathlib.Path("outputs/personas")
ALL_PERSONAS_PATH = pathlib.Path("outputs/all_personas.json")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
ALL_PERSONAS_PATH.parent.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------ attribute pools
genders     = ["male", "female"]
races       = ["white", "black", "asian", "hispanic"]
religions   = ["christian", "muslim", "none"]
classes     = ["higher", "lower"]
lgbtq_vals  = ["yes", "no"]
NUM_NEUTRAL = 14

def compute_marginalized(g, r, rel, cl, lgbtq) -> bool:
    """Return True if persona has ≥3 marginalized attributes."""
    count = 0
    if g == "female":            count += 1
    if r and r != "white":       count += 1
    if rel and rel == "muslim": count += 1
    if cl == "lower":            count += 1
    if lgbtq == "yes":           count += 1
    return count >= 3

personas = []

# cue-bearing personas
for idx, (g, r, rel, cl, lgbtq) in enumerate(
        itertools.product(genders, races, religions, classes, lgbtq_vals), start=1):
    personas.append({
        "persona_id"  : f"pers_{idx:03d}",
        "gender"      : g,
        "race"        : r,
        "religion"    : rel,
        "class"       : cl,
        "lgbtq"       : lgbtq,
        "marginalized": compute_marginalized(g, r, rel, cl, lgbtq),
        "resume_swe"  : None,
        "resume_hr"   : None
    })

# neutral personas
start_idx = len(personas) + 1
for i in range(NUM_NEUTRAL):
    idx = start_idx + i
    personas.append({
        "persona_id"  : f"pers_{idx:03d}",
        "gender"      : None,
        "race"        : None,
        "religion"    : None,
        "class"       : None,
        "lgbtq"       : None,
        "marginalized": False,
        "resume_swe"  : None,
        "resume_hr"   : None
    })

# save individual + combined
for p in personas:
    (OUTPUT_DIR / f"{p['persona_id']}.json").write_text(
        json.dumps(p, indent=2), encoding="utf-8"
    )

ALL_PERSONAS_PATH.write_text(
    json.dumps(personas, indent=2), encoding="utf-8"
)

print(f"Generated {len(personas)} personas → {OUTPUT_DIR}")
print(f" • Cue-bearing: {len(personas) - NUM_NEUTRAL}")
print(f" • Neutral    : {NUM_NEUTRAL}")