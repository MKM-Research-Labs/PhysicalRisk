MODELS = gev_hazard prs_pricing storm_intensity flood_risk storm_gauge \
         mortgage_pricer property_valuation timeseries_statistics risk_assessment \
         flood_classifier

.PHONY: all clean $(MODELS)

all: $(MODELS)

$(MODELS):
	$(MAKE) -C $@

clean:
	@for dir in $(MODELS); do $(MAKE) -C $$dir clean; done
