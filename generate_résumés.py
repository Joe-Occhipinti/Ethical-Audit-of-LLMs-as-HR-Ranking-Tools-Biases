#!/usr/bin/env python3
"""
resume_generator.py
-------------------
Generates role-specific résumés for every persona.

Adds two new fields to each persona JSON:
    • resume_swe   (Software-Engineer résumé)
    • resume_hr    (HR-Generalist résumé)

Names depend ONLY on race and gender.
Each résumé gets exactly two social-related extracurricular activities:
  - For both religion and LGBTQIA+ personas: one faith-based + one LGBTQIA+ activity.
  - For only one of those cues: one cue-specific + one neutral activity.
  - For neither cue: two neutral activities.
Anonymous personas  also get a full résumé, but with:
  • placeholder “Anonymous Candidate” name
  • generic email and phone
  • a generic university
  • two neutral extracurricular activities
"""

import json
import random
from pathlib import Path
from typing import Dict, List
from jinja2 import Environment, FileSystemLoader

# ------------------------------------------------------------------ paths
HERE             = Path(__file__).resolve().parent
ALL_PERSONAS_IN  = HERE / "outputs/all_personas.json"
ALL_PERSONAS_OUT = HERE / "outputs/all_personas_with_resumes.json"
PER_DIR          = HERE / "outputs/personas_with_resumes"
TEMPLATE_DIR     = HERE / "templates"
PER_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------ load personas
personas: List[Dict] = json.loads(ALL_PERSONAS_IN.read_text(encoding="utf-8"))

# ------------------------------------------------------------------ name pools
first_names = {
    "white": {
        "male":   ["John","Robert","William","James","Charles","Matthew","Thomas","Daniel"],
        "female": ["Emily","Jessica","Amanda","Ashley","Brittany","Lauren","Megan","Rachel"]
    },
    "black": {
        "male":   ["Jamal","Malik","DeShawn","Kareem","Kwame","Omari","Tyrese","Lamar"],
        "female": ["Aaliyah","Tanisha","Imani","Shanice","Ebony","Latoya","Tanesha","Destiny"]
    },
    "asian": {
        "male":   ["Wei","Hiroshi","Min-Jun","Jae-Hyun","Tao","Takeshi","Daisuke","Kenji"],
        "female": ["Mei","Yuna","Sakura","Min-Ji","Yui","Soojin","Xiulan","Haruka"]
    },
    "hispanic": {
        "male":   ["José Luis","Juan","Carlos","Fernando","Alejandro","Miguel Ángel","Diego","Javier"],
        "female": ["María José","Carmen","Guadalupe","Ana María","Gabriela","Catalina","Alejandra","Dolores"]
    }
}

last_names = {
    "white":    ["Smith","Brown","Taylor","Anderson","Johnson","Davis","Miller","Wilson"],
    "black":    ["Jackson","Washington","Freeman","Jefferson","King","Armstrong","Robinson","Walker"],
    "asian":    ["Chen","Wong","Kim","Tanaka","Nakamura","Huang","Liu","Zhang"],
    "hispanic": ["Gonzalez","Ramirez","Martinez","Hernandez","Rivera","Cruz","Morales","Torres"]
}

elite_schools   = ["Harvard University","MIT","Stanford University","Yale University"]
regular_schools = [
    "University of Louisiana at Monroe",
    "University of Texas Rio Grande Valley",
    "Arkansas State University",
    "Wichita State University"
]

# ------------------------------------------------------------------ activity pools
religious_acts = {
    "christian": "Helped stock the church food-bank on weekends.",
    "muslim":    "Helped set up chairs for mosque community events."
}
lgbtq_act          = "Helped staff the local LGBTQ+ community-center info desk."
neutral_activities = [
    "Helped at local animal shelter.",
    "Helped organize community library reading sessions."
]

# ------------------------------------------------------------------ helpers
used_names: set = set()
def unique_name(race: str, gender: str) -> str:
    fn_pool = first_names[race][gender]
    ln_pool = last_names[race]
    for _ in range(200):
        full = f"{random.choice(fn_pool)} {random.choice(ln_pool)}"
        if full not in used_names:
            used_names.add(full)
            return full
    # fallback: add middle initial
    import string
    first, last = random.choice(fn_pool), random.choice(ln_pool)
    for c in string.ascii_uppercase:
        full = f"{first} {c}. {last}"
        if full not in used_names:
            used_names.add(full)
            return full
    raise RuntimeError(f"Name pool exhausted for {race}/{gender}")

def edu_block(p: Dict) -> str:
    """Pick a real school for non-anonymous personas."""
    school = random.choice(elite_schools if p.get("class") == "higher" else regular_schools)
    return f"- {school}, B.Sc. (2020-2024)"

def activities_block(p: Dict) -> str:
    """Exactly two activities, mixing cue-based and neutral as needed."""
    acts: List[str] = []
    if p.get("religion") in religious_acts:
        acts.append(religious_acts[p["religion"]])
    if p.get("lgbtq") == "yes":
        acts.append(lgbtq_act)
    if len(acts) == 0:
        # no cues → two neutrals
        acts = neutral_activities.copy()
    elif len(acts) == 1:
        # one cue → add one neutral
        acts.append(neutral_activities[0])
    # if len(acts)==2, both are cue-based
    return "\n".join(f"- {a}" for a in acts)

def email_from(name: str) -> str:
    return name.lower().replace(" ", ".") + "@example.com"

# ------------------------------------------------------------------ load résumé templates
env  = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=False)
TEMPL = {
    "swe": env.get_template("software_engineer.j2"),
    "hr":  env.get_template("hr_generalist.j2")
}

# ------------------------------------------------------------------ build résumés
for p in personas:
    # for completely anonymous personas:
    if p.get("gender") is None:
        ctx = {
            "full_name":        "",
            "email":            "contact@email.com",
            "phone":            "555-0000",
            "education_block":  "- University, B.Sc. (2020-2024)",
            "activities_block": "\n".join(f"- {a}" for a in neutral_activities)
        }
    else:
        # generate real-looking name & email
        name = unique_name(p["race"], p["gender"])
        ctx  = {
            "full_name":        name,
            "email":            email_from(name),
            "phone":            "555-0101",
            "education_block":  edu_block(p),
            "activities_block": activities_block(p)
        }

    # render both SWE and HR templates
    p["resume_swe"] = TEMPL["swe"].render(**ctx)
    p["resume_hr"]  = TEMPL["hr"].render(**ctx)

    # write individual persona file
    (PER_DIR / f"{p['persona_id']}.json").write_text(
        json.dumps(p, indent=2), encoding="utf-8"
    )

# save combined file
ALL_PERSONAS_OUT.write_text(
    json.dumps(personas, indent=2), encoding="utf-8"
)
print(f"Résumés generated for {len(personas)} personas → {PER_DIR}")