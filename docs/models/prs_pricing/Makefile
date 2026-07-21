TEX = pdflatex -interaction=nonstopmode
SRC = $(filter-out sensitivity_tables.tex test_results.tex, $(wildcard *.tex))
PDF = $(SRC:.tex=.pdf)

.PHONY: all clean

all: $(PDF)

%.pdf: %.tex ../shared/mkm_header.tex
	$(TEX) $<
	$(TEX) $<

clean:
	rm -f *.aux *.log *.out *.toc *.synctex.gz *.synctex\(busy\)
