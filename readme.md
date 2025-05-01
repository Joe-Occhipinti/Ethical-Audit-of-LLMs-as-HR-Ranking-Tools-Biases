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
│   ├── personas_with_resumes/        # 96 synthetic persona files (JSON)
│   ├── prompts/                      # Prompt templates for SWE and HR roles
│   ├── batches/                      # All batch compositions and shuffles
│   ├── runs/                         # API logs and generated model outputs
│   └── metrics/                      # AIRs, SRs, p-values, regression results
│
├── templates/                        # Resume Jinja templates for SWE and HR
│
├── src/                              # All code modules
│   ├── resume_generator.py           # Generates synthetic resumes from personas
│   ├── compose_batches.py            # Creates shuffled evaluation batches
│   ├── run_gemini_swe.py             # Prompts Gemini model for SWE role
│   ├── run_gemini_hr.py              # Prompts Gemini model for HR role
│   ├── run_air.py                    # Computes SR and AIR metrics
│   └── run_statistical_tests.py      # Runs Fisher tests and GEE regression
│
├── appendix/                         # Markdown tables and references for paper
├── requirements.txt
├── README.md
└── LICENSE
```
Steps to Reproduce the Audit
Clone the repository

bash
Copia
Modifica
git clone https://github.com/your-username/ethical-audit-llm-hr-gemini.git
cd ethical-audit-llm-hr-gemini
Set up a virtual environment and install dependencies

bash
Copia
Modifica
python3 -m venv env
source env/bin/activate  # For Windows: .\env\Scripts\activate
pip install -r requirements.txt
Generate synthetic personas and resumes

bash
Copia
Modifica
python src/resume_generator.py
Compose randomized batch variants

bash
Copia
Modifica
python src/compose_batches.py
Run Gemini model prompts (SWE and HR roles)

bash
Copia
Modifica
python src/run_gemini_swe.py
python src/run_gemini_hr.py
Compute AIR and SR metrics

bash
Copia
Modifica
python src/run_air.py
Run statistical tests (Fisher + GEE)

bash
Copia
Modifica
python src/run_statistical_tests.py
Outputs
AIR & SR tables: Adverse impact ratios and selection rates for each protected group.

P-value tables: One-sided Fisher exact test with Holm correction.

Mixed-effects regression results: GEE models controlling for batch variability.

Appendices: Metrics, reproducibility instructions, and JSON logs are available in the appendix/.

Citation
If you use this code or audit protocol in your research, please cite:

Occhipinti, G. M. (2025). Who Gets to the Top?: Ethical Audit of Gemini 2 Flash Lite for HR Ranking Tools with a Focus on Fairness and Biases. University of Bologna.

License
This project is licensed under the MIT License. See the LICENSE file for details.
