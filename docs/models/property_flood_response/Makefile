TEX = property_flood_response.tex
PDF = $(TEX:.tex=.pdf)

all: $(PDF)

$(PDF): $(TEX)
	pdflatex -interaction=nonstopmode $(TEX)
	pdflatex -interaction=nonstopmode $(TEX)

clean:
	rm -f *.aux *.log *.out *.toc *.pdf
