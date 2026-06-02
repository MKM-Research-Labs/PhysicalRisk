# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""Basis summary strip — populateBasisStrip() JS function."""


def get_js() -> str:
    """Return JS for the populateBasisStrip() function."""
    return """
            function populateBasisStrip() {
                var strip = document.getElementById('phc-basis-strip');
                if (!strip || !phcData) return;

                var ng0 = (phcData.nearest_gauges || [])[0] || {};
                var gaugeSevere = phcData._severe_at_gauge || 0;
                var propFloods = phcData.flood_count || 0;
                var sd = phcData.spread_decomposition || {};

                // Spread values come straight from spread_decomposition in the
                // hazard data — the generator already used the correct storm
                // count when it built that block. The previous implementation
                // hard-coded /20000 (the thames default --num-storms) which made
                // every catchment with a different storm count read 200x too
                // small on the gauge/SHE/SHD side, while the property spread
                // (which used the real value below) stayed correct — visually
                // inconsistent.
                var gaugeSpread = sd.gauge_spread_bps || 0;
                var propSpread = sd.property_spread_bps
                    || ((phcData.term_structure || {}).severe
                        ? phcData.term_structure.severe.prs_spread_bps[0]
                        : 0);

                // BRI-adjusted (resilient) spread — present once the propertybri
                // stage has run. Raising the effective flood floor removes severe
                // floods, so the resilient spread is <= the pure property spread.
                var hasBri = (sd.bri_spread_bps !== undefined && sd.bri_spread_bps !== null);
                var briSpread = sd.bri_spread_bps || 0;
                var resilienceCredit = sd.resilience_effect_bps;
                if (resilienceCredit === undefined || resilienceCredit === null) {
                    resilienceCredit = propSpread - briSpread;
                }

                // Physical measurements
                var stormsGauges = (phcData._storms_data || {}).nearest_gauges || [];
                var stormGauge0 = stormsGauges.find(function(sg) { return sg.gauge_id === ng0.gauge_id; }) || {};
                var gaugeName = stormGauge0.gauge_name || (ng0.gauge_id || '').substring(0, 18);
                var gaugeElev = ng0.gauge_elevation_m || 0;
                var propElev = phcData.elevation_m || 0;
                var distKm = ng0.distance_km || 0;
                var floorLevel = phcData.floor_level_m || 0;
                var elevDiff = propElev - gaugeElev;
                var effectiveDiff = elevDiff + floorLevel - 0.5;

                // Storm counts at each stage
                var storms = phcData.storm_details || [];
                var gaugeCount = storms.filter(function(s) { return s.exceeded_severe; }).length || gaugeSevere;
                var sheCount = phcData._she ? (phcData._she.flood_count || 0) : '\\u2014';
                var shdCount = phcData._shd ? (phcData._shd.flood_count || 0) : '\\u2014';
                var briCount = phcData._bri ? (phcData._bri.flood_count || 0) : '\\u2014';

                var chipStyle = 'display:inline-flex;align-items:center;gap:4px;padding:4px 10px;' +
                    'border-radius:12px;font-weight:600;font-size:11px;';
                var arrowStyle = 'color:#bbb;font-size:16px;margin:0 4px;';
                var countStyle = 'font-size:15px;font-weight:700;';
                var labelStyle = 'font-size:9px;color:#888;text-transform:uppercase;letter-spacing:0.3px;line-height:1.2;';
                var detailStyle = 'font-size:9px;color:#999;line-height:1.1;';

                // Resilient (BRI) chip — only rendered when a BRI curve exists.
                var briChip = '';
                if (hasBri) {
                    briChip =
                        '<span style="' + arrowStyle + '">\\u2192</span>' +
                        '<div style="' + chipStyle + 'background:#EDE7F6;color:#4527A0;flex-direction:column;min-width:70px;text-align:center;">' +
                        '<span style="' + countStyle + '">' + briCount + '</span>' +
                        '<span style="' + labelStyle + '">BRI resilient</span>' +
                        '<span style="' + detailStyle + '">' + briSpread.toFixed(1) + 'bp</span>' +
                        '</div>';
                }

                strip.innerHTML =
                    '<div style="display:flex;align-items:center;gap:2px;">' +

                    // Gauge
                    '<div style="' + chipStyle + 'background:#FFEBEE;color:#C62828;flex-direction:column;min-width:70px;text-align:center;">' +
                    '<span style="' + countStyle + '">' + gaugeCount + '</span>' +
                    '<span style="' + labelStyle + '">gauge severe</span>' +
                    '<span style="' + detailStyle + '">' + gaugeSpread.toFixed(0) + 'bp</span>' +
                    '</div>' +

                    '<span style="' + arrowStyle + '">\\u2192</span>' +

                    // SHE (elevation)
                    '<div style="' + chipStyle + 'background:#FFF3E0;color:#E65100;flex-direction:column;min-width:70px;text-align:center;">' +
                    '<span style="' + countStyle + '">' + sheCount + '</span>' +
                    '<span style="' + labelStyle + '">SHE</span>' +
                    '<span style="' + detailStyle + '">+' + elevDiff.toFixed(1) + 'm</span>' +
                    '</div>' +

                    '<span style="' + arrowStyle + '">\\u2192</span>' +

                    // SHD (distance)
                    '<div style="' + chipStyle + 'background:#E8F5E9;color:#2E7D32;flex-direction:column;min-width:70px;text-align:center;">' +
                    '<span style="' + countStyle + '">' + shdCount + '</span>' +
                    '<span style="' + labelStyle + '">SHD</span>' +
                    '<span style="' + detailStyle + '">' + distKm.toFixed(1) + 'km</span>' +
                    '</div>' +

                    '<span style="' + arrowStyle + '">\\u2192</span>' +

                    // Asset (residential property or commercial asset)
                    '<div style="' + chipStyle + 'background:#E3F2FD;color:#1565C0;flex-direction:column;min-width:70px;text-align:center;">' +
                    '<span style="' + countStyle + '">' + propFloods + '</span>' +
                    '<span style="' + labelStyle + '">asset</span>' +
                    '<span style="' + detailStyle + '">' + propSpread.toFixed(1) + 'bp</span>' +
                    '</div>' +

                    // Resilient (BRI) chip — appended only when present
                    briChip +

                    // Separator + spread summary
                    '<div style="margin-left:12px;padding-left:12px;border-left:1px solid #ddd;font-size:10px;color:#666;line-height:1.5;">' +
                    '<div><b>Gauge:</b> ' + gaugeName + '</div>' +
                    '<div><b>Spread:</b> ' + gaugeSpread.toFixed(1) + 'bp \\u2192 ' + propSpread.toFixed(1) + 'bp</div>' +
                    '<div><b>Basis:</b> ' + (gaugeSpread - propSpread).toFixed(1) + 'bp</div>' +
                    (hasBri ? '<div><b>Resilience:</b> \\u2212' + resilienceCredit.toFixed(1) + 'bp \\u2192 ' + briSpread.toFixed(1) + 'bp</div>' : '') +
                    '</div>' +

                    '</div>';

                strip.style.display = 'block';
            }
"""
