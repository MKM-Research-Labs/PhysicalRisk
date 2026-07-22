TEX    = pdflatex -interaction=nonstopmode
SHARED = ../models/shared
SRC    = $(wildcard *.tex)
PDF    = $(SRC:.tex=.pdf)
BUILD  = .build

.PHONY: all clean

all: $(PDF)

# This directory is outside docs/models/, so the shared header's own relative
# reference to ../shared/Logos/ does not resolve from here.  Build inside
# $(BUILD)/doc/ with $(BUILD)/shared symlinked to the real shared directory,
# which reproduces the layout the header expects, then copy the PDF back.
%.pdf: %.tex $(SHARED)/mkm_header.tex
	@mkdir -p $(BUILD)/doc
	@rm -f $(BUILD)/shared
	@ln -s $(abspath $(SHARED)) $(BUILD)/shared
	@cp $< $(BUILD)/doc/
	cd $(BUILD)/doc && $(TEX) $< && $(TEX) $< && $(TEX) $<
	@cp $(BUILD)/doc/$@ .

clean:
	rm -rf $(BUILD)
