# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Panel data loading — loadHazardData() async function."""


def get_data_js() -> str:
    """Return JS that defines the loadHazardData() async function."""
    return """
            // ================================================================
            // Data loading
            // ================================================================
            async function loadHazardData(gaugeId) {
                var status = document.getElementById('hazard-status');
                status.textContent = 'Loading...';

                try {
                    var cfg = window.__BACKEND_CONFIG || {};
                    var baseUrl = cfg.url || '';
                    var url = baseUrl + '/api/v1/gauges/' + gaugeId + '/hazard';

                    var response = await fetch(url, {mode: 'cors'});
                    if (!response.ok) throw new Error('HTTP ' + response.status);

                    var data = await response.json();
                    if (data.status !== 'success') throw new Error(data.message || 'Failed');

                    hazardData = data;

                    // Also fetch counterparties for PRS tab
                    try {
                        var ctpyResp = await fetch(baseUrl + '/api/v1/counterparties', {mode: 'cors'});
                        if (ctpyResp.ok) {
                            var ctpyData = await ctpyResp.json();
                            if (ctpyData.status === 'success') {
                                counterpartyData = ctpyData.counterparties || [];
                            }
                        }
                    } catch (ctpyErr) {
                        console.warn('Counterparty data not available:', ctpyErr.message);
                    }

                    console.log('[GaugeHazard] Loaded hazard data for', gaugeId);
                    // Fetch market hazard term structures for overlay (await so data
                    // is available when renderPRSPricing runs on first open)
                    await _fetchMarketHazardTS();
                    buildPRSControls();

                    // Pre-populate inputs from blotter (trade review or close-out)
                    if (window._tradeReviewData) {
                        var td = window._tradeReviewData;
                        window._tradeReviewData = null;

                        // Set counterparty by matching ID first, then name
                        var ctpySel = document.getElementById('prs-counterparty');
                        if (ctpySel) {
                            var matched = false;
                            if (td.counterparty_id) {
                                for (var i = 0; i < ctpySel.options.length; i++) {
                                    if (ctpySel.options[i].value === td.counterparty_id) {
                                        ctpySel.selectedIndex = i;
                                        matched = true;
                                        break;
                                    }
                                }
                            }
                            if (!matched && td.counterparty) {
                                for (var i = 0; i < ctpySel.options.length; i++) {
                                    if (ctpySel.options[i].text.indexOf(td.counterparty) >= 0) {
                                        ctpySel.selectedIndex = i;
                                        break;
                                    }
                                }
                            }
                        }

                        // Set direction
                        var dirSel = document.getElementById('prs-direction');
                        if (dirSel && td.is_payer != null) {
                            dirSel.value = td.is_payer ? 'payer' : 'receiver';
                        }

                        // Set trigger
                        var trigSel = document.getElementById('prs-trigger');
                        if (trigSel && td.trigger) trigSel.value = td.trigger;

                        // Set notional
                        var notInput = document.getElementById('prs-notional');
                        if (notInput && td.notional) notInput.value = Number(td.notional).toLocaleString();

                        // Set maturity by matching the date value
                        var matSel = document.getElementById('prs-maturity');
                        if (matSel && td.maturity) {
                            for (var i = 0; i < matSel.options.length; i++) {
                                if (matSel.options[i].value === td.maturity) {
                                    matSel.selectedIndex = i;
                                    break;
                                }
                            }
                            // If exact match not found, add as custom option
                            if (matSel.value !== td.maturity) {
                                var opt = document.createElement('option');
                                opt.value = td.maturity;
                                opt.text = td.maturity + ' (custom)';
                                opt.dataset.tenor = td.tenor || 5;
                                matSel.appendChild(opt);
                                matSel.value = td.maturity;
                            }
                        }

                        // Set spread
                        var spdInput = document.getElementById('prs-spread');

                        if (td.is_close_out) {
                            // CLOSE-OUT MODE: opposing trade, spread + ctpy editable
                            isCloseOut = true;
                            isTradeReview = false;
                            closeOutSwapId = td.close_out_of || '';
                            closeOutIsPayer = td.is_payer;

                            // Set spread to fair (editable — trader chooses exit level)
                            if (spdInput && td.fair_spread_bps != null) {
                                spdInput.value = td.fair_spread_bps.toFixed(1);
                            }

                            // Disable contract details: direction, counterparty, trigger, notional, maturity
                            var lockedIds = ['prs-direction', 'prs-counterparty', 'prs-trigger', 'prs-notional', 'prs-maturity', 'prs-maturity-info'];
                            lockedIds.forEach(function(id) {
                                var el = document.getElementById(id);
                                if (el) { el.disabled = true; el.style.opacity = '0.7'; el.style.cursor = 'not-allowed'; }
                            });
                            // Only spread remains editable (counterparty locked to original)

                            var titleEl = document.getElementById('hazard-panel-title');
                            if (titleEl) {
                                var dirLabel = td.is_payer ? 'Pay' : 'Rcv';
                                titleEl.textContent = 'Close Out: ' + dirLabel + ' | ' + gaugeId;
                            }
                        } else {
                            // TRADE REVIEW MODE: ALL inputs disabled, read-only
                            isTradeReview = true;
                            isCloseOut = false;
                            closeOutSwapId = null;

                            if (spdInput && td.trade_spread_bps != null) spdInput.value = td.trade_spread_bps.toFixed(1);

                            // Disable ALL inputs
                            var allIds = ['prs-direction', 'prs-counterparty', 'prs-trigger', 'prs-notional', 'prs-maturity', 'prs-spread', 'prs-maturity-info'];
                            allIds.forEach(function(id) {
                                var el = document.getElementById(id);
                                if (el) { el.disabled = true; el.style.opacity = '0.7'; el.style.cursor = 'not-allowed'; }
                            });

                            var titleEl = document.getElementById('hazard-panel-title');
                            if (titleEl) {
                                var dirLabel = td.is_payer ? 'Pay' : 'Rcv';
                                titleEl.textContent = td.swap_id + ' | ' + dirLabel + ' | ' + gaugeId;
                            }
                        }

                        activeTab = 0;
                    } else {
                        isTradeReview = false;
                        isCloseOut = false;
                        closeOutSwapId = null;
                    }

                    // Update title with gauge ID and name
                    var titleEl = document.getElementById('hazard-panel-title');
                    if (titleEl && !isTradeReview && !isCloseOut) {
                        var gName = hazardData.gauge_name || '';
                        titleEl.textContent = gName ? gName + ' (' + gaugeId + ')' : gaugeId;
                    }

                    switchTab(activeTab);
                    status.textContent = hazardData.gauge_name || 'Loaded';
                } catch (error) {
                    console.error('[GaugeHazard] Load error:', error);
                    status.textContent = 'Error: ' + error.message;
                    if (window.showError) window.showError('Failed to load hazard curve data');
                }
            }
"""
