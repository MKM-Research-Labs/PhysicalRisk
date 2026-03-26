DOC = hydrograph_sensitivity

.PHONY: all clean tables

all: tables $(DOC).pdf

tables:
	cd ../../.. && PYTHONPATH=src:. python -c \
		"from docs.models.sensitivities.hydrograph.generator import generate; generate()"

$(DOC).pdf: $(DOC).tex sensitivity_tables.tex ../shared/mkm_header.tex
	pdflatex -interaction=nonstopmode $(DOC).tex
	pdflatex -interaction=nonstopmode $(DOC).tex

clean:
	rm -f *.aux *.log *.out *.toc *.pdf
