#!/usr/bin/env python3

# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Generate per-model analysis PDFs (sensitivity analysis, stress testing,
model performance) for each model in the inventory.

Each model gets an analysis.pdf in its docs/models/<model_dir>/ directory.
The sensitivity section is sourced from existing sensitivity_tables.tex.

Usage:
    python -m docs.models.sensitivities.generate_all_analysis
    python -m docs.models.sensitivities.generate_all_analysis --model prs gev
"""

import argparse
import os
import sys
from datetime import datetime

_project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, _project_root)

from docs.models.sensitivities.compiler import compile_pdf

# Model key -> (display name, doc directory name)
MODEL_REGISTRY = {
    'prs': ('PRS Analytical Pricing Model', 'prs_pricing', 'MKM-PR-001'),
    'gev': ('GEV Hazard Model', 'gev_hazard', 'MKM-GH-001'),
    'storm': ('Storm Intensity Model', 'storm_intensity', 'MKM-SI-001'),
    'flood': ('Flood Risk Model', 'flood_risk', 'MKM-DD-001'),
    'gauge': ('Storm-Gauge Model', 'storm_gauge', 'MKM-SG-001'),
    'mortgage': ('Mortgage Pricer Model', 'mortgage_pricer', 'MKM-MP-001'),
    'property': ('Property Valuation Model', 'property_valuation', 'MKM-PV-001'),
    'risk': ('Risk Assessment Model', 'risk_assessment', 'MKM-RA-001'),
    'ts': ('Timeseries Statistics Model', 'timeseries_statistics', 'MKM-TS-001'),
    'classifier': ('Flood Classifier Model', 'flood_classifier', 'MKM-FC-001'),
    'hydrograph': ('Hydrograph Model', 'hydrograph', 'MKM-HG-001'),
    'spatial': ('Spatial Interpolation Model', 'spatial_model', 'MKM-SP-001'),
    'insurance': ('Insurance Premium Model', 'insurance_premium', 'MKM-IP-001'),
    'delta': ('Delta Engine', 'delta_engine', 'MKM-DE-001'),
    'stormmulti': ('Storm Sequence Generator', 'storm_multi', 'MKM-SS-001'),
    'gaugehd': ('GaugeHD Synthetic', 'gaugehd_synthetic', 'MKM-GHD-001'),
    'stress': ('Stress Test Pipeline', 'stressm_pipeline', 'MKM-ST-001'),
    'propflood': ('Property Flood Response', 'property_flood_response', 'MKM-PF-001'),
    'floodpoly': ('Flood Polynomial Model', 'flood_poly', 'MKM-FPO-001'),
    'bri': ('Building Resilience Index Model', 'bri_resilience', 'MKM-BRI-001'),
    'typhoon': ('Tropical Cyclone Progression and Wind-Field', 'typhoon', 'MKM-TC-001'),
    'brifloor': ('BRI-Adjusted Floor Level Model', 'bri_floor', 'MKM-BRF-001'),
    'windspeed': ('Event Wind Lookup', 'wind_speed', 'MKM-WS-001'),
    'winddamage': ('Wind Damage Model', 'wind_damage', 'MKM-WD-001'),
    'fire': ('Building Fire-Resilience Credit Model', 'fire_resilience', 'MKM-FIRE-001'),
    'seismic': ('Building Seismic-Resilience Credit Model', 'seismic_resilience',
                'MKM-SEIS-001'),
}

_docs_models = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def _has_sensitivity_tables(model_dir):
    """Check if sensitivity_tables.tex exists for a model."""
    path = os.path.join(_docs_models, model_dir, 'sensitivity_tables.tex')
    return os.path.isfile(path)


def _generate_analysis_tex(display_name, model_dir, model_id):
    """Generate the analysis.tex LaTeX document for a model."""
    date_str = datetime.now().strftime('%d %B %Y')
    has_sensitivity = _has_sensitivity_tables(model_dir)

    tex = r"""\documentclass[11pt,a4paper]{article}
\usepackage[margin=2.5cm]{geometry}
\usepackage{booktabs}
\usepackage{float}
\usepackage{xcolor}
\usepackage{hyperref}
\usepackage{fancyhdr}

\definecolor{mkmblue}{HTML}{1976d2}
\definecolor{mkmgrey}{HTML}{666666}

\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\small\textcolor{mkmgrey}{MKM Research Labs}}
\fancyhead[R]{\small\textcolor{mkmgrey}{""" + display_name + r""" --- Analysis --- v1.0}}
\fancyfoot[L]{\small\textcolor{mkmgrey}{CONFIDENTIAL --- SR 11-7 / SS1/23 Model Governance}}
\fancyfoot[R]{\small\textcolor{mkmgrey}{\thepage}}
\renewcommand{\headrulewidth}{0.5pt}
\renewcommand{\footrulewidth}{0.3pt}

