# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Property hazard curve — PRS Pricing tab sub-module.

Input controls, analytical semi-annual cashflow pricer,
6-component PRS rendering with basis waterfall, and trade commit.

Sub-modules:
- phc_prs_pricer: Survival interpolation + cashflow computation
- phc_prs_render: 6-component PRS rendering with basis waterfall
"""

from . import phc_prs_pricer, phc_prs_render


def get_js() -> str:
    """Return JS fragment for PRS pricing tab (injected into parent IIFE)."""
    return """
            // ================================================================
            // PRS Controls (input form for Tab 2)
            // ================================================================
            function buildPRSControls() {
                var controls = document.getElementById('phc-controls');
                var inputStyle = 'padding:3px 6px;border:1px solid #ccc;border-radius:3px;width:90px;font-size:11px;';
                var labelStyle = 'font-weight:600;font-size:11px;color:#555;margin-right:3px;';
                var selectStyle = 'padding:3px 6px;border:1px solid #ccc;border-radius:3px;font-size:11px;';

                // Build counterparty options
                var ctpyOptions = '<option value="">-- Select --</option>';
                counterpartyData.forEach(function(c) {
                    var label = c.short_name + ' (' + c.credit_rating + ')';
                    ctpyOptions += '<option value="' + c.counterparty_id + '">' + label + '</option>';
                });

                // Build EA zone dropdown, default to property's actual zone
                var zoneOrder = ['Zone 3b', 'Zone 3a', 'Zone 3', 'Zone 2', 'Zone 1'];
                var actualZone = phcData.flood_zone || 'Zone 1';
                var zoneOptions = '';
                zoneOrder.forEach(function(z) {
                    var sel = (z === actualZone) ? ' selected' : '';
                    zoneOptions += '<option value="' + z + '"' + sel + '>' + z + '</option>';
                });

                controls.innerHTML =
                    '<div style="display:flex;align-items:center;gap:12px;padding:8px 16px;flex-wrap:wrap;">' +
                    '<span style="' + labelStyle + '">Direction:</span>' +
                    '<select id="phc-direction" style="' + selectStyle + '">' +
                    '<option value="payer">Payer (buy protection)</option>' +
                    '<option value="receiver">Receiver (sell protection)</option>' +
                    '</select>' +
                    '<span style="' + labelStyle + '">Ctpy:</span>' +
                    '<select id="phc-counterparty" style="' + selectStyle + 'min-width:140px;">' +
                    ctpyOptions +
                    '</select>' +
                    '<span style="' + labelStyle + '">EA Zone:</span>' +
                    '<select id="phc-ea-zone" style="' + selectStyle + '">' +
                    zoneOptions +
                    '</select>' +
                    '<span style="' + labelStyle + '">Notional:</span>' +
                    '<input id="phc-notional" type="text" value="10,000,000" style="' + inputStyle + '">' +
                    '<span style="' + labelStyle + '">Tenor (yr):</span>' +
                    '<input id="phc-tenor" type="number" value="5" min="1" max="30" style="' + inputStyle + 'width:50px;">' +
                    '<span style="' + labelStyle + '">Spread (bps):</span>' +
                    '<input id="phc-spread" type="number" value="' + Math.round(((phcData.term_structure || {}).severe || {}).prs_spread_bps ? phcData.term_structure.severe.prs_spread_bps[0] : 100) + '" min="1" max="10000" style="' + inputStyle + 'width:60px;">' +
                    '</div>';

                // Auto-recompute on any input change
                var ids = ['phc-direction', 'phc-counterparty', 'phc-ea-zone', 'phc-notional', 'phc-tenor', 'phc-spread'];
                ids.forEach(function(id) {
                    var el = document.getElementById(id);
                    if (el) el.addEventListener('change', function() { if (activeTab === 2) renderPRSPricing(); });
                });
            }

""" + phc_prs_pricer.get_js() + phc_prs_render.get_js() + """
            // ================================================================
            // Commit Property PRS Trade
            // ================================================================
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
                        if (btn) { btn.textContent = 'Committed'; btn.style.background = '#1976D2'; }
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
                    if (btn) { btn.textContent = 'Commit'; btn.disabled = false; btn.style.background = '#4CAF50'; }
                    if (window.showError) window.showError('Commit failed: ' + error.message);
                }
            };
"""
