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
Gauge hazard curve — PRS Pricing: trade commit.

POST to /api/v1/prs/commit with trade parameters,
handles close-out mode, PDF display, and notifications.
"""


def get_js() -> str:
    """Return JS fragment for PRS trade commit."""
    return """
            // ================================================================
            // Commit PRS Trade
            // ================================================================
            window.commitPRSTrade = async function() {
                var btn = document.getElementById('prs-commit-btn');
                if (btn) { btn.disabled = true; btn.textContent = isCloseOut ? 'Closing...' : 'Committing...'; }

                try {
                    var result = computePRSCashflows();
                    var ctpyEl = document.getElementById('prs-counterparty');
                    var ctpyId = ctpyEl ? ctpyEl.value : '';
                    var ctpyName = ctpyEl ? ctpyEl.options[ctpyEl.selectedIndex].text : '';

                    var gaugeId = hazardData ? hazardData.gauge_id : '';
                    var gaugeName = hazardData ? (hazardData.gauge_name || '') : '';

                    var cfg = window.__BACKEND_CONFIG || {};
                    var baseUrl = cfg.url || '';

                    var payload = {
                        gauge_id: gaugeId,
                        gauge_name: gaugeName,
                        counterparty_id: ctpyId,
                        counterparty_name: ctpyName,
                        trigger: result.trigger,
                        notional: result.notional,
                        tenor: result.tenor,
                        maturity_date: result.maturityDate,
                        spread_bps: result.spreadBps,
                        fair_spread_bps: result.fairSpreadBps,
                        npv: result.npv,
                        premium_leg_pv: result.totalPremPV,
                        protection_leg_pv: result.totalProtPV,
                        risky_annuity: result.riskyAnnuity,
                        yield_curve: result.yieldCurve,
                        recovery: result.recovery,
                        payer: result.isPayer,
                        cashflows: result.periods
                    };

                    // Close-out: include original swap ID and flip payer flag
                    if (isCloseOut && closeOutSwapId) {
                        payload.close_out_of = closeOutSwapId;
                        payload.payer = closeOutIsPayer;
                    }

                    var response = await fetch(baseUrl + '/api/v1/prs/commit', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });

                    var data = await response.json();
                    if (data.status === 'success') {
                        var actionLabel = isCloseOut ? 'Closed' : 'Committed';
                        if (btn) { btn.textContent = actionLabel; btn.style.background = '#1976D2'; }
                        var msg = isCloseOut
                            ? 'Trade ' + closeOutSwapId + ' closed. Offsetting trade ' + data.swap_id
                            : 'Trade ' + data.swap_id + ' committed';
                        if (window.showSuccess) window.showSuccess(msg);

                        // Show PDF inline via panel
                        if (data.pdf_base64) {
                            if (window.GaugePDFPanel && typeof window.GaugePDFPanel.show === 'function') {
                                window.GaugePDFPanel.show(data.swap_id, data.pdf_base64);
                            } else if (window.PropertyPDFPanel && typeof window.PropertyPDFPanel.show === 'function') {
                                window.PropertyPDFPanel.show(data.swap_id, data.pdf_base64);
                            } else {
                                window.open(baseUrl + '/api/v1/prs/trades/' + data.swap_id + '/pdf', '_blank');
                            }
                        }

                        document.getElementById('hazard-status').textContent =
                            data.swap_id + ' ' + actionLabel.toLowerCase() + ' | ' + result.trigger;

                        // Refresh active gauges list (for context menu + blotter)
                        try {
                            var agResp = await fetch(baseUrl + '/api/v1/trading/blotter/active-gauges', {mode: 'cors'});
                            var agData = await agResp.json();
                            if (agData.status === 'success') {
                                if (window.setActiveGauges) window.setActiveGauges(agData.gauge_ids || []);
                                // Enable blotter button if this gauge now has trades
                                var blBtn = document.getElementById('hazard-blotter-link');
                                if (blBtn) {
                                    blBtn.disabled = false;
                                    blBtn.style.color = '#1565c0';
                                    blBtn.style.cursor = 'pointer';
                                    blBtn.style.background = '#e3f2fd';
                                }
                            }
                        } catch (e) { /* non-critical */ }

                        // Invalidate blotter cache so next open fetches fresh data
                        window._tdPreBlotter = null;
                    } else {
                        throw new Error(data.message || 'Failed');
                    }
                } catch (error) {
                    console.error('PRS commit error:', error);
                    if (btn) { btn.textContent = isCloseOut ? 'Close Out' : 'Commit'; btn.disabled = false; btn.style.background = isCloseOut ? '#ef5350' : '#4CAF50'; }
                    if (window.showError) window.showError('Failed: ' + error.message);
                }
            };
"""
