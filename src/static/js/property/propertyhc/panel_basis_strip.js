// Copyright (c) 2022-2026 MKM Research Labs.
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

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
                var sheCount = phcData._she ? (phcData._she.flood_count || 0) : '\u2014';
                var shdCount = phcData._shd ? (phcData._shd.flood_count || 0) : '\u2014';
                var briCount = phcData._bri ? (phcData._bri.flood_count || 0) : '\u2014';

                var chipStyle = 'display:inline-flex;align-items:center;gap:var(--space-2);padding:var(--space-2) var(--space-5);' +
                    'border-radius:var(--radius-pill);font-weight:600;font-size:var(--size-xs);';
                var arrowStyle = 'color:var(--faint);font-size:var(--size-lg);margin:0 var(--space-2);';
                var countStyle = 'font-size:var(--size-lg);font-weight:700;';
                var labelStyle = 'font-size:var(--size-xxs);color:var(--muted);text-transform:uppercase;letter-spacing:0.3px;line-height:1.2;';
                var detailStyle = 'font-size:var(--size-xxs);color:var(--muted-2);line-height:1.1;';

                // Resilient (BRI) chip — only rendered when a BRI curve exists.
                var briChip = '';
                if (hasBri) {
                    briChip =
                        '<span style="' + arrowStyle + '">\u2192</span>' +
                        '<div style="' + chipStyle + 'background:var(--product-bg);color:var(--product-ink);flex-direction:column;min-width:70px;text-align:center;">' +
                        '<span style="' + countStyle + '">' + briCount + '</span>' +
                        '<span style="' + labelStyle + '">BRI resilient</span>' +
                        '<span style="' + detailStyle + '">' + briSpread.toFixed(1) + 'bp</span>' +
                        '</div>';
                }

                strip.innerHTML =
                    '<div style="display:flex;align-items:center;gap:var(--space-1);">' +

                    // Gauge
                    '<div style="' + chipStyle + 'background:var(--danger-bg-soft);color:var(--red-dark);flex-direction:column;min-width:70px;text-align:center;">' +
                    '<span style="' + countStyle + '">' + gaugeCount + '</span>' +
                    '<span style="' + labelStyle + '">gauge severe</span>' +
                    '<span style="' + detailStyle + '">' + gaugeSpread.toFixed(0) + 'bp</span>' +
                    '</div>' +

                    '<span style="' + arrowStyle + '">\u2192</span>' +

                    // SHE (elevation)
                    '<div style="' + chipStyle + 'background:var(--warn-bg-warm);color:var(--amber-deep);flex-direction:column;min-width:70px;text-align:center;">' +
                    '<span style="' + countStyle + '">' + sheCount + '</span>' +
                    '<span style="' + labelStyle + '">SHE</span>' +
                    '<span style="' + detailStyle + '">+' + elevDiff.toFixed(1) + 'm</span>' +
                    '</div>' +

                    '<span style="' + arrowStyle + '">\u2192</span>' +

                    // SHD (distance)
                    '<div style="' + chipStyle + 'background:var(--ok-bg);color:var(--green-dark);flex-direction:column;min-width:70px;text-align:center;">' +
                    '<span style="' + countStyle + '">' + shdCount + '</span>' +
                    '<span style="' + labelStyle + '">SHD</span>' +
                    '<span style="' + detailStyle + '">' + distKm.toFixed(1) + 'km</span>' +
                    '</div>' +

                    '<span style="' + arrowStyle + '">\u2192</span>' +

                    // Asset (residential property or commercial asset)
                    '<div style="' + chipStyle + 'background:var(--accent-soft);color:var(--accent-mid);flex-direction:column;min-width:70px;text-align:center;">' +
                    '<span style="' + countStyle + '">' + propFloods + '</span>' +
                    '<span style="' + labelStyle + '">asset</span>' +
                    '<span style="' + detailStyle + '">' + propSpread.toFixed(1) + 'bp</span>' +
                    '</div>' +

                    // Resilient (BRI) chip — appended only when present
                    briChip +

                    // Separator + spread summary
                    '<div style="margin-left:var(--space-6);padding-left:var(--space-6);border-left:1px solid var(--line-strong);font-size:var(--size-xxs);color:var(--text-3);line-height:1.5;">' +
                    '<div><b>Gauge:</b> ' + gaugeName + '</div>' +
                    '<div><b>Spread:</b> ' + gaugeSpread.toFixed(1) + 'bp \u2192 ' + propSpread.toFixed(1) + 'bp</div>' +
                    '<div><b>Basis:</b> ' + (gaugeSpread - propSpread).toFixed(1) + 'bp</div>' +
                    (hasBri ? '<div><b>Resilience:</b> \u2212' + resilienceCredit.toFixed(1) + 'bp \u2192 ' + briSpread.toFixed(1) + 'bp</div>' : '') +
                    '</div>' +

                    '</div>';

                strip.style.display = 'block';
            }
