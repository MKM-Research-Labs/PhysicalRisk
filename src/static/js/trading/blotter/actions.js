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

            window.tdViewTrade = function(tradeIndex) {
                if (!tdBlotterData || tradeIndex < 0 || tradeIndex >= tdBlotterData.length) return;

                var t = tdBlotterData[tradeIndex];
                var gaugeId = t.gauge_id || '';
                var propertyId = t.property_id || '';

                // Store trade data for read-only review
                window._tradeReviewData = {
                    swap_id: t.swap_id,
                    gauge_id: gaugeId,
                    property_id: propertyId,
                    counterparty: t.counterparty || '',
                    counterparty_id: t.counterparty_id || '',
                    trigger: t.trigger || 'severe',
                    notional: t.notional || 10000000,
                    tenor: t.tenor || 5,
                    maturity: t.maturity || '',
                    trade_spread_bps: t.trade_spread_bps,
                    fair_spread_bps: t.fair_spread_bps,
                    is_payer: t.is_payer,
                    is_close_out: false
                };

                // Hide the trading desk panel first
                if (window.TradingDesk && window.TradingDesk.hide) {
                    window.TradingDesk.hide();
                }

                if (propertyId && window.PropertyHazardCurvePanel && window.PropertyHazardCurvePanel.show) {
                    window.PropertyHazardCurvePanel.show(propertyId);
                } else if (propertyId && window.viewPropertyHazard) {
                    window.viewPropertyHazard(propertyId);
                } else if (gaugeId && window.GaugeHazardCurve && window.GaugeHazardCurve.show) {
                    window.GaugeHazardCurve.show(gaugeId);
                } else if (gaugeId && window.viewHazardCurve) {
                    window.viewHazardCurve(gaugeId);
                } else {
                    console.warn('[Blotter] No PRS panel available for', gaugeId, propertyId);
                }
            };

            // Close out trade: show mini pricer modal with user-negotiated closeout spread
            window.tdCloseOutTrade = function(tradeIndex) {
                if (!tdBlotterData || tradeIndex < 0 || tradeIndex >= tdBlotterData.length) return;

                var t = tdBlotterData[tradeIndex];
                var swapId = t.swap_id || '';
                var closeDir = t.is_payer ? 'Receiver (sell protection)' : 'Payer (buy protection)';
                var closeDirColor = t.is_payer ? 'var(--green-dark)' : 'var(--red-dark)';
                var gaugeName = t.gauge_name || t.gauge_id || '';
                var tradeSpd = t.trade_spread_bps || 0;
                var fairSpd = t.fair_spread_bps || 0;
                var spreadMove = fairSpd - tradeSpd;
                var moveColor = spreadMove >= 0 ? 'var(--green-dark)' : 'var(--red-dark)';
                var moveSign = spreadMove >= 0 ? '+' : '';
                var notional = t.original_notional || t.notional || 0;
                var riskyAnnuity = t.risky_annuity || 0;
                var direction = t.is_payer ? 1.0 : -1.0;

                // Helper: recalculate settlement from a given closeout spread
                function calcSettlement(closeoutSpd) {
                    var spreadDiff = (closeoutSpd - tradeSpd) / 10000;
                    var mtm = spreadDiff * riskyAnnuity * notional * direction;
                    return { amount: Math.abs(mtm), dir: mtm >= 0 ? 'Receivable' : 'Payable',
                             color: mtm >= 0 ? 'var(--green-dark)' : 'var(--red-dark)' };
                }

                // Remove any existing modal
                var existing = document.getElementById('td-closeout-modal');
                if (existing) existing.remove();

                var overlay = document.createElement('div');
                overlay.id = 'td-closeout-modal';
                overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:var(--scrim);z-index:10000;display:flex;align-items:center;justify-content:center;';

                var modal = document.createElement('div');
                modal.style.cssText = 'background:var(--panel);border-radius:8px;box-shadow:var(--shadow-modal);width:420px;max-width:90vw;overflow:hidden;';

                // Header
                modal.innerHTML =
                    '<div style="padding:12px 16px;background:var(--accent-mid);color:var(--inverse);display:flex;justify-content:space-between;align-items:center;">' +
                        '<div style="font-size:13px;font-weight:700;">Close-Out: ' + swapId + '</div>' +
                        '<span id="td-closeout-close" style="cursor:pointer;font-size:18px;opacity:0.8;">&times;</span>' +
                    '</div>' +

                    // Trade details
                    '<div style="padding:12px 16px;border-bottom:1px solid var(--line-soft);">' +
                        '<div style="display:flex;justify-content:space-between;padding:3px 0;font-size:11px;">' +
                            '<span style="color:var(--muted);">Gauge</span><span style="font-weight:600;">' + gaugeName + '</span></div>' +
                        '<div style="display:flex;justify-content:space-between;padding:3px 0;font-size:11px;">' +
                            '<span style="color:var(--muted);">Counterparty</span><span style="font-weight:600;">' + (t.counterparty || '') + '</span></div>' +
                        '<div style="display:flex;justify-content:space-between;padding:3px 0;font-size:11px;">' +
                            '<span style="color:var(--muted);">Trigger</span><span style="font-weight:600;">' + (t.trigger || '') + '</span></div>' +
                        '<div style="display:flex;justify-content:space-between;padding:3px 0;font-size:11px;">' +
                            '<span style="color:var(--muted);">Close-Out Direction</span><span style="font-weight:700;color:' + closeDirColor + ';">' + closeDir + '</span></div>' +
                        '<div style="display:flex;justify-content:space-between;padding:3px 0;font-size:11px;">' +
                            '<span style="color:var(--muted);">Notional</span><span style="font-weight:600;">' + fmtGBP(notional) + '</span></div>' +
                        '<div style="display:flex;justify-content:space-between;padding:3px 0;font-size:11px;">' +
                            '<span style="color:var(--muted);">Tenor / Maturity</span><span style="font-weight:600;">' + (t.tenor || '') + 'Y / ' + fmtMaturity(t.maturity || '') + '</span></div>' +
                    '</div>' +

                    // Pricing — closeout spread is editable; starts blank (user must fill in)
                    '<div style="padding:12px 16px;border-bottom:1px solid var(--line-soft);">' +
                        '<div style="display:flex;justify-content:space-between;padding:3px 0;font-size:11px;">' +
                            '<span style="color:var(--muted);">Trade Spread</span>' +
                            '<span style="font-weight:600;">' + tradeSpd.toFixed(1) + ' bps</span></div>' +
                        '<div style="display:flex;justify-content:space-between;padding:3px 0;font-size:11px;">' +
                            '<span style="color:var(--muted);">Current Spread</span>' +
                            '<span style="font-weight:600;">' + fairSpd.toFixed(1) + ' bps</span></div>' +
                        '<div style="display:flex;justify-content:space-between;align-items:center;padding:3px 0;font-size:11px;">' +
                            '<span style="color:var(--muted);font-weight:700;">Closeout Spread</span>' +
                            '<span style="display:flex;align-items:center;gap:4px;">' +
                                '<input id="td-closeout-spread-input" type="number" min="0" step="0.1" ' +
                                    'style="width:72px;text-align:right;padding:3px 5px;border:2px solid var(--accent-mid);border-radius:3px;font-size:11px;font-weight:700;" ' +
                                    'placeholder="bps">' +
                                '<span style="color:var(--muted);">bps</span>' +
                            '</span></div>' +
                        '<div style="display:flex;justify-content:space-between;padding:3px 0;font-size:11px;">' +
                            '<span style="color:var(--muted);">Spread Move</span>' +
                            '<span id="td-closeout-move" style="font-weight:700;color:' + moveColor + ';">' + moveSign + spreadMove.toFixed(1) + ' bps</span></div>' +
                    '</div>' +

                    // Settlement — dynamically updated as closeout spread changes (indicative; backend confirms)
                    '<div id="td-settlement-section" style="padding:12px 16px;background:var(--warn-bg);border-bottom:1px solid var(--line-soft);">' +
                        '<div style="display:flex;justify-content:space-between;padding:3px 0;font-size:11px;">' +
                            '<span style="color:var(--muted);">Settlement Amount</span>' +
                            '<span id="td-settle-amount" style="font-size:14px;font-weight:700;color:var(--disabled);">Enter spread above</span></div>' +
                        '<div style="display:flex;justify-content:space-between;padding:3px 0;font-size:11px;">' +
                            '<span style="color:var(--muted);">Direction</span>' +
                            '<span id="td-settle-dir" style="font-weight:700;color:var(--disabled);">—</span></div>' +
                        '<div style="display:flex;justify-content:space-between;padding:3px 0;font-size:11px;">' +
                            '<span style="color:var(--muted);">Settlement Date</span><span style="font-weight:600;">T+2</span></div>' +
                        '<div style="padding-top:4px;font-size:9px;color:var(--disabled);text-align:right;">Indicative — confirmed by full revaluation on submit</div>' +
                    '</div>' +

                    // Confirm button — disabled until spread is entered
                    '<div style="padding:12px 16px;text-align:center;">' +
                        '<button id="td-closeout-confirm" disabled ' +
                            'style="padding:8px 32px;font-size:12px;font-weight:700;background:var(--faint);color:var(--inverse);border:none;border-radius:4px;cursor:not-allowed;">Confirm Close-Out</button>' +
                    '</div>';

                overlay.appendChild(modal);
                document.body.appendChild(overlay);

                // Wire up live spread input
                var spreadInput = document.getElementById('td-closeout-spread-input');
                var confirmBtn = document.getElementById('td-closeout-confirm');

                spreadInput.addEventListener('input', function() {
                    var raw = spreadInput.value.trim();
                    if (raw === '' || isNaN(parseFloat(raw)) || parseFloat(raw) < 0) {
                        document.getElementById('td-settle-amount').textContent = 'Enter spread above';
                        document.getElementById('td-settle-amount').style.color = Theme.value('disabled');
                        document.getElementById('td-settle-dir').textContent = '—';
                        document.getElementById('td-settle-dir').style.color = Theme.value('disabled');
                        document.getElementById('td-closeout-move').textContent = '—';
                        confirmBtn.disabled = true;
                        confirmBtn.style.background = Theme.value('faint');
                        confirmBtn.style.cursor = 'not-allowed';
                        return;
                    }
                    var closeoutSpd = parseFloat(raw);
                    var settle = calcSettlement(closeoutSpd);
                    var move = closeoutSpd - tradeSpd;
                    var moveC = move >= 0 ? 'var(--green-dark)' : 'var(--red-dark)';
                    var moveS = move >= 0 ? '+' : '';

                    document.getElementById('td-settle-amount').textContent = fmtGBP(settle.amount);
                    document.getElementById('td-settle-amount').style.color = Theme.value('text');
                    document.getElementById('td-settle-dir').textContent = settle.dir;
                    document.getElementById('td-settle-dir').style.color = settle.color;
                    document.getElementById('td-closeout-move').textContent = moveS + move.toFixed(1) + ' bps';
                    document.getElementById('td-closeout-move').style.color = moveC;

                    confirmBtn.disabled = false;
                    confirmBtn.style.background = Theme.value('amber-deep');
                    confirmBtn.style.cursor = 'pointer';
                });

                // Focus the spread input
                setTimeout(function() { spreadInput.focus(); }, 50);

                // Close modal handlers
                document.getElementById('td-closeout-close').addEventListener('click', function() {
                    overlay.remove();
                });
                overlay.addEventListener('click', function(e) {
                    if (e.target === overlay) overlay.remove();
                });

                // Confirm handler
                document.getElementById('td-closeout-confirm').addEventListener('click', function() {
                    var closeoutSpd = parseFloat(spreadInput.value);
                    if (isNaN(closeoutSpd) || closeoutSpd < 0) return;

                    var btn = document.getElementById('td-closeout-confirm');
                    btn.disabled = true;
                    btn.textContent = 'Closing...';

                    var url = getBaseUrl() + '/api/v1/trading/close/' + swapId;
                    window.__mkmAdminFetch(url, {
                        method: 'POST',
                        body: JSON.stringify({ closeout_spread_bps: closeoutSpd }),
                        mode: 'cors'
                    })
                    .then(function(r) { return r.json(); })
                    .then(function(result) {
                        overlay.remove();
                        if (result.status === 'success') {
                            // Show authoritative settlement from backend full revaluation
                            var settleAmt = result.settlement_amount != null
                                ? fmtGBP(result.settlement_amount) : '';
                            var settleDir = result.final_pnl != null
                                ? (result.final_pnl >= 0 ? 'Receivable' : 'Payable') : '';
                            var msg = result.message || (swapId + ' closed');
                            if (settleAmt) msg += ' — Settlement: ' + settleAmt + ' ' + settleDir;
                            if (window.showSuccess) window.showSuccess(msg);
                            // Show updated PDF if available
                            if (result.pdf_base64) {
                                if (window.GaugePDFPanel && typeof window.GaugePDFPanel.show === 'function') {
                                    window.GaugePDFPanel.show(swapId, result.pdf_base64);
                                }
                            }
                            // Reload blotter
                            loadBlotterData();
                            // Refresh main map FS01
                            if (window.refreshMainMapFS01) window.refreshMainMapFS01();
                        } else {
                            if (window.showError) window.showError(result.message || 'Close-out failed');
                        }
                    })
                    .catch(function(err) {
                        overlay.remove();
                        if (window.showError) window.showError('Close-out failed: ' + err.message);
                    });
                });
            };

            // View trade contract PDF inline
            window.tdViewContract = function(swapId) {
                if (!swapId) return;
                var url = getBaseUrl() + '/api/v1/prs/trades/' + swapId + '/pdf';
                fetch(url, {mode: 'cors'})
                    .then(function(r) {
                        if (!r.ok) throw new Error('HTTP ' + r.status);
                        return r.blob();
                    })
                    .then(function(blob) {
                        // Convert to base64 for inline display
                        var reader = new FileReader();
                        reader.onload = function() {
                            var base64 = reader.result.split(',')[1];
                            if (window.GaugePDFPanel && typeof window.GaugePDFPanel.show === 'function') {
                                window.GaugePDFPanel.show(swapId, base64);
                            } else if (window.PropertyPDFPanel && typeof window.PropertyPDFPanel.show === 'function') {
                                window.PropertyPDFPanel.show(swapId, base64);
                            } else {
                                // Fallback: open in new tab
                                window.open(URL.createObjectURL(blob), '_blank');
                            }
                        };
                        reader.readAsDataURL(blob);
                    })
                    .catch(function(err) {
                        console.error('[Blotter] Contract PDF error:', err);
                        if (window.showError) window.showError('Contract PDF not available for ' + swapId);
                    });
            };
