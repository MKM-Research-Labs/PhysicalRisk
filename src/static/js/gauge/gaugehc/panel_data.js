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

                    // Enable/disable blotter button based on active trades
                    var blBtn = document.getElementById('hazard-blotter-link');
                    if (blBtn) {
                        var _setBlotterEnabled = function (enabled) {
                            blBtn.disabled = !enabled;
                            blBtn.style.color = enabled ? '#1565c0' : '#bbb';
                            blBtn.style.cursor = enabled ? 'pointer' : 'default';
                            blBtn.style.background = enabled ? '#e3f2fd' : '#f5f5f5';
                        };
                        try {
                            var agResp = await fetch(baseUrl + '/api/v1/trading/blotter/active-gauges', {mode: 'cors'});
                            var agData = await agResp.json();
                            var hasT = agData.status === 'success' && (agData.gauge_ids || []).indexOf(gaugeId) !== -1;
                            _setBlotterEnabled(hasT);
                        } catch (e) {
                            // Fail open: the active-gauges probe is a best-effort
                            // convenience. If it errors (e.g. the endpoint 500s per
                            // blotter.py:154's documented contract), enable the button
                            // rather than silently locking the trader out — the Trading
                            // Desk filters to this gauge on open regardless.
                            _setBlotterEnabled(true);
                        }
                    }

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
                                var gName = hazardData.gauge_name || '';
                                var dirLabel = td.is_payer ? 'Pay' : 'Rcv';
                                titleEl.textContent = __GAUGE_TITLE__ + ' — Close Out: ' + dirLabel;
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
                                var gName = hazardData.gauge_name || '';
                                var dirLabel = td.is_payer ? 'Pay' : 'Rcv';
                                titleEl.textContent = __GAUGE_TITLE__ + ' — ' + td.swap_id + ' | ' + dirLabel;
                            }
                        }

                        activeTab = 0;
                    } else {
                        isTradeReview = false;
                        isCloseOut = false;
                        closeOutSwapId = null;
                    }

                    // Store gauge name for blotter navigation
                    if (hazardData.gauge_name && hazardPanel) {
                        hazardPanel.dataset.gaugeName = hazardData.gauge_name;
                    }

                    // Update title with gauge ID and name
                    var titleEl = document.getElementById('hazard-panel-title');
                    if (titleEl && !isTradeReview && !isCloseOut) {
                        var gName = hazardData.gauge_name || '';
                        titleEl.textContent = __GAUGE_TITLE__;
                    }

                    switchTab(activeTab);
                    status.textContent = hazardData.gauge_name || 'Loaded';
                } catch (error) {
                    console.error('[GaugeHazard] Load error:', error);
                    status.textContent = 'Error: ' + error.message;
                    if (window.showError) window.showError('Failed to load hazard curve data');
                }
            }
