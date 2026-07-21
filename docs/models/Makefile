MODELS = gev_hazard prs_pricing storm_intensity flood_risk storm_gauge \
         mortgage_pricer property_valuation timeseries_statistics risk_assessment \
         flood_classifier typhoon fire_resilience seismic_resilience \
         spatial_model insurance_premium delta_engine flood_poly \
         gaugehd_synthetic storm_multi stressm_pipeline property_flood_response \
         bri_resilience bri_floor wind_speed wind_damage

.PHONY: all clean $(MODELS)

all: $(MODELS)

$(MODELS):
	$(MAKE) -C $@

clean:
	@for dir in $(MODELS); do $(MAKE) -C $$dir clean; done
