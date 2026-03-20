DOCNAME = storm_multi

all: $(DOCNAME).pdf

$(DOCNAME).pdf: $(DOCNAME).tex
	pdflatex -interaction=nonstopmode $(DOCNAME).tex
	pdflatex -interaction=nonstopmode $(DOCNAME).tex

clean:
	rm -f $(DOCNAME).aux $(DOCNAME).log $(DOCNAME).out $(DOCNAME).toc

distclean: clean
	rm -f $(DOCNAME).pdf

.PHONY: all clean distclean