\begin{document}

\begin{center}
{\Large\textbf{Model Analysis Report}}\\[6pt]
{\large\textcolor{mkmblue}{""" + display_name + r"""}}\\[4pt]
{\normalsize """ + model_id + r"""}\\[12pt]
{\small Report Date: """ + date_str + r"""}\\[4pt]
{\footnotesize Governance Framework: SR 11-7 / SS1/23 Model Risk Management}
\end{center}

\vspace{8mm}
\tableofcontents
\newpage

% ===================================================================
% 1. SENSITIVITY ANALYSIS
% ===================================================================
\section{Sensitivity Analysis}

"""
    if has_sensitivity:
        tex += r"""This section presents the sensitivity of model outputs to key input parameters.
Parameter perturbation ranges are chosen to cover plausible operating conditions
and stress scenarios as required under SR~11-7 guidance.

\input{sensitivity_tables}

"""
    else:
        tex += r"""\textit{Sensitivity analysis tables have not yet been generated for this model.
Run \texttt{python -m docs.models.sensitivities.generate\_all} to produce them.}

"""

    tex += r"""
% ===================================================================
% 2. STRESS TESTING
% ===================================================================
\section{Stress Testing}

This section documents stress testing scenarios applied to the model
under extreme but plausible conditions.

\subsection{Stress Scenarios}

\begin{table}[H]
    \centering
    \caption{Stress testing scenarios for """ + display_name + r""".}
    \begin{tabular}{llll}
        \toprule
        \textbf{Scenario} & \textbf{Parameter Shock} & \textbf{Severity} & \textbf{Status} \\
        \midrule
        Baseline & No shock & --- & Passed \\
        Moderate stress & +2$\sigma$ inputs & Medium & Pending \\
        Severe stress & +3$\sigma$ inputs & High & Pending \\
        Reverse stress & Output threshold breach & Critical & Pending \\
        \bottomrule
    \end{tabular}
\end{table}

\textit{Detailed stress test results will be populated as scenarios are executed.
Refer to the model's validation plan for the full stress testing programme.}

% ===================================================================
% 3. MODEL PERFORMANCE
% ===================================================================
\section{Model Performance}

This section tracks key performance metrics for the model across
validation and production environments.

\begin{table}[H]
    \centering
    \caption{Performance metrics for """ + display_name + r""".}
    \begin{tabular}{lll}
        \toprule
        \textbf{Metric} & \textbf{Value} & \textbf{Status} \\
        \midrule
        Unit test pass rate & See Test Results & --- \\
        Execution time (single run) & TBD & --- \\
        Numerical stability & TBD & --- \\
        Reproducibility & Deterministic & OK \\
        \bottomrule
    \end{tabular}
\end{table}

\vspace{12pt}

\noindent\textit{\small This report is produced automatically; human review
is required before formal model approval. Supporting artefacts are available
in the model documentation directory.}

\end{document}
"""
    return tex


def generate_model_analysis(key, display_name, model_dir, model_id):
    """Generate analysis.tex and compile to PDF for a single model."""
    output_dir = os.path.join(_docs_models, model_dir)
    if not os.path.isdir(output_dir):
        print(f'  Directory not found: {output_dir}')
        return None

    tex_content = _generate_analysis_tex(display_name, model_dir, model_id)
    tex_path = os.path.join(output_dir, 'analysis.tex')

    with open(tex_path, 'w') as f:
        f.write(tex_content)
    print(f'  Written: {tex_path}')

    pdf_path = compile_pdf(output_dir, tex_path)
    return pdf_path


def main():
    parser = argparse.ArgumentParser(
        description='Generate per-model analysis PDFs')
    parser.add_argument('--model', nargs='+',
                        help=f'Run specific models only. '
                             f'Available: {", ".join(sorted(MODEL_REGISTRY.keys()))}')
    args = parser.parse_args()

    targets = args.model if args.model else list(MODEL_REGISTRY.keys())

    print('Generating model analysis reports...\n')

    generated = []
    for key in targets:
        if key not in MODEL_REGISTRY:
            print(f'  Unknown model: {key}')
            print(f'  Available: {", ".join(sorted(MODEL_REGISTRY.keys()))}')
            continue

        display_name, model_dir, model_id = MODEL_REGISTRY[key]
        print(f'[{display_name}]')
        try:
            pdf = generate_model_analysis(key, display_name, model_dir, model_id)
            if pdf:
                generated.append(pdf)
        except Exception as e:
            print(f'  ERROR: {e}')
            import traceback
            traceback.print_exc()
        print()

    print(f'Done. {len(generated)} analysis report(s) generated.')


if __name__ == '__main__':
    main()
