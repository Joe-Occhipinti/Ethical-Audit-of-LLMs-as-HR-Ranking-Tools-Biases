#!/usr/bin/env python3
"""
run_gemini_swe.py
-----------------
• Builds Software-Engineer prompts
• Splits the load across TWO Google-GenAI API keys
    – first 450 prompts → KEY_1
    – next  450 prompts → KEY_2
    – repeat for every additional 900-prompt block
• Uses <explanation>/<top-3> tags to parse the answer
• Retries with exponential back-off, throttles to ≈ 30 req/min
• Check-points after every prompt so you can stop / resume
• Logs one JSONL line per prompt to outputs/runs/
"""

import os, json, re, time, logging
from pathlib import Path
from typing import List
from datetime import datetime, timezone
from dotenv import load_dotenv

# ── 1) Load .env & API-keys ────────────────────────────────────────────────
HERE   = Path(__file__).resolve().parent
DOTENV = HERE / ".env"
if not DOTENV.exists():
    raise RuntimeError("❌  .env missing – put your API keys there.")
load_dotenv(DOTENV, override=True)

KEY_LIST: list[str] = [
    k.strip() for k in os.getenv("GOOGLE_API_KEYS", "").split(",") if k.strip()
]
if len(KEY_LIST) < 2:
    raise RuntimeError("Need at least two keys in GOOGLE_API_KEYS")

import google.generativeai as genai
from google.generativeai import types

# ── 2) Constants & paths ──────────────────────────────────────────────────
MODEL_NAME      = "gemini-2.0-flash-lite"
MAX_RETRIES     = 3
BACKOFF_BASE    = 1.5      # seconds
DELAY_SECONDS   = 2.1      # ~30 req/minute
PROMPTS_PER_KEY = 450      # free quota per key
DRY_RUN_LIMIT   = 1        # set False for full run

VARIANT_FILE   = HERE / "outputs/batches/batch_variants.json"
PERSONA_FILE   = HERE / "outputs/all_personas_with_resumes.json"
TEMPLATE_FILE  = HERE / "outputs/prompts/swe_templates.json"
RUN_DIR        = HERE / "outputs/runs";  RUN_DIR.mkdir(parents=True, exist_ok=True)

ts      = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
RUN_LOG = RUN_DIR / f"swe_run_{ts}.jsonl"
CP_FILE = RUN_DIR / ".last_checkpoint_swe.json"

variants  = json.loads(VARIANT_FILE.read_text(encoding="utf-8"))
personas  = json.loads(PERSONA_FILE.read_text(encoding="utf-8"))
templates = json.loads(TEMPLATE_FILE.read_text(encoding="utf-8"))
id2p      = {p["persona_id"]: p for p in personas}
style_items = list(templates.items())

# ── 3) Helpers ────────────────────────────────────────────────────────────
EXPL_RE = re.compile(r"<explanation>(.*?)</explanation>.*?<top-3>(.*?)</top-3>", re.S|re.I)
def split_response(txt: str):
    m = EXPL_RE.search(txt)
    return ("", txt) if not m else (m.group(1).strip(), m.group(2).strip())

def parse_selection(sel_line: str, pids: List[str]) -> List[str]:
    nums = re.findall(r"\d+", sel_line)
    chosen = []
    for n in nums:
        idx = int(n) - 1
        if 0 <= idx < len(pids):
            pid = pids[idx]
            if pid not in chosen:
                chosen.append(pid)
    return chosen

def pick_api_key(global_idx: int) -> str:
    block = (global_idx - 1) // PROMPTS_PER_KEY
    return KEY_LIST[block % len(KEY_LIST)]

def call_gemini(prompt: str, api_key: str) -> str:
    genai.configure(api_key=api_key)
    cfg = types.GenerationConfig(temperature=0.0, max_output_tokens=8000)
    for attempt in range(1, MAX_RETRIES+1):
        try:
            text = genai.GenerativeModel(MODEL_NAME)\
                      .generate_content(prompt, generation_config=cfg)\
                      .text.strip()
            if not re.search(r"\d", text):
                raise ValueError("No digit found – parse error")
            return text
        except Exception as e:
            logging.warning(f"[retry {attempt}/{MAX_RETRIES}] {e}")
            if attempt < MAX_RETRIES:
                time.sleep(BACKOFF_BASE ** attempt)
    return ""  # give up here

def load_checkpoint() -> int:
    return json.loads(CP_FILE.read_text()).get("done", 0) if CP_FILE.exists() else 0

def save_checkpoint(n: int):
    CP_FILE.write_text(json.dumps({"done": n}), encoding="utf-8")

# ── 4) Main ────────────────────────────────────────────────────────────────
def main(dry_run: bool = True):
    total = len(variants) * len(style_items)
    done  = load_checkpoint()

    with RUN_LOG.open("a", encoding="utf-8") as fout:
        for vi, var in enumerate(variants, 1):
            if dry_run and vi > DRY_RUN_LIMIT:
                break

            resumes = [id2p[pid]["resume_swe"] for pid in var["persona_ids"]]
            block   = ("\n" + "-"*80 + "\n").join(
                          f"### Candidate {i+1}\n{txt}"
                          for i, txt in enumerate(resumes)
                      )

            for si, (style_key, tmpl) in enumerate(style_items, 1):
                idx_global  = (vi - 1)*len(style_items) + si
                if idx_global <= done:
                    continue

                prompt    = tmpl.replace("{{candidates_block}}", block)
                scenario  = f"{var['variant_id']}_{style_key}_swe"
                api_key   = pick_api_key(idx_global)
                resp      = call_gemini(prompt, api_key)
                rat, selb = split_response(resp)
                sel_ids   = parse_selection(selb, var["persona_ids"])

                meta = [
                    {k: p.get(k) for k in
                     ("persona_id","gender","race","religion","class","lgbtq","marginalized")}
                    for p in (id2p[pid] for pid in var["persona_ids"])
                ]
                rec = {
                    "scenario_id":          scenario,
                    "role":                 "swe",
                    "prompt_style":         style_key,
                    "persona_ids":          var["persona_ids"],
                    "persona_meta":         meta,
                    "prompt_text":          prompt,
                    "response_text":        resp,
                    "rationale_text":       rat,
                    "selection_line":       selb,
                    "selected_persona_ids": sel_ids,
                    "timestamp_utc":        datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                }
                fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
                fout.flush()

                done = idx_global
                save_checkpoint(done)

                status = f"selected {sel_ids}" if resp else "SKIPPED"
                print(f"[{done}/{total}] {scenario} → {status} (key#{KEY_LIST.index(api_key)+1})")
                time.sleep(DELAY_SECONDS)

    logging.info(f"✅ SWE run complete: {done}/{total} → {RUN_LOG}")
    if done >= total and CP_FILE.exists():
        CP_FILE.unlink()

if __name__ == "__main__":
    main(dry_run=False)