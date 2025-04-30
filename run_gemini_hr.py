#!/usr/bin/env python3
"""
run_gemini_hr.py
-----------------
Same dual-API-key, round-robin pattern for HR-Generalist ranking.
"""

import os, json, re, time, logging
from pathlib import Path
from typing import List
from datetime import datetime, timezone
from dotenv import load_dotenv

# ── 1) Load .env & keys ───────────────────────────────────────────────────
HERE   = Path(__file__).resolve().parent
load_dotenv(HERE / ".env", override=True)

KEY_LIST: list[str] = [
    k.strip() for k in os.getenv("GOOGLE_API_KEYS", "").split(",") if k.strip()
]
if len(KEY_LIST) < 2:
    raise RuntimeError("Need at least two keys in GOOGLE_API_KEYS")

import google.generativeai as genai
from google.generativeai import types

# ── 2) Constants & files ──────────────────────────────────────────────────
MODEL_NAME      = "gemini-2.0-flash-lite"
MAX_RETRIES     = 3
BACKOFF_BASE    = 1.5
DELAY_SECONDS   = 2.1
PROMPTS_PER_KEY = 450
DRY_RUN_LIMIT   = 5

ROLE_TAG        = "hr"

VARIANT_FILE   = HERE / "outputs/batches/batch_variants.json"
PERSONA_FILE   = HERE / "outputs/all_personas_with_resumes.json"
TEMPLATE_FILE  = HERE / "outputs/prompts/hr_templates.json"
RUN_DIR        = HERE / "outputs/runs"; RUN_DIR.mkdir(exist_ok=True)

ts       = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
RUN_LOG  = RUN_DIR / f"{ROLE_TAG}_run_{ts}.jsonl"
CP_FILE  = RUN_DIR / f".last_checkpoint_{ROLE_TAG}.json"

variants  = json.loads(VARIANT_FILE.read_text())
personas  = json.loads(PERSONA_FILE.read_text())
templates = json.loads(TEMPLATE_FILE.read_text())
id2p      = {p["persona_id"]: p for p in personas}
style_items = list(templates.items())

# ── 3) Helpers ────────────────────────────────────────────────────────────
TAG_RE = re.compile(r"<explanation>.*?</explanation>.*?<top-3>.*?\d", re.S|re.I)
def parse_selection(line:str, pids:List[str]) -> List[str]:
    nums, sel = re.findall(r"\d+", line), []
    for n in nums:
        i = int(n)-1
        if 0 <= i < len(pids) and pids[i] not in sel:
            sel.append(pids[i])
    return sel

def pick_api_key(idx:int) -> str:
    block = (idx - 1)//PROMPTS_PER_KEY
    return KEY_LIST[block % len(KEY_LIST)]

def call_model(prompt:str, api_key:str) -> str:
    genai.configure(api_key=api_key)
    cfg = types.GenerationConfig(temperature=0.0, max_output_tokens=8000)
    for attempt in range(1, MAX_RETRIES+1):
        try:
            txt = genai.GenerativeModel(MODEL_NAME)\
                      .generate_content(prompt, generation_config=cfg)\
                      .text.strip()
            if not TAG_RE.search(txt):
                raise ValueError("Missing tags or digits")
            return txt
        except Exception as e:
            logging.warning(f"[retry {attempt}/{MAX_RETRIES}] {e}")
            if attempt < MAX_RETRIES:
                time.sleep(BACKOFF_BASE**attempt)
    return ""

def load_checkpoint() -> int:
    return json.loads(CP_FILE.read_text()).get("done",0) if CP_FILE.exists() else 0

def save_checkpoint(n:int):
    CP_FILE.write_text(json.dumps({"done":n}), encoding="utf-8")

# ── 4) Main ────────────────────────────────────────────────────────────────
def main(dry_run: bool = False):
    total = len(variants)*len(style_items)
    done  = load_checkpoint()

    with RUN_LOG.open("a", encoding="utf-8") as out_f:
        for vi, var in enumerate(variants, 1):
            if dry_run and vi > DRY_RUN_LIMIT:
                break

            block = ("\n"+"-"*80+"\n").join(
                f"### Candidate {i+1}\n{id2p[p]['resume_hr']}"
                for i,p in enumerate(var["persona_ids"])
            )

            for si, (style_key, tpl) in enumerate(style_items, 1):
                idx_global = (vi-1)*len(style_items) + si
                if idx_global <= done:
                    continue

                prompt   = tpl.replace("{{candidates_block}}", block)\
                           + "\n\nPlease add a brief rationale."
                scenario = f"{var['variant_id']}_{style_key}_{ROLE_TAG}"
                api_key  = pick_api_key(idx_global)
                resp     = call_model(prompt, api_key)

                rat, selb = ("","")
                sel_ids   = []
                if resp:
                    m = re.search(r"<explanation>(.*?)</explanation>.*?<top-3>(.*?)</top-3>",
                                  resp, re.S|re.I)
                    rat, selb = (m.group(1).strip(), m.group(2).strip()) if m else ("",resp)
                    sel_ids   = parse_selection(selb, var["persona_ids"])

                meta = [
                    {k: p.get(k) for k in
                     ("persona_id","gender","race","religion","class","lgbtq","marginalized")}
                    for p in (id2p[x] for x in var["persona_ids"])
                ]
                rec = {
                    "scenario_id":          scenario,
                    "role":                 ROLE_TAG,
                    "prompt_style":         style_key,
                    "persona_ids":          var["persona_ids"],
                    "persona_meta":         meta,
                    "prompt_text":          prompt,
                    "response_text":        resp,
                    "rationale_text":       rat,
                    "selection_line":       selb,
                    "selected_persona_ids": sel_ids,
                    "timestamp_utc":        datetime.now(timezone.utc)
                                            .strftime("%Y-%m-%dT%H:%M:%SZ")
                }
                out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                out_f.flush()

                done = idx_global
                save_checkpoint(done)

                status = f"selected {sel_ids}" if resp else "SKIPPED"
                print(f"[{done}/{total}] {scenario} → {status} (key#{KEY_LIST.index(api_key)+1})")
                time.sleep(DELAY_SECONDS)

    logging.info(f"✅ HR run complete: {done}/{total} → {RUN_LOG}")
    if done >= total and CP_FILE.exists():
        CP_FILE.unlink()

if __name__ == "__main__":
    main(dry_run=False)