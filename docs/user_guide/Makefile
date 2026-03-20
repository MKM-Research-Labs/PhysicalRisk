TEX = pdflatex -interaction=nonstopmode
SRC = $(wildcard *.tex)
PDF = $(SRC:.tex=.pdf)

.PHONY: all clean

all: $(PDF)

%.pdf: %.tex ../models/shared/mkm_header.tex
	$(TEX) $<
	$(TEX) $<

clean:
	rm -f *.aux *.log *.out *.toc *.synctex.gz *.synctex\(busy\)
