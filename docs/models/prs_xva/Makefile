TEX = pdflatex -interaction=nonstopmode
SRC = MKM-XV-001_model_document.tex
PDF = $(SRC:.tex=.pdf)

.PHONY: all clean

all: $(PDF)

%.pdf: %.tex ../shared/mkm_header.tex $(wildcard evidence_tables_*.tex)
	$(TEX) $<
	$(TEX) $<

clean:
	rm -f *.aux *.log *.out *.toc *.synctex.gz *.synctex\(busy\)
