TEX = bri_resilience.tex
PDF = $(TEX:.tex=.pdf)

all: $(PDF)

$(PDF): $(TEX) test_results.tex sensitivity_tables.tex
	pdflatex -interaction=nonstopmode $(TEX)
	pdflatex -interaction=nonstopmode $(TEX)

clean:
	rm -f *.aux *.log *.out *.toc

distclean: clean
	rm -f $(PDF)

.PHONY: all clean distclean
