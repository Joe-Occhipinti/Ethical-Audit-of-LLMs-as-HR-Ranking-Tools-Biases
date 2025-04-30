"""
compose_batches.py
------------------
Create raw candidate batches (NO prompt text yet).

• 10 base batches of 11 personas
• 4 extra global reshuffles  → 5 shuffles × 10 = 50 distinct batches
• 3 in-batch permutations    → 150 total ‘batch-variants’

Output
------
outputs/batches/batch_variants.json  – list of dicts:
    {
      "variant_id": "sh2_b7_p1",      # shuffle 2, batch-7, permutation-1
      "persona_ids": ["pers_004", … 11 ids …]
    }
"""

import json, random, itertools
from pathlib import Path
from typing import List, Dict

# ------------------------------------------------ paths / constants
HERE            = Path(__file__).resolve().parent
PERSONA_FILE    = HERE / "outputs/all_personas_with_resumes.json"
OUT_DIR         = HERE / "outputs/batches"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE        = OUT_DIR / "batch_variants.json"

NUM_BASE_BATCHES   = 10           # 10 × 11 = 110 personas
BATCH_SIZE         = 11
NUM_SHUFFLES       = 10            # original + 4 reshuffles
INBATCH_PERMS      = 3            # 3 orderings inside each batch
SEED               = 42           # reproducibility ("The answer to life, universe, everything..." :) )

# ------------------------------------------------ load personas
personas: List[Dict] = json.loads(PERSONA_FILE.read_text(encoding="utf-8"))
all_ids = [p["persona_id"] for p in personas]
assert len(all_ids) == 110, "Need exactly 110 personas."

# ------------------------------------------------ compose batches
random.seed(SEED)
variants = []

for sh in range(NUM_SHUFFLES):
    ids = all_ids.copy()
    random.shuffle(ids)                         # global shuffle

    # slice into 10 batches
    batches = [
        ids[i * BATCH_SIZE : (i + 1) * BATCH_SIZE]
        for i in range(NUM_BASE_BATCHES)
    ]

    for b_idx, base in enumerate(batches):
        for perm in range(INBATCH_PERMS):
            permuted = base.copy()
            random.shuffle(permuted)
            variants.append({
                "variant_id": f"sh{sh}_b{b_idx}_p{perm}",
                "persona_ids": permuted
            })

# ------------------------------------------------ save
OUT_FILE.write_text(json.dumps(variants, indent=2), encoding="utf-8")
print(f"✅ Saved {len(variants)} batch-variants → {OUT_FILE}")  # 150 expected