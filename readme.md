# Ethical Audit of Gemini 2 Flash Lite for HR Ranking Tools
## Overview
This repository contains the full codebase, data, and evaluation pipeline for an experimental audit assessing fairness and intersectional bias in Google’s Gemini 2 Flash Lite when used for résumé ranking in hiring scenarios. By simulating hiring tasks and observing model outputs across controlled variations in candidate social identities, we provide a replicable framework for conducting fairness evaluations of LLM-based HR tools.

## Research Questions
1) Fairness: Do marginalized candidates reach the shortlist less often than their dominant-group peers?
2) Intersectionality: Are disparities amplified when social identity cues intersect?
3) Statistical Robustness: Are group differences significant after accounting for ranking batch variation?

## Main Contributions
1) First audit of Gemini 2 Flash Lite’s résumé ranking behavior using an intersectional lens.
2) Reusable audit protocol to assess fairness in HR contexts.
3) Mitigation strategies: prompt reengineering, human-in-the-loop safeguards, and interpretability recommendations.

## Repository Structure
```bash
ethical-audit-llm-hr-gemini/
│
├── outputs/
│   ├── personas
│   ├── personas_with_resumes/     # 96 synthetic persona files (JSON)
│   ├── prompts/                   # Prompt templates for SWE and HR roles
│   ├── batches/                   # All batch compositions after shuffles
│   ├── runs/                      # API logs and generated model outputs
│   ├── plots/                     
│   └── metrics/
│
│
├── templates/                    # Resume Jinja templates for SWE and HR résumés
│
│                                 # All code modules       
├── generate_personas.py
├── prompt_builder.py                                     
├── resume_generator.py           # Generates synthetic resumes from personas
├── compose_batches.py            # Creates shuffled evaluation batches
├── run_gemini_swe.py             # Prompts Gemini model for SWE role
├── run_gemini_hr.py              # Prompts Gemini model for HR role
├── run_air.py                    # Computes AIR metrics
├── run_selection_rates.py        # Computes SR metrics            
├── run_statistical_tests.py      # Runs Fisher tests (and GEE regression)
│
├── requirements.txt
├── README.md
└── LICENSE
```
## Steps to Reproduce the Audit
1) Clone the repository
bash
```
git clone https://github.com/Joe-Occhipinti/Ethical-Audit-of-LLMs-as-HR-Ranking-Tools-Biases.git
cd ethical-audit-llm-hr-gemini
```
2) Set up a virtual environment and install dependencies
bash
```
python3 -m venv env
source env/bin/activate  # For Windows: .\env\Scripts\activate
pip install -r requirements.txt
```
3) Generate synthetic personas and resumes
bash
```
python generate_personas.py
python resume_generator.py
```
4) Compose randomized batch variants
bash
```
python compose_batches.py
```
5) Run Gemini model prompts (SWE and HR roles)
bash
```
python run_gemini_swe.py
python run_gemini_hr.py
```
6) Compute SR and AIR metrics
bash
```
python run_selection_rates.py
python run_air.py
```
7) Run statistical tests (Fisher + GEE) and plot
bash
```
python run_statistical_tests.py
python run_plots.py
```
## Outputs
1) AIR & SR tables: Adverse impact ratios and selection rates for each protected group.
2) P-value tables: One-sided Fisher exact test with Holm correction.
3) Mixed-effects regression results: GEE models controlling for batch variability.
4) Plots for the above
5) JSON files for: persona metadata, prompt templates, batch compositions, time stamped model runs (prompt + response)

## Citation
If you use this code or audit protocol in your research, please cite: Occhipinti, G. M. (2025). Who Gets to the Top?: Ethical Audit of Gemini 2 Flash Lite for HR Ranking Tools with a Focus on Fairness and Biases. University College Dublin

## License
This project is licensed under the MIT License. See the LICENSE file for details.
