TEX = pdflatex -interaction=nonstopmode
SRC = topology.tex
PDF = topology.pdf

.PHONY: all clean

all: $(PDF)

$(PDF): $(SRC) ../shared/mkm_header.tex
	$(TEX) $(SRC)
	$(TEX) $(SRC)

clean:
	rm -f *.aux *.log *.out *.toc *.synctex.gz *.synctex\(busy\)
