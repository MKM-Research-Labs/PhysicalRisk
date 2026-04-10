# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Control tab — data loading, saving, and reset logic."""


def get_js() -> str:
    """Return JavaScript for loadControlData / saveControlData / resetControlData."""
    return r"""
            // ---- Section field definitions (with help tooltips) ----
            var _ctrlFields = {
                storm_generation: [
                    {type:'scalar', label:'Event Window (hours)',           key:'event_window_hours',
                     help:'Total duration of the analysis window for multi-storm sequences. All storm pulses and drainage tails must fit within this window. Default 168 hours (7 days).'},
                    {type:'scalar', label:'Min Drainage Window (hours)',    key:'min_drainage_window_hours',
                     help:'Minimum drainage tail required after the last precipitation event ends. Ensures the hydrograph has time to recede before the window closes.'},
                    {type:'scalar', label:'Intensity Variation (\u00b1)',   key:'intensity_variation',          step:'0.01',
                     help:'Fractional variation applied around the base intensity for each storm pulse. A value of 0.20 means each pulse intensity varies by up to \u00b120% from the category mean.'},
                    {type:'scalar', label:'First Storm Dominant Prob',      key:'first_storm_dominant_prob',     step:'0.01',
                     help:'Probability that the first storm in a sequence is the strongest. Lower values allow later storms to dominate, producing compound flooding patterns.'},
                    {type:'scalar', label:'Correlation Prob',              key:'correlation_prob',              step:'0.01',
                     help:'Probability that subsequent storms in a sequence maintain or increase intensity relative to the first. Controls whether sequences escalate or decay.'},
                    {type:'array',  label:'Default Type Weights [D,C,P]',  key:'default_type_weights',
                     help:'Default weights for [doublet, cluster, persistent] sequence types used for minimal/baseline intensity categories. Higher-intensity categories use their own weights.'},
                    {type:'dict',   label:'Sequence Probability',          key:'sequence_probability',
                     help:'Probability that a storm of each intensity category forms a multi-storm sequence rather than remaining isolated. Higher intensities are more likely to cluster.'},
                    {type:'dict',   label:'Intensity Weights (Batch)',     key:'default_intensity_weights',
                     help:'Distribution of storm intensities across the 20,000-sequence batch. Controls the proportion of moderate, severe, extreme, and catastrophic storms generated.'},
                    {type:'dict',   label:'Catchment Base Precip (mm)',    key:'catchment_base_precip',
                     help:'Baseline precipitation depth per catchment used to scale storm intensity factors into physical rainfall amounts. Varies by catchment climatology.'},
                    {type:'dict',   label:'Duration Params [min,mode,max]',key:'duration_params',
                     help:'Triangular distribution parameters (min, mode, max hours) for storm pulse duration by intensity category. Drives how long each precipitation event lasts.'},
                    {type:'dict',   label:'Gap Params [min,mode,max]',     key:'gap_params',
                     help:'Triangular distribution parameters (min, mode, max hours) for inter-storm drainage gaps. Short gaps produce compound flooding; long gaps allow partial drainage.'},
                    {type:'dict',   label:'Base Intensity [\u03bc,\u03c3]',key:'base_intensity_params',
                     help:'Mean and standard deviation of the intensity factor for each category. Storms are sampled from a normal distribution clipped to positive values.'},
                    {type:'dict',   label:'Sequence Type Weights [D,C,P]', key:'sequence_type_weights',
                     help:'Per-intensity weights for [doublet, cluster, persistent] sequence types. More severe storms shift towards cluster and persistent patterns.'}
                ],
                hydrograph_synthesis: [
                    {type:'dict',   label:'Hydro Alpha (\u03b1 by type)',  key:'hydro_alpha',
                     help:'Gamma shape parameter controlling the rise/fall balance of the hydrograph. Small values produce flashy peaks with long tails; large values produce broad symmetric peaks.'},
                    {type:'scalar', label:'Saturation Beta (\u03b2)',      key:'saturation_beta',               step:'0.01',
                     help:'Antecedent saturation sensitivity. Controls how much prior rainfall amplifies later storm peaks via the formula s = 1 + \u03b2 \u00d7 log(1 + A/P0). Higher values increase compound flooding.'},
                    {type:'scalar', label:'Saturation P0 (mm)',            key:'saturation_p0_mm',              step:'1',
                     help:'Reference precipitation depth for the saturation formula. Normalises antecedent rainfall so that A/P0 is dimensionless. Typical UK catchment value is 50mm.'},
                    {type:'scalar', label:'Infiltration Rate (1/hr)',      key:'infiltration_rate_per_hour',    step:'0.001',
                     help:'Hourly rate at which flood water is absorbed along the flow path. Higher values reduce peak depths at properties further from the river.'},
                    {type:'scalar', label:'Infiltration Ymax Ref (m)',     key:'infiltration_ymax_ref_m',       step:'0.01',
                     help:'Maximum infiltrable depth for fully pervious ground. The effective capacity is reduced by the impervious fraction. Once exhausted, no further infiltration occurs.'},
                    {type:'scalar', label:'Default Imperv Fraction',       key:'default_imperv_fraction',       step:'0.01',
                     help:'Fraction of impervious surface along the flow path. Urban corridors have higher values (~0.4), reducing infiltration capacity and increasing peak flood depths at properties.'},
                    {type:'scalar', label:'Superposition Cap Factor',      key:'superposition_cap_factor',      step:'0.1',
                     help:'Maximum exceedance cap above base level, expressed as a multiple of (severe - base). Prevents unrealistic compound peaks from exceeding physical channel capacity.'},
                    {type:'array',  label:'Depth Points (m)',              key:'depth_points',
                     help:'Control points (in metres) for the piecewise-linear depth-damage vulnerability curve. Paired with Damage Points to define the damage ratio at each flood depth.'},
                    {type:'array',  label:'Damage Points (ratio)',         key:'damage_points',
                     help:'Damage ratios (0-1) corresponding to each Depth Point. Defines what fraction of property value is lost at each flood depth. UK-calibrated curve.'}
                ],
                gauge_propagation: [
                    {type:'scalar', label:'Manning Roughness (n)',          key:'default_roughness',             step:'0.001',
                     help:'Manning roughness coefficient for the floodplain. Controls flow velocity via v = (1/n) R^(2/3) S^(1/2). Lower values mean faster flow and less attenuation.'},
                    {type:'scalar', label:'Retention Length (m)',           key:'default_retention_length',      step:'100',
                     help:'Exponential decay length scale for peak water surface elevation. At distance d from the river, retention = exp(-d/L). Controls how rapidly flood signal attenuates with distance.'},
                    {type:'scalar', label:'Min Slope',                     key:'min_slope',                     step:'0.0001',
                     help:'Minimum terrain slope used in Manning velocity calculation to avoid division instability. Applied when the actual slope is near-zero on flat floodplains.'},
                    {type:'scalar', label:'Recession Factor',              key:'default_recession_factor',      step:'0.1',
                     help:'Multiplier making drainage slower than arrival. Values above 1.0 extend the flood duration at properties, reflecting the physical reality that water drains more slowly than it arrives.'},
                    {type:'scalar', label:'Bankfull Offset (m)',           key:'bankfull_offset_m',             step:'0.1',
                     help:'Offset below the severe warning level at which overbank flooding begins. The severe level is an administrative safety alert set 0.5-1.0m above bankfull for UK rivers.'},
                    {type:'scalar', label:'N Nearest Gauges (IDW)',        key:'n_nearest_gauges',
                     help:'Number of nearest gauges used for inverse-distance-weighted interpolation of flood levels at each property. Controls spatial smoothing of the flood signal.'},
                    {type:'dict',   label:'Terrain Velocity Scale',        key:'terrain_velocity_scale',
                     help:'Flow velocity scaling by terrain type, relative to urban baseline (1.0). Lower values mean slower flow and more attenuation. Based on Manning n ratios for different land cover.'}
                ],
                spatial_correlation: [
                    {type:'scalar', label:'Spatial Corr Enabled',          key:'spatial_corr_enabled',
                     help:'Master switch for the spatial correlation model. When enabled, nearby gauges receive correlated precipitation fields. When disabled, each gauge receives independent rainfall.'},
                    {type:'scalar', label:'Base Range (km)',               key:'spatial_corr_base_range_km',    step:'1',
                     help:'Correlation range at unit intensity factor. Defines the e-folding distance of the exponential correlation kernel. Approximately half the Thames corridor width at 40km.'},
                    {type:'scalar', label:'Nugget',                        key:'spatial_corr_nugget',           step:'0.01',
                     help:'Micro-scale variability added to the correlation matrix diagonal. Represents sub-grid rainfall heterogeneity that is uncorrelated even between co-located gauges.'},
                    {type:'scalar', label:'Rho Intensity',                 key:'spatial_corr_rho_intensity',    step:'0.01',
                     help:'Range scaling per unit intensity factor above 1.0. Makes extreme storms more spatially coherent by increasing the correlation range with storm intensity.'},
                    {type:'scalar', label:'Sigma Lognormal',               key:'spatial_corr_sigma_lognormal',  step:'0.01',
                     help:'Log-space standard deviation of the spatial precipitation field. A value of 0.40 corresponds to approximately 40% coefficient of variation in rainfall across the catchment.'}
                ],
                stress_catalogue: [
                    {type:'scalar', label:'Min Storm Count',               key:'stress_storms_min_count',
                     help:'Minimum number of alert-breaching storms required in the stress catalogue for each gauge. If fewer storms breach alert, the gauge is excluded from stress testing.'},
                    {type:'scalar', label:'Default Duration (hours)',       key:'stress_storm_default_duration_hours',
                     help:'Default hydrograph duration used when storm metadata does not include explicit timing. Matches the event window for consistency.'},
                    {type:'scalar', label:'Default Peak Position',         key:'stress_storm_default_peak_position', step:'0.01',
                     help:'Default fractional position of the peak within the storm window (0.0 = start, 1.0 = end). A value of 0.5 centres the peak, producing symmetric rise and fall.'}
                ]
            };

            // ---- Populate a section from data ----
            function _ctrlRenderSection(sectionId, data) {
                var wrap = document.getElementById('sp-ctrl-section-' + sectionId);
                if (!wrap) return;
                var fields = _ctrlFields[sectionId];
                if (!fields || !data) { wrap.innerHTML = '<span style="color:#999;font-size:10px;">No data</span>'; return; }

                var html = '';
                fields.forEach(function(f) {
                    var val = data[f.key];
                    if (val === undefined) return;
                    if (f.type === 'scalar') {
                        html += _ctrlScalarField(f.label, sectionId + '.' + f.key, val, {step: f.step, help: f.help});
                    } else if (f.type === 'dict') {
                        html += _ctrlDictField(f.label, sectionId + '.' + f.key, val, {help: f.help});
                    } else if (f.type === 'array') {
                        html += _ctrlArrayField(f.label, sectionId + '.' + f.key, val, {help: f.help});
                    }
                });
                wrap.innerHTML = html;
            }

            // ---- Load ----
            function loadControlData() {
                var cfg = window.__BACKEND_CONFIG || {};
                var base = cfg.url || '';
                fetch(base + '/api/v1/trading/control/params')
                    .then(function(r) { return r.json(); })
                    .then(function(resp) {
                        if (resp.status !== 'success') return;
                        ctrlData = resp.params;
                        var sections = ctrlData.sections || {};
                        Object.keys(_ctrlFields).forEach(function(secId) {
                            _ctrlRenderSection(secId, sections[secId] || {});
                        });
                        ctrlClearDirty();
                        var bar = document.getElementById('sp-ctrl-status');
                        if (bar) bar.textContent = 'Source: ' + resp.source + '  |  Version: ' + (ctrlData.version || '?');
                    })
                    .catch(function(err) {
                        console.error('Control load error:', err);
                        var bar = document.getElementById('sp-ctrl-status');
                        if (bar) bar.textContent = 'Error loading parameters';
                    });
            }

            // ---- Collect form values back into JSON ----
            function _ctrlCollect() {
                if (!ctrlData) return null;
                var result = JSON.parse(JSON.stringify(ctrlData));
                var inputs = document.querySelectorAll('[data-ctrl-key]');
                inputs.forEach(function(inp) {
                    var path = inp.getAttribute('data-ctrl-key').split('.');
                    var sec = path[0];
                    if (!result.sections[sec]) result.sections[sec] = {};
                    var target = result.sections[sec];

                    if (path.length === 2) {
                        if (inp.type === 'checkbox') {
                            target[path[1]] = inp.checked;
                        } else {
                            target[path[1]] = parseFloat(inp.value);
                        }
                    } else if (path.length === 3) {
                        var key = path[1];
                        var sub = path[2];
                        if (!target[key]) target[key] = {};
                        var idx = parseInt(sub);
                        if (!isNaN(idx) && Array.isArray(target[key])) {
                            target[key][idx] = parseFloat(inp.value);
                        } else {
                            target[key][sub] = parseFloat(inp.value);
                        }
                    } else if (path.length === 4) {
                        var key2 = path[1];
                        var sub2 = path[2];
                        var idx2 = parseInt(path[3]);
                        if (!target[key2]) target[key2] = {};
                        if (!target[key2][sub2]) target[key2][sub2] = [];
                        target[key2][sub2][idx2] = parseFloat(inp.value);
                    }
                });
                return result;
            }

            // ---- Save ----
            function saveControlData() {
                var data = _ctrlCollect();
                if (!data) return;
                var cfg = window.__BACKEND_CONFIG || {};
                var base = cfg.url || '';
                var btn = document.getElementById('sp-ctrl-save-btn');
                if (btn) { btn.textContent = 'Saving...'; btn.disabled = true; }

                fetch(base + '/api/v1/trading/control/params', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                })
                .then(function(r) { return r.json(); })
                .then(function(resp) {
                    if (btn) { btn.textContent = 'Save & Apply'; btn.disabled = false; }
                    if (resp.status === 'success') {
                        ctrlClearDirty();
                        ctrlData = data;
                        var bar = document.getElementById('sp-ctrl-status');
                        if (bar) bar.textContent = 'Source: json  |  Version: ' + (data.version || '?') + '  |  Saved \u2713';
                    } else {
                        alert('Save failed: ' + (resp.message || 'Unknown error'));
                    }
                })
                .catch(function(err) {
                    if (btn) { btn.textContent = 'Save & Apply'; btn.disabled = false; }
                    alert('Save error: ' + err);
                });
            }

            // ---- Reset ----
            function resetControlData() {
                if (!confirm('Reset all parameters to Python defaults?')) return;
                var cfg = window.__BACKEND_CONFIG || {};
                var base = cfg.url || '';
                fetch(base + '/api/v1/trading/control/reset', {method: 'POST'})
                    .then(function(r) { return r.json(); })
                    .then(function(resp) {
                        if (resp.status === 'success') {
                            ctrlData = resp.params;
                            var sections = ctrlData.sections || {};
                            Object.keys(_ctrlFields).forEach(function(secId) {
                                _ctrlRenderSection(secId, sections[secId] || {});
                            });
                            ctrlClearDirty();
                            var bar = document.getElementById('sp-ctrl-status');
                            if (bar) bar.textContent = 'Source: defaults (reset)  |  Version: ' + (ctrlData.version || '?');
                        }
                    })
                    .catch(function(err) { alert('Reset error: ' + err); });
            }
    """
