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

        <script>
        (function() {{
            var PANEL_W = '{panel_width}';
            var PANEL_H = '{panel_height}';
            var lpPanel = null;
            var currentAssetId = null;
            // standaloneMode = true when launched as the asset-independent
            // "Loan Calculator": no asset is loaded; the user types every
            // input and re-pricing POSTs to the standalone endpoint.
            var standaloneMode = false;
            // 'residential' | 'commercial' — commercial caps the term at 7y
            // server-side and is sent as asset_class on the standalone POST.
            var standaloneAssetClass = 'residential';
            // The asset the calculator was launched from (if any). The
            // standalone calculator prices asset-independently, but when it
            // was opened from a property/commercial marker we keep that id so
            // the flood leg can deep-link to that asset's PRS pricer panel.
            var standaloneOriginAssetId = null;
            // The origin asset's own modelled flood PRS spread (bps), read
            // from its hazard curve. When set, it drives the flood leg of the
            // coupon instead of the coarse flood-category lookup, so the
            // calculator matches the property PRS pricer. null = use category.
            var assetFloodSpreadBps = null;
            // The origin asset's modelled combined flood-OR-wind PRS spread
            // (the union, bps), read from the same hazard curve when the
            // catchment has a coupled typhoon stage. When set, the wind leg is
            // PRS-priced as the incremental hazard on top of flood
            // (union - flood). null = no wind curve -> wind stays on the static
            // category lookup (flood-only catchments).
            var assetUnionSpreadBps = null;
            // The origin asset's full PRS scenario fan, in bps, read from the
            // hazard curve: flo (raw flood), bri (flood with BRI resilience),
            // win (wind only), faw (flood AND wind), fow (flood OR wind). The
            // calculator's PRS-scenario dropdown picks one of these to drive the
            // coupon's single hazard leg. Any entry left null (scenario absent
            // for this asset/catchment) makes that menu choice fall back to the
            // legacy flood+wind category lookup server-side.
            var assetScenarioSpreads = {{flo: null, bri: null, win: null, faw: null, fow: null, baw: null, bow: null}};
            // The origin asset's independent-peril legs (bps), read from the
            // hazard curve's spread_decomposition. Fire and seismic are toggled
            // on/off by the calculator's peril buttons; when on, each leg is
            // folded into the all-in coupon by root-sum-of-squares. null = the
            // asset has no such leg (no fire/seismic model run) -> button stays
            // disabled.
            var assetFireSpreadBps = null;
            var assetSeismicSpreadBps = null;
            // Borrower income sourced from the origin asset. Commercial markers
            // forward the asset's net initial yield (passing rent / value) so
            // the server can derive income = yield x property value; residential
            // markers forward the borrower's gross annual income directly. Both
            // null = use the STANDALONE_DEFAULTS income.
            var assetIncomeYield = null;
            var assetGrossIncome = null;

            // Sensible starting values for the standalone calculator so the
            // first price renders immediately. pct fields are stored as
            // decimals (populateInputs multiplies by 100 for display). Note
            // there is no interest_rate here: the contractual coupon is built
            // up server-side from the credit rating + flood/wind hazard.
            var STANDALONE_DEFAULTS = {{
                loan_amount: 7500000,
                property_value: 10000000,
                gross_annual_income: 50000,
                insurance_rate: 0.002,
                recovery_haircut: 0.2,
                original_maturity: 30,
                current_term: 30,
                credit_rating: 'BBB',
                prs_scenario: 'fow'
            }};

            // field id -> {{label, kind}}. kind 'pct' fields are stored on the
            // server as decimals but shown to the user as percentages.
            var FIELDS = [
                {{id: 'lp-loan_amount',        label: 'Outstanding Balance', kind: 'num'}},
                {{id: 'lp-property_value',     label: 'Property Value',      kind: 'num'}},
                {{id: 'lp-gross_annual_income',label: 'Borrower Income',     kind: 'num'}},
                {{id: 'lp-interest_rate',      label: 'Interest Rate (%)',   kind: 'pct'}},
                {{id: 'lp-insurance_rate',     label: 'Insurance Rate (%)',  kind: 'pct'}},
                {{id: 'lp-recovery_haircut',   label: 'Recovery Haircut (%)',kind: 'pct'}},
                {{id: 'lp-original_maturity',  label: 'Original Term (yrs)', kind: 'num'}},
                {{id: 'lp-current_term',       label: 'Remaining Term (yrs)',kind: 'num'}}
            ];
            var CREDIT_RATINGS = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC'];
            // PRS hazard scenarios offered by the dropdown. The chosen scenario's
            // modelled spread becomes the coupon's single hazard leg. 'fow'
            // (flood OR wind) is the default so the calculator opens on the full
            // combined peril, matching the prior flood+wind behaviour.
            var PRS_SCENARIOS = [
                {{value: 'flo', label: 'Flood only'}},
                {{value: 'bri', label: 'Flood only + BRI resilience'}},
                {{value: 'win', label: 'Wind only'}},
                {{value: 'faw', label: 'Flood AND wind'}},
                {{value: 'fow', label: 'Flood OR wind (combined)'}},
                {{value: 'baw', label: 'BRI AND wind'}},
                {{value: 'bow', label: 'BRI OR wind (resilient combined)'}}
            ];

            function createPanel() {{
                if (lpPanel) return lpPanel;

                lpPanel = document.createElement('div');
                lpPanel.id = 'loan-pricer-panel';
                lpPanel.style.cssText =
                    'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);' +
                    'width:' + PANEL_W + ';height:' + PANEL_H + ';' +
                    'background:var(--panel);border:1px solid var(--divider);border-radius:var(--radius-lg);' +
                    'box-shadow:var(--shadow-toast);z-index:2000;' +
                    'display:none;flex-direction:column;font-family:Arial,sans-serif;';

                var header = document.createElement('div');
                header.style.cssText =
                    'display:flex;justify-content:space-between;align-items:center;' +
                    'padding:var(--space-5) var(--space-8);border-bottom:1px solid var(--line-soft);background:var(--wash);' +
                    'border-radius:var(--radius-lg) var(--radius-lg) 0 0;';

                var title = document.createElement('span');
                title.id = 'loan-pricer-title';
                title.style.cssText = 'font-weight:bold;font-size:var(--size-14);color:var(--text);';

                var closeBtn = document.createElement('button');
                closeBtn.innerHTML = '&times;';
                closeBtn.style.cssText =
                    'border:none;background:none;font-size:var(--size-24);cursor:pointer;' +
                    'color:var(--text-3);padding:0 var(--space-4);line-height:1;';
                closeBtn.onclick = hidePanel;

                header.appendChild(title);
                header.appendChild(closeBtn);

                var body = document.createElement('div');
                body.style.cssText = 'flex:1;display:flex;overflow:hidden;';

                // Left: editable inputs
                var form = document.createElement('div');
                form.id = 'loan-pricer-form';
                form.style.cssText =
                    'width:46%;padding:var(--space-6) var(--space-8);overflow-y:auto;font-size:var(--size-md);' +
                    'border-right:1px solid var(--line-soft);';

                // Right: pricing results
                var results = document.createElement('div');
                results.id = 'loan-pricer-results';
                results.style.cssText = 'flex:1;padding:var(--space-6) var(--space-8);overflow-y:auto;font-size:var(--size-md);';

                body.appendChild(form);
                body.appendChild(results);

                lpPanel.appendChild(header);
                lpPanel.appendChild(body);
                document.body.appendChild(lpPanel);

                document.addEventListener('keydown', function(e) {{
                    if (e.key === 'Escape' && lpPanel.style.display !== 'none') hidePanel();
                }});

                return lpPanel;
            }}

            function hidePanel() {{
                if (lpPanel) lpPanel.style.display = 'none';
                console.log('[LoanPricer] Panel closed');
            }}

            function fmtCurrency(v) {{
                if (typeof v !== 'number' || isNaN(v)) return 'N/A';
                return 'USD ' + v.toLocaleString('en-US', {{maximumFractionDigits: 0}});
            }}

            function fmtPct(v) {{
                if (typeof v !== 'number' || isNaN(v)) return 'N/A';
                return (v * 100).toFixed(2) + '%';
            }}

            function fmtNum(v, dp) {{
                if (typeof v !== 'number' || isNaN(v)) return 'N/A';
                return v.toFixed(dp === undefined ? 2 : dp);
            }}

            // Build a labelled <select> as an HTML string.
