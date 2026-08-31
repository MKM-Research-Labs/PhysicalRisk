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

            window.commitPropertyPRSTrade = async function() {
                var btn = document.getElementById('phc-commit-btn');
                if (btn) { btn.disabled = true; btn.textContent = 'Committing...'; }

                try {
                    var result = computePropertyPRSCashflows();
                    var ctpyEl = document.getElementById('phc-counterparty');
                    var ctpyId = ctpyEl ? ctpyEl.value : '';
                    var ctpyName = ctpyEl ? ctpyEl.options[ctpyEl.selectedIndex].text : '';

                    var propertyId = phcPanel ? phcPanel.dataset.propertyId : '';
                    var triggerNames = {'any_flood': 'alert', 'moderate': 'warning', 'severe': 'severe'};
                    var trigger = triggerNames[result.triggerKey] || result.triggerKey;

                    var cfg = window.__BACKEND_CONFIG || {};
                    var baseUrl = cfg.url || '';

                    // Primary gauge from nearest-gauge components, fallback to phcData
                    var primaryGauge = result.gaugeComponents && result.gaugeComponents.length > 0
                        ? result.gaugeComponents[0] : null;
                    var ng0 = (phcData.nearest_gauges || [])[0] || {};
                    var commitGaugeId = (primaryGauge && primaryGauge.gauge_id) || ng0.gauge_id || '';

                    if (!commitGaugeId) {
                        throw new Error('gauge_id is required — no nearest gauge found for this property');
                    }

                    var payload = {
                        gauge_id: commitGaugeId,
                        gauge_name: ng0.gauge_name || commitGaugeId,
                        property_id: propertyId,
                        counterparty_id: ctpyId,
                        counterparty_name: ctpyName,
                        trigger: trigger,
                        notional: result.notional,
                        tenor: result.tenor,
                        spread_bps: result.spreadBps,
                        fair_spread_bps: result.fairSpreadBps,
                        npv: result.npv,
                        premium_leg_pv: result.totalPremPV,
                        protection_leg_pv: result.totalProtPV,
                        risky_annuity: result.riskyAnnuity,
                        yield_curve: result.yieldCurve,
                        recovery: result.recovery,
                        avg_basis_bps: result.avgBasis,
                        gauge_components: result.gaugeComponents,
                        cashflows: result.periods,
                        ea_flood_zone: result.selectedZone || '',
                        ea_flood_zone_actual: result.actualZone || '',
                        terrain_delta_bps: result.terrainDelta || 0
                    };

                    var response = await window.__mkmAdminFetch(baseUrl + '/api/v1/prs/commit', {
                        method: 'POST',
                        body: JSON.stringify(payload)
                    });

                    var data = await response.json();
                    if (data.status === 'success') {
                        if (btn) { btn.textContent = 'Committed'; btn.style.background = 'var(--accent)'; }
                        if (window.showSuccess) window.showSuccess('Trade ' + data.swap_id + ' committed');

                        // Show PDF inline via panel
                        if (data.pdf_base64) {
                            if (window.PropertyPDFPanel && typeof window.PropertyPDFPanel.show === 'function') {
                                window.PropertyPDFPanel.show(data.swap_id, data.pdf_base64);
                            } else {
                                window.open(baseUrl + '/api/v1/prs/trades/' + data.swap_id + '/pdf', '_blank');
                            }
                        }

                        document.getElementById('phc-status').textContent =
                            data.swap_id + ' committed | Property PRS';

                        // Refresh active gauges list and invalidate blotter cache
                        try {
                            var agResp = await fetch(baseUrl + '/api/v1/trading/blotter/active-gauges', {mode: 'cors'});
                            var agData = await agResp.json();
                            if (agData.status === 'success' && window.setActiveGauges) {
                                window.setActiveGauges(agData.gauge_ids || []);
                            }
                        } catch (e) { /* non-critical */ }
                        window._tdPreBlotter = null;
                    } else {
                        throw new Error(data.message || 'Commit failed');
                    }
                } catch (error) {
                    console.error('Property PRS commit error:', error);
                    if (btn) { btn.textContent = 'Commit'; btn.disabled = false; btn.style.background = 'var(--green-bright)'; }
                    if (window.showError) window.showError('Commit failed: ' + error.message);
                }
            };
