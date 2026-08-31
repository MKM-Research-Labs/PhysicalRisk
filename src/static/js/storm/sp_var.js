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

            var spVarData = null;
            var spVarChart = null;
            var spVarMode = 'property';

            // ================================================================
            // VaR tab — DOM creation
            // ================================================================
            function createVarView() {
                var view = document.createElement('div');
                view.id = 'sp-var-view';
                view.style.cssText = 'display:none;flex-direction:column;flex:1;overflow:hidden;';

                var toggleRow = document.createElement('div');
                toggleRow.style.cssText = 'padding:var(--space-4) var(--space-8);border-bottom:1px solid var(--line-soft);display:flex;align-items:center;gap:var(--space-6);background:var(--raised);';
                var toggleLabel = document.createElement('span');
                toggleLabel.textContent = 'Distribution:';
                toggleLabel.style.cssText = 'font-size:var(--size-sm);font-weight:600;color:var(--text-2);';
                var toggleWrap = document.createElement('div');
                toggleWrap.style.cssText = 'display:flex;border:1px solid var(--line-strong);border-radius:var(--radius-4);overflow:hidden;';
                var propBtn = document.createElement('button');
                propBtn.id = 'sp-var-prop-btn';
                propBtn.textContent = 'Property Damage';
                propBtn.style.cssText = 'padding:var(--space-2) var(--space-7);font-size:var(--size-xs);border:none;cursor:pointer;background:var(--accent);color:var(--inverse);';
                propBtn.onclick = function() { switchVarMode('property'); };
                var mortBtn = document.createElement('button');
                mortBtn.id = 'sp-var-mort-btn';
                mortBtn.textContent = 'Mortgage Impairment';
                mortBtn.style.cssText = 'padding:var(--space-2) var(--space-7);font-size:var(--size-xs);border:none;cursor:pointer;background:var(--panel);color:var(--text);';
                mortBtn.onclick = function() { switchVarMode('mortgage'); };
                toggleWrap.appendChild(propBtn);
                toggleWrap.appendChild(mortBtn);
                toggleRow.appendChild(toggleLabel);
                toggleRow.appendChild(toggleWrap);

                var chartWrap = document.createElement('div');
                chartWrap.id = 'sp-var-chart-wrap';
                chartWrap.style.cssText = 'flex:1;padding:var(--space-6) var(--space-8);position:relative;';

                var metrics = document.createElement('div');
                metrics.id = 'sp-var-metrics';
                metrics.style.cssText = 'padding:var(--space-5) var(--space-8);border-top:1px solid var(--line-soft);display:flex;gap:var(--space-5);flex-wrap:wrap;';

                view.appendChild(toggleRow);
                view.appendChild(chartWrap);
                view.appendChild(metrics);
                return view;
            }

            // ================================================================
            // VaR mode switching
            // ================================================================
            function switchVarMode(mode) {
                spVarMode = mode;
                var propBtn = document.getElementById('sp-var-prop-btn');
                var mortBtn = document.getElementById('sp-var-mort-btn');
                if (mode === 'property') {
                    propBtn.style.background = Theme.value('accent');
                    propBtn.style.color = Theme.value('panel');
                    mortBtn.style.background = Theme.value('panel');
                    mortBtn.style.color = Theme.value('text');
                } else {
                    mortBtn.style.background = Theme.value('purple');
                    mortBtn.style.color = Theme.value('panel');
                    propBtn.style.background = Theme.value('panel');
                    propBtn.style.color = Theme.value('text');
                }
                if (spVarData) {
                    renderVarChart(spVarData, mode);
                    renderVarMetrics(spVarData, mode);
                }
            }

            function renderVarMetrics(data, mode) {
                if (!mode) mode = spVarMode;
                var metrics = document.getElementById('sp-var-metrics');
                var isProp = mode === 'property';
                var d = isProp ? data.property_damage : data.mortgage_impairment;
                var labelColor = isProp ? 'var(--accent)' : 'var(--purple)';
                var label = isProp ? 'Property Damage' : 'Mortgage Impairment';
                metrics.innerHTML = '';

                var probRow = document.createElement('div');
                probRow.style.cssText = 'width:100%;padding:var(--space-3) var(--space-5);margin-bottom:var(--space-3);font-size:var(--size-xs);color:var(--text-2);background:var(--bg);border-radius:var(--radius-4);';
                probRow.innerHTML = 'P(loss) = <b>' + data.prob_loss_pct.toFixed(2) + '%</b> (' + data.storms_with_damage + ' of ' + data.storm_count.toLocaleString() + ' storms)' +
                    ' &mdash; Conditional metrics below given a damaging storm occurs';
                metrics.appendChild(probRow);

                var row = document.createElement('div');
                row.style.cssText = 'display:flex;gap:var(--space-4);width:100%;';
                var lbl = document.createElement('div');
                lbl.style.cssText = 'min-width:130px;padding:var(--space-4) var(--space-5);font-size:var(--size-xs);font-weight:700;color:' + labelColor + ';display:flex;align-items:center;';
                lbl.textContent = label;
                row.appendChild(lbl);
                [
                    { label: 'Cond. Mean', value: fmtGBP(d.cond_mean), color: labelColor },
                    { label: 'VaR 95%', value: fmtGBP(d.cond_var_95), color: 'var(--amber)' },
                    { label: 'VaR 99.9%', value: fmtGBP(d.cond_var_999), color: 'var(--red)' },
                    { label: 'ES 95%', value: fmtGBP(d.cond_es_95), color: 'var(--amber)' },
                    { label: 'ES 99.9%', value: fmtGBP(d.cond_es_999), color: 'var(--red)' },
                    { label: 'Max', value: fmtGBP(d.max), color: 'var(--purple)' },
                ].forEach(function(c) {
                    var card = document.createElement('div');
                    card.style.cssText = 'flex:1;padding:var(--space-4) var(--space-5);border-radius:var(--radius-md);background:var(--sunken);border-left:3px solid ' + c.color + ';';
                    card.innerHTML = '<div style="font-size:var(--size-xxs);color:var(--muted);text-transform:uppercase;">' + c.label + '</div>' +
                        '<div style="font-size:var(--size-14);font-weight:700;color:' + c.color + ';">' + c.value + '</div>';
                    card.appendChild(document.createElement('div'));
                    row.appendChild(card);
                });
                metrics.appendChild(row);
            }

            // ================================================================
            // VaR data loading
            // ================================================================
            function loadVarData() {
                console.log('[StormPortfolio] Fetching VaR distribution');
                var statsBar = document.getElementById('sp-stats-bar');
                statsBar.innerHTML = '<span>Loading VaR distribution...</span>';
                var wrap = document.getElementById('sp-var-chart-wrap');
                // Keep a canvas in the DOM from the start so downstream tests and
                // chart-init code always find #sp-var-canvas, even during loading
                // or when the backend returns an empty/erroring payload.
                wrap.innerHTML = '<canvas id="sp-var-canvas"></canvas>' +
                    '<div id="sp-var-status" style="padding:var(--space-4);text-align:center;color:var(--muted);font-size:var(--size-xs);">Loading VaR data…</div>';
                var metrics = document.getElementById('sp-var-metrics');
                metrics.innerHTML = '<span style="font-size:var(--size-xxs);color:var(--muted);">VaR: loading…</span>';

                var baseUrl = getBaseUrl();
                fetch(baseUrl + '/api/v1/propertyts/portfolio-var', {mode: 'cors'})
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        if (data.status !== 'success') {
                            var statusEl = document.getElementById('sp-var-status');
                            if (statusEl) statusEl.innerHTML = '<span style="color:var(--red-dark);">Error loading VaR: ' + (data.message || 'Unknown') + '</span>';
                            metrics.innerHTML = '<span style="font-size:var(--size-xxs);color:var(--red-dark);">VaR unavailable — ' + (data.message || 'no data') + '</span>';
                            return;
                        }
                        spVarData = data;
                        console.log('[StormPortfolio] VaR loaded:', data.storm_count, 'storms,', data.storms_with_damage, 'with damage');
                        document.getElementById('sp-panel-title').textContent =
                            'Portfolio VaR — Loss Distribution';

                        renderVarChart(data, spVarMode);
                        renderVarMetrics(data, spVarMode);

                        statsBar.innerHTML =
                            '<span>Scenarios: <b>' + data.storm_count.toLocaleString() + '</b> storms</span>' +
                            '<span>Damaging: <b>' + data.storms_with_damage + '</b></span>' +
                            '<span>Portfolio value: <b>' + fmtGBP(data.total_portfolio_value) + '</b></span>' +
                            '<span>Portfolio mortgages: <b>' + fmtGBP(data.total_portfolio_mortgages) + '</b></span>';
                    })
                    .catch(function(err) {
                        wrap.innerHTML = '<div style="padding:var(--space-inset);text-align:center;color:var(--red);">Failed to load VaR data</div>';
                        console.error('VaR error:', err);
                    });
            }
