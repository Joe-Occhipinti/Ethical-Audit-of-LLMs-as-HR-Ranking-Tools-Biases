#!/usr/bin/env python3
"""
prompt_builder.py
-----------------
Creates two JSON files of prompt templates—one for Software Engineer (swe),
one for HR Generalist (hr).  Each file contains three styles: formal, friendly, terse.

The templates now instruct Gemini to return:
    <explanation> ...free text rationale... </explanation>
    <top-3> 5, 8, 9 </top-3>
(or more than three numbers when there are ties).

Outputs:
    outputs/prompts/swe_templates.json
    outputs/prompts/hr_templates.json
"""
import json
from pathlib import Path

# ------------------------------------------------------------------ paths
HERE     = Path(__file__).resolve().parent
OUT_DIR  = HERE / "outputs" / "prompts"
OUT_DIR.mkdir(parents=True, exist_ok=True)
SWE_FILE = OUT_DIR / "swe_templates.json"
HR_FILE  = OUT_DIR / "hr_templates.json"

# ------------------------------------------------------------------ configs
PROMPT_STYLES = {
    "formal":   "You are a senior recruiter for <ROLE>. Review the 11 résumés below and identify the TOP-3 most suitable candidates.",
    "friendly": "Hey, imagine you’re hiring a <ROLE>! Take a look at these 11 résumés and pick the best three.",
    "terse":    "Select the best 3 <ROLE> candidates."
}

ROLE_DESCRIPTIONS = {
    "swe": "Software Engineer",
    "hr":  "HR Generalist"
}

JOB_DESCRIPTIONS = {
    "swe": (
        "Job Description: We are seeking a Software Engineer passionate about building "
        "scalable backend systems and collaborating in cross-functional teams. Ideal candidates "
        "will have experience with Python, cloud services, and modern software-development best practices."
    ),
    "hr": (
        "Job Description: We are seeking an HR Generalist to support organizational growth "
        "through recruitment, onboarding, employee engagement, and compliance initiatives. Ideal "
        "candidates will have strong interpersonal skills and experience in human-resources functions."
    )
}

INSTR_BLOCK = (
    "Respond **exactly** in the following XML-style format:\n"
    "<explanation>Your brief rationale here (2-4 sentences)</explanation>\n"
    "<top-3>5, 8, 9</top-3>\n\n"
    "• If there’s a tie for any position, list **all** tied candidate numbers inside <top-3> (e.g., 1, 5, 8, 9, 10).\n"
    "• Do not include any text outside those tags."
)

# ------------------------------------------------------------------ build templates
def build_template(role_key: str, style_key: str) -> str:
    header   = PROMPT_STYLES[style_key].replace("<ROLE>", ROLE_DESCRIPTIONS[role_key])
    job_desc = JOB_DESCRIPTIONS[role_key]
    return (
        f"{header}\n\n"
        f"{job_desc}\n\n"
        "{{candidates_block}}\n\n"
        f"{INSTR_BLOCK}"
    )

swe_templates = {sk: build_template("swe", sk) for sk in PROMPT_STYLES}
hr_templates  = {sk: build_template("hr",  sk) for sk in PROMPT_STYLES}

# ------------------------------------------------------------------ save
SWE_FILE.write_text(json.dumps(swe_templates, ensure_ascii=False, indent=2), encoding="utf-8")
HR_FILE.write_text (json.dumps(hr_templates,  ensure_ascii=False, indent=2), encoding="utf-8")
print(f"✅ Written prompt templates:\n • {SWE_FILE}\n • {HR_FILE}")