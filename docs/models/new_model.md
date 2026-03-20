# New Model Checklist

This document provides the complete checklist for introducing a new analytical
model into the MKM Physical Risk platform. Each step must be completed and
evidenced before the model can be presented to the MRC for production approval.

---

## 1. Model Registration

Add an entry to `data/model_inventory.json` with:

- `model_id` — Unique identifier (format: `MKM-XX-NNN`)
- `name` — Human-readable model name
- `tier` — Governance tier (1=Maximum, 2=Substantial, 3=Moderate, 4=Minimal)
- `source_module` — Path to primary source file (e.g. `src/models/hazard/gev.py`)
- `assumptions` — Key modelling assumptions
- `limitations` — Known limitations
- `key_parameters` — List of principal input parameters
- `rag_status` — Initial RAG rating (typically `Amber` for new models)
- `owner` — Model owner name
- `last_review_date` — Date of initial review
- `next_review_date` — Scheduled recertification date

---

## 2. LaTeX Documentation

Create `docs/models/<model_name>/<model_name>.tex` with:

```latex
\documentclass[11pt]{article}
\newcommand{\doctitle}{<Model Name>}
\newcommand{\docsubtitle}{Model Documentation}
\newcommand{\docversion}{1.0}
\newcommand{\docdate}{<date>}
\newcommand{\docauthor}{<author>}
\input{../shared/mkm_header}

\begin{document}
\mkmtitlepage
\mkmlegalpage
\tableofcontents
\clearpage

% Sections: Purpose, Methodology, Parameters, Implementation,
%           Validation, Limitations, Change History

\end{document}
```

Required sections:

- Purpose and scope
- Mathematical framework and methodology
- Input parameters and calibration
- Implementation details and source code references
- Validation and backtesting results (include `\input{test_results}`)
- Sensitivity analysis (include `\input{sensitivity_tables}`)
- Known limitations and assumptions
- Change history

---

## 3. Makefile

Create `docs/models/<model_name>/Makefile`:

```makefile
TEX = <model_name>.tex
PDF = $(TEX:.tex=.pdf)

all: $(PDF)

$(PDF): $(TEX)
	pdflatex -interaction=nonstopmode $(TEX)
	pdflatex -interaction=nonstopmode $(TEX)

clean:
	rm -f *.aux *.log *.out *.toc *.pdf
```

Update the root `docs/models/Makefile` to add `<model_name>` to the `MODELS` list.

---

## 4. Test Mapping

Add entries to `docs/models/test_results/generator/models.py`:

- `TEST_MODEL_MAP`: Map test file paths to the model ID
- `MODEL_INFO`: Add model name and doc directory
- `MODEL_ALIASES`: Add short alias for `--model` flag

---

## 5. Parameter Inventory

Add a parameter section to `docs/models/parameter_inventory/generator/parameters.py`
in the `get_parameter_sections()` return list, documenting all hard-coded
parameters with:

- Parameter name
- Current value
- Description
- Source file and line number

---

## 6. Sensitivity Analysis

Create `docs/models/sensitivities/<model_name>/generator/__init__.py` with a
`generate()` function that:

1. Imports the model
2. Varies key input parameters
3. Produces LaTeX tables via `latex_table()` and `write_tables()`

Register in `docs/models/sensitivities/generate_all.py` by adding an entry
to the `GENERATORS` dict.

---

## 7. Test Results

Run the test results generator to produce the per-model `test_results.tex`
fragment:

```bash
python -m docs.models.test_results.generator --model <ALIAS>
```

This writes `test_results.tex` to the model's doc directory for inclusion
in the main LaTeX document.

---

## 8. MRC Review

Present the model to the MRC at the next quarterly meeting:

- Provide completed model documentation PDF
- Present test results and sensitivity analysis
- Propose tier classification with justification
- Request production approval (with or without conditions)
- MRC assigns RAG rating and sets recertification date

---

## 9. BCBS 239 Compliance

Confirm the model meets BCBS 239 data aggregation and reporting principles:

- Data inputs are traceable and auditable
- Model outputs are included in risk reporting
- Documentation meets governance standards
- Update `data/bcbs239_assessment.json` if principles are affected
