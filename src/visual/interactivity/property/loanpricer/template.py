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
Loan Pricer panel - client-side JavaScript template.

Holds the (large) JS/HTML body for the Loan Pricer popup as a ``str.format``
template. Literal JavaScript braces are DOUBLED (``{{`` / ``}}``) so that
``.format()`` leaves them intact; the only substituted placeholders are
``{panel_width}`` and ``{panel_height}``, supplied by
:class:`~visual.interactivity.property.loanpricer.panel.LoanPricerPanel`.
"""

LOAN_PRICER_JS_TEMPLATE = """
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
                wind_risk_category: 'Medium',
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
            var WIND_OPTIONS = ['Very low', 'Low', 'Medium', 'High', 'Very high'];
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
                    'background:white;border:1px solid #ccc;border-radius:8px;' +
                    'box-shadow:0 4px 20px rgba(0,0,0,0.3);z-index:2000;' +
                    'display:none;flex-direction:column;font-family:Arial,sans-serif;';

                var header = document.createElement('div');
                header.style.cssText =
                    'display:flex;justify-content:space-between;align-items:center;' +
                    'padding:10px 16px;border-bottom:1px solid #eee;background:#f8f9fa;' +
                    'border-radius:8px 8px 0 0;';

                var title = document.createElement('span');
                title.id = 'loan-pricer-title';
                title.style.cssText = 'font-weight:bold;font-size:14px;color:#333;';

                var closeBtn = document.createElement('button');
                closeBtn.innerHTML = '&times;';
                closeBtn.style.cssText =
                    'border:none;background:none;font-size:24px;cursor:pointer;' +
                    'color:#666;padding:0 8px;line-height:1;';
                closeBtn.onclick = hidePanel;

                header.appendChild(title);
                header.appendChild(closeBtn);

                var body = document.createElement('div');
                body.style.cssText = 'flex:1;display:flex;overflow:hidden;';

                // Left: editable inputs
                var form = document.createElement('div');
                form.id = 'loan-pricer-form';
                form.style.cssText =
                    'width:46%;padding:12px 16px;overflow-y:auto;font-size:13px;' +
                    'border-right:1px solid #eee;';

                // Right: pricing results
                var results = document.createElement('div');
                results.id = 'loan-pricer-results';
                results.style.cssText = 'flex:1;padding:12px 16px;overflow-y:auto;font-size:13px;';

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
            function selectHtml(id, label, options) {{
                var h = '<div style="margin-bottom:6px;">' +
                    '<label style="display:block;color:#666;font-size:11px;margin-bottom:2px;">' +
                    label + '</label>' +
                    '<select id="' + id + '" ' +
                    'style="width:100%;box-sizing:border-box;padding:4px 6px;' +
                    'border:1px solid #ccc;border-radius:4px;font-size:13px;">';
                options.forEach(function(o) {{
                    // Accept either a plain string (value === text) or a
                    // {{value, label}} object so the same helper builds both the
                    // category selects and the PRS-scenario selector.
                    var val = (o && o.value !== undefined) ? o.value : o;
                    var txt = (o && o.label !== undefined) ? o.label : o;
                    h += '<option value="' + val + '">' + txt + '</option>';
                }});
                return h + '</select></div>';
            }}

            function buildForm() {{
                var form = document.getElementById('loan-pricer-form');
                var html = '<div style="font-weight:700;font-size:12px;color:#1565C0;' +
                    'border-bottom:1px solid #BBDEFB;padding-bottom:4px;margin-bottom:8px;">' +
                    'Loan Inputs</div>';
                FIELDS.forEach(function(f) {{
                    // In standalone mode the coupon is derived (rating + hazard),
                    // so the contractual rate isn't a free input.
                    if (standaloneMode && f.id === 'lp-interest_rate') return;
                    html += '<div style="margin-bottom:6px;">' +
                        '<label style="display:block;color:#666;font-size:11px;margin-bottom:2px;">' +
                        f.label + '</label>' +
                        '<input id="' + f.id + '" type="number" step="any" ' +
                        'style="width:100%;box-sizing:border-box;padding:4px 6px;' +
                        'border:1px solid #ccc;border-radius:4px;font-size:13px;"></div>';
                }});
                // Standalone calculator exposes the coupon build-up drivers:
                // borrower credit rating + wind hazard category. The flood leg
                // is driven by the asset's own modelled PRS spread (or the
                // server-side category fallback), so it has no input here.
                if (standaloneMode) {{
                    html += selectHtml('lp-credit_rating', 'Borrower Credit Rating', CREDIT_RATINGS);
                    html += selectHtml('lp-wind_risk_category', 'Wind Risk Category', WIND_OPTIONS);
                    // PRS hazard scenario: which modelled peril spread drives
                    // the coupon's hazard leg. Only meaningful when launched
                    // from an asset (its fan supplies the spreads); otherwise
                    // the chosen scenario falls back to the category lookup.
                    html += selectHtml('lp-prs_scenario', 'PRS Hazard Scenario', PRS_SCENARIOS);
                }}
                html += '<button id="lp-reprice-btn" ' +
                    'style="width:100%;margin-top:4px;padding:8px;background:#1565C0;color:white;' +
                    'border:none;border-radius:4px;font-size:13px;font-weight:600;cursor:pointer;">' +
                    'Re-price</button>';
                form.innerHTML = html;
                document.getElementById('lp-reprice-btn').onclick = reprice;
            }}

            function populateInputs(inputs) {{
                inputs = inputs || {{}};
                FIELDS.forEach(function(f) {{
                    var key = f.id.replace('lp-', '');
                    var v = inputs[key];
                    var el = document.getElementById(f.id);
                    if (el == null) return;
                    if (v == null) {{ el.value = ''; return; }}
                    el.value = (f.kind === 'pct') ? (v * 100) : v;
                }});
                var wr = document.getElementById('lp-wind_risk_category');
                if (wr && inputs.wind_risk_category) wr.value = inputs.wind_risk_category;
                var cr = document.getElementById('lp-credit_rating');
                if (cr && inputs.credit_rating) cr.value = inputs.credit_rating;
                var ps = document.getElementById('lp-prs_scenario');
                if (ps && inputs.prs_scenario) ps.value = inputs.prs_scenario;
            }}

            function readOverrides() {{
                var ov = {{}};
                FIELDS.forEach(function(f) {{
                    var el = document.getElementById(f.id);
                    if (!el || el.value === '') return;
                    var num = parseFloat(el.value);
                    if (isNaN(num)) return;
                    var key = f.id.replace('lp-', '');
                    ov[key] = (f.kind === 'pct') ? (num / 100) : num;
                }});
                var wr = document.getElementById('lp-wind_risk_category');
                if (wr && wr.value) ov.wind_risk_category = wr.value;
                var cr = document.getElementById('lp-credit_rating');
                if (cr && cr.value) ov.credit_rating = cr.value;
                var ps = document.getElementById('lp-prs_scenario');
                if (ps && ps.value) ov.prs_scenario = ps.value;
                return ov;
            }}

            function renderResults(data) {{
                var p = (data && data.pricing) || {{}};
                var rows = [
                    ['Fair Value', fmtCurrency(p.mortgage_value), '#1B5E20'],
                    ['Discount to Par', fmtCurrency(p.discount_to_par), '#C62828'],
                    ['Discount %', fmtNum(p.discount_percentage, 2) + '%', '#C62828'],
                    ['Discount Rate', fmtPct(p.discount_rate), '#333'],
                    ['LTV Ratio', fmtPct(p.ltv_ratio), '#333'],
                    ['Monthly Payment', fmtCurrency(p.monthly_payment), '#333'],
                    ['Annual Payment', fmtCurrency(p.annual_payment), '#333'],
                    ['PV Cashflows', fmtCurrency(p.pv_cashflows), '#333'],
                    ['PV Losses', fmtCurrency(p.pv_losses), '#333']
                ];
                var html = '';
                // Coupon build-up (standalone calculator only): show how the
                // contractual coupon decomposes into risk-free + credit + hazard.
                var c = data && data.coupon;
                if (c) {{
                    // The flood leg is PRS-priced; the label notes whether it
                    // came from the asset's own hazard curve or the category
                    // fallback. When opened from an asset, deep-link the leg to
                    // that asset's PRS pricer panel so the user can drill in.
                    var fromAsset = (c.flood_priced_by || '').indexOf('asset') >= 0;
                    var floodLabel = fromAsset
                        ? 'Flood Hazard (PRS \\u00b7 asset curve)'
                        : 'Flood Hazard (PRS \\u00b7 category)';
                    if (standaloneOriginAssetId && window.viewPropertyHazard) {{
                        floodLabel += ' <a href="#" id="lp-flood-prs-link" ' +
                            'style="color:#1565C0;text-decoration:underline;font-size:11px;" ' +
                            'title="Open the PRS pricer for this asset">&#8599; PRS pricer</a>';
                    }}
                    // The wind leg is either PRS-priced from the asset's modelled
                    // union (incremental flood OR wind) or, for flood-only assets,
                    // the static wind-category lookup. Label it accordingly.
                    var windFromUnion = (c.wind_priced_by || '').indexOf('union') >= 0;
                    var windLabel = windFromUnion
                        ? 'Wind Hazard (PRS \\u00b7 combined)'
                        : 'Wind Hazard (static)';
                    var couponRows = [
                        ['Contractual Coupon', fmtPct(c.rate), '#0D47A1'],
                        ['Risk-free (curve)', fmtPct(c.risk_free), '#333'],
                        ['Credit Spread (' + (c.credit_rating || '') + ')', fmtPct(c.credit_spread), '#333']
                    ];
                    // When the user picked a PRS scenario the coupon carries a
                    // single hazard leg (that scenario's modelled spread); show
                    // it as one labelled row. Otherwise fall back to the legacy
                    // flood + wind two-leg decomposition.
                    if (c.prs_scenario) {{
                        var SCEN_LABELS = {{
                            flo: 'Flood only', bri: 'Flood only \\u00b7 BRI resilience',
                            win: 'Wind only', faw: 'Flood AND wind',
                            fow: 'Flood OR wind (combined)'
                        }};
                        var scLabel = SCEN_LABELS[c.prs_scenario] || c.prs_scenario;
                        var prsLabel = 'PRS Hazard (' + scLabel + ')';
                        if (standaloneOriginAssetId && window.viewPropertyHazard) {{
                            prsLabel += ' <a href="#" id="lp-flood-prs-link" ' +
                                'style="color:#1565C0;text-decoration:underline;font-size:11px;" ' +
                                'title="Open the PRS pricer for this asset">&#8599; PRS pricer</a>';
                        }}
                        couponRows.push([prsLabel, fmtPct(c.hazard_spread), '#333']);
                    }} else {{
                        couponRows.push([floodLabel, fmtPct(c.flood_spread), '#333']);
                        couponRows.push([windLabel, fmtPct(c.wind_spread), '#333']);
                    }}
                    html += '<div style="font-weight:700;font-size:12px;color:#1565C0;' +
                        'border-bottom:1px solid #BBDEFB;padding-bottom:4px;margin-bottom:8px;">' +
                        'Coupon Build-up</div>';
                    couponRows.forEach(function(r) {{
                        html += '<div style="display:flex;justify-content:space-between;padding:3px 0;' +
                            'border-bottom:1px solid #f5f5f5;">' +
                            '<span style="color:#666;">' + r[0] + '</span>' +
                            '<span style="font-weight:600;color:' + r[2] + ';">' + r[1] + '</span></div>';
                    }});
                    html += '<div style="height:12px;"></div>';
                }}
                html += '<div style="font-weight:700;font-size:12px;color:#1565C0;' +
                    'border-bottom:1px solid #BBDEFB;padding-bottom:4px;margin-bottom:8px;">' +
                    'Pricing Results</div>';
                rows.forEach(function(r) {{
                    html += '<div style="display:flex;justify-content:space-between;padding:3px 0;' +
                        'border-bottom:1px solid #f5f5f5;">' +
                        '<span style="color:#666;">' + r[0] + '</span>' +
                        '<span style="font-weight:600;color:' + r[2] + ';">' + r[1] + '</span></div>';
                }});
                document.getElementById('loan-pricer-results').innerHTML = html;
                // Wire the flood leg's PRS deep-link (added above only when the
                // calculator was launched from an asset). Uses a listener rather
                // than inline onclick to keep the id out of the HTML string.
                var floodLink = document.getElementById('lp-flood-prs-link');
                if (floodLink && standaloneOriginAssetId && window.viewPropertyHazard) {{
                    floodLink.onclick = function(ev) {{
                        ev.preventDefault();
                        window.viewPropertyHazard(standaloneOriginAssetId);
                        return false;
                    }};
                }}
            }}

            function endpointFor(assetId) {{
                var cfg = window.__BACKEND_CONFIG || {{}};
                var baseUrl = cfg.url || '';
                var path = (assetId.indexOf('CPROP-') === 0)
                    ? '/api/v1/commercial/' : '/api/v1/properties/';
                return baseUrl + path + assetId + '/loan-pricer';
            }}

            function standaloneEndpoint() {{
                var cfg = window.__BACKEND_CONFIG || {{}};
                return (cfg.url || '') + '/api/v1/loan-pricer';
            }}

            // Hazard endpoint for the asset the calculator was launched from.
            // Commercial assets (CPROP- prefix) use the commercial route.
            function hazardEndpointFor(assetId) {{
                var cfg = window.__BACKEND_CONFIG || {{}};
                var baseUrl = cfg.url || '';
                var path = (assetId.indexOf('CPROP-') === 0)
                    ? '/api/v1/commercial/' : '/api/v1/properties/';
                return baseUrl + path + assetId + '/hazard';
            }}

            // Read the origin asset's own modelled flood PRS spread (severe
            // trigger, bps) from its hazard curve. The spread is flat across
            // tenors (storms are independent), so the first point is taken.
            // Sets assetFloodSpreadBps; leaves it null on any miss (e.g. the
            // asset has < 3 flood events and so has no hazard curve), in which
            // case the coupon falls back to the flood-category lookup.
            //
            // BRI preference: when the asset has a Building Resilience Index
            // curve, the loan's flood leg is priced on the BRI-adjusted
            // (resilient) spread instead of the pure surveyed-floor spread.
            // Raising the effective flood floor removes severe floods, so the
            // resilient spread is lower — the borrower gets the credit for the
            // building's resilience in their coupon. spread_decomposition.
            // bri_spread_bps is flat across tenors (same construction as
            // prs_spread_bps), so it is directly comparable to the first point.
            async function loadAssetFloodSpread() {{
                assetFloodSpreadBps = null;
                assetUnionSpreadBps = null;
                assetScenarioSpreads = {{flo: null, bri: null, win: null, faw: null, fow: null}};
                if (!standaloneOriginAssetId) return;
                try {{
                    var resp = await fetch(hazardEndpointFor(standaloneOriginAssetId),
                                           {{mode: 'cors'}});
                    if (!resp.ok) return;
                    var body = await resp.json();
                    var d = body && body.data;
                    var ts = d && d.term_structure;
                    var severe = ts && ts.severe;
                    var arr = severe && severe.prs_spread_bps;
                    if (arr && arr.length && arr[0] != null && !isNaN(arr[0])) {{
                        assetFloodSpreadBps = parseFloat(arr[0]);
                        // Raw surveyed-floor flood spread (flo scenario).
                        assetScenarioSpreads.flo = assetFloodSpreadBps;
                    }}
                    // Combined flood-OR-wind PRS (the union) — present only when
                    // the catchment has a coupled typhoon stage. Flat across
                    // tenors, so the first point is taken. Absent for flood-only
                    // catchments, leaving assetUnionSpreadBps null (wind stays
                    // on the static category lookup).
                    var perils = ts && ts.perils;
                    var fow = perils && perils.flood_or_wind;
                    var uarr = fow && fow.prs_spread_bps;
                    if (uarr && uarr.length && uarr[0] != null && !isNaN(uarr[0])) {{
                        assetUnionSpreadBps = parseFloat(uarr[0]);
                    }}
                    // Prefer the BRI-adjusted (resilient) spread when present.
                    var sd = d && d.spread_decomposition;
                    var briBps = sd && sd.bri_spread_bps;
                    if (briBps != null && !isNaN(briBps)) {{
                        assetFloodSpreadBps = parseFloat(briBps);
                        assetScenarioSpreads.bri = parseFloat(briBps);
                    }}
                    // Peril fan scalars (Option A): wind-only, flood-AND-wind,
                    // flood-OR-wind. Each is the canonical scenario spread read
                    // from the win/faw/fow hazard files via the decomposition.
                    if (sd && sd.win_spread_bps != null && !isNaN(sd.win_spread_bps)) {{
                        assetScenarioSpreads.win = parseFloat(sd.win_spread_bps);
                    }}
                    if (sd && sd.faw_spread_bps != null && !isNaN(sd.faw_spread_bps)) {{
                        assetScenarioSpreads.faw = parseFloat(sd.faw_spread_bps);
                    }}
                    if (sd && sd.fow_spread_bps != null && !isNaN(sd.fow_spread_bps)) {{
                        assetScenarioSpreads.fow = parseFloat(sd.fow_spread_bps);
                    }}
                    // BRI-anchored peril scalars: BRI-AND-wind and BRI-OR-wind.
                    // Same union/intersection as faw/fow but on the resilient
                    // (BRI-adjusted) flood leg rather than the raw asset flood.
                    if (sd && sd.baw_spread_bps != null && !isNaN(sd.baw_spread_bps)) {{
                        assetScenarioSpreads.baw = parseFloat(sd.baw_spread_bps);
                    }}
                    if (sd && sd.bow_spread_bps != null && !isNaN(sd.bow_spread_bps)) {{
                        assetScenarioSpreads.bow = parseFloat(sd.bow_spread_bps);
                    }}
                    // Prefer the BRI-adjusted union (peril outcomes are attached
                    // to the decomposition from the BRI node) to stay consistent
                    // with the BRI-preferred flood leg above.
                    var po = sd && sd.peril_outcomes;
                    var pou = po && po.flood_or_wind;
                    var pouBps = pou && pou.spread_bps;
                    if (pouBps != null && !isNaN(pouBps)) {{
                        assetUnionSpreadBps = parseFloat(pouBps);
                        if (assetScenarioSpreads.fow == null) {{
                            assetScenarioSpreads.fow = parseFloat(pouBps);
                        }}
                    }}
                    // Fall back to the peril-fan scalars for win/faw too, so the
                    // dropdown is populated even on payloads that carry only the
                    // peril_outcomes block (not the flat *_spread_bps mirrors).
                    if (po) {{
                        var pw = po.wind_only && po.wind_only.spread_bps;
                        if (assetScenarioSpreads.win == null && pw != null && !isNaN(pw)) {{
                            assetScenarioSpreads.win = parseFloat(pw);
                        }}
                        var pfaw = po.flood_and_wind && po.flood_and_wind.spread_bps;
                        if (assetScenarioSpreads.faw == null && pfaw != null && !isNaN(pfaw)) {{
                            assetScenarioSpreads.faw = parseFloat(pfaw);
                        }}
                        var pbaw = po.bri_and_wind && po.bri_and_wind.spread_bps;
                        if (assetScenarioSpreads.baw == null && pbaw != null && !isNaN(pbaw)) {{
                            assetScenarioSpreads.baw = parseFloat(pbaw);
                        }}
                        var pbow = po.bri_or_wind && po.bri_or_wind.spread_bps;
                        if (assetScenarioSpreads.bow == null && pbow != null && !isNaN(pbow)) {{
                            assetScenarioSpreads.bow = parseFloat(pbow);
                        }}
                    }}
                }} catch (e) {{
                    console.warn('[LoanPricer] asset flood spread unavailable', e);
                }}
            }}

            // Backend endpoint for the origin asset's full commercial record
            // (CommercialAsset wrapper intact) — used to read the net initial
            // yield for the income derivation.
            function commercialRecordEndpoint(assetId) {{
                var cfg = window.__BACKEND_CONFIG || {{}};
                return (cfg.url || '') + '/api/v1/commercial/' + assetId;
            }}

            // Backend endpoint for the origin asset's linked loan pricer (GET) —
            // its derived inputs carry the residential borrower's income.
            function loanPricerEndpointFor(assetId) {{
                var cfg = window.__BACKEND_CONFIG || {{}};
                return (cfg.url || '') + '/api/v1/properties/' + assetId + '/loan-pricer';
            }}

            // Source the borrower income from the origin asset (if any).
            // Commercial: read the asset's net initial yield (passing rent /
            // capital value) so the server derives income = yield x property
            // value. Residential: read the borrower's gross annual income from
            // the linked loan record. Leaves both null on any miss, in which
            // case the calculator keeps the STANDALONE_DEFAULTS income.
            async function loadAssetIncome() {{
                assetIncomeYield = null;
                assetGrossIncome = null;
                if (!standaloneOriginAssetId) return;
                try {{
                    if (standaloneAssetClass === 'commercial') {{
                        var resp = await fetch(
                            commercialRecordEndpoint(standaloneOriginAssetId), {{mode: 'cors'}});
                        if (!resp.ok) return;
                        var body = await resp.json();
                        var ca = body && body.property && body.property.CommercialAsset;
                        var ten = ca && ca.Tenancy;
                        var y = ten && ten.NetInitialYield;
                        if (y != null && !isNaN(y) && y > 0) assetIncomeYield = parseFloat(y);
                    }} else {{
                        var resp2 = await fetch(
                            loanPricerEndpointFor(standaloneOriginAssetId), {{mode: 'cors'}});
                        if (!resp2.ok) return;
                        var body2 = await resp2.json();
                        var inc = body2 && body2.inputs && body2.inputs.gross_annual_income;
                        if (inc != null && !isNaN(inc) && inc > 0) assetGrossIncome = parseFloat(inc);
                    }}
                }} catch (e) {{
                    console.warn('[LoanPricer] asset income unavailable', e);
                }}
            }}

            async function reprice() {{
                if (!standaloneMode && !currentAssetId) return;
                var btn = document.getElementById('lp-reprice-btn');
                if (btn) {{ btn.disabled = true; btn.textContent = 'Pricing...'; }}
                try {{
                    var overrides = readOverrides();
                    // When launched from an asset, drive the flood leg from
                    // that asset's modelled PRS spread instead of the category.
                    if (standaloneMode && assetFloodSpreadBps != null) {{
                        overrides.flood_spread_bps = assetFloodSpreadBps;
                    }}
                    // When the asset has a coupled wind curve, drive the wind
                    // leg from the modelled union (flood OR wind) so the coupon
                    // prices the combined peril. The server takes the wind leg
                    // as the incremental union - flood. Absent for flood-only
                    // assets -> wind stays on the static category lookup.
                    if (standaloneMode && assetUnionSpreadBps != null) {{
                        overrides.union_spread_bps = assetUnionSpreadBps;
                    }}
                    // PRS hazard scenario: the chosen peril spread becomes the
                    // coupon's single hazard leg server-side. Send the scenario
                    // tag plus its modelled spread (bps). When the asset has no
                    // spread for that scenario the value is null and the server
                    // falls back to the legacy flood+wind category lookup.
                    if (standaloneMode) {{
                        var scen = overrides.prs_scenario || 'fow';
                        var scenBps = assetScenarioSpreads[scen];
                        if (scenBps != null && !isNaN(scenBps)) {{
                            overrides.prs_spread_bps = scenBps;
                        }}
                    }}
                    // Derive commercial income from the asset's net initial
                    // yield x the (editable) property value, server-side. The
                    // displayed income is informational here, so drop it from
                    // the overrides to let the yield-derived value through.
                    if (standaloneMode && assetIncomeYield != null) {{
                        overrides.income_yield = assetIncomeYield;
                        delete overrides.gross_annual_income;
                    }}
                    var url = standaloneMode ? standaloneEndpoint() : endpointFor(currentAssetId);
                    var payload = standaloneMode
                        ? {{inputs: overrides, asset_class: standaloneAssetClass}}
                        : {{overrides: overrides}};
                    var response = await fetch(url, {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        mode: 'cors',
                        body: JSON.stringify(payload)
                    }});
                    if (!response.ok) throw new Error('HTTP ' + response.status);
                    var data = await response.json();
                    if (data.status !== 'success') throw new Error(data.message || 'Pricing failed');
                    populateInputs(data.inputs);
                    renderResults(data);
                }} catch (error) {{
                    document.getElementById('loan-pricer-results').innerHTML =
                        '<p style="color:#d32f2f;text-align:center;">Error: ' + error.message + '</p>';
                }} finally {{
                    if (btn) {{ btn.disabled = false; btn.textContent = 'Re-price'; }}
                }}
            }}

            async function showPanel(assetId) {{
                console.log('[LoanPricer] Opening panel for', assetId);
                standaloneMode = false;
                currentAssetId = assetId;
                createPanel();
                buildForm();
                var title = document.getElementById('loan-pricer-title');
                var results = document.getElementById('loan-pricer-results');
                title.textContent = 'Loan Pricer: ' + assetId;
                results.innerHTML = '<p style="color:#999;text-align:center;">Loading...</p>';
                lpPanel.style.display = 'flex';

                try {{
                    var response = await fetch(endpointFor(assetId), {{mode: 'cors'}});
                    if (!response.ok) throw new Error('HTTP ' + response.status);
                    var data = await response.json();
                    if (data.status !== 'success') throw new Error(data.message || 'No loan data');
                    populateInputs(data.inputs);
                    renderResults(data);
                }} catch (error) {{
                    results.innerHTML =
                        '<p style="color:#d32f2f;text-align:center;">Error: ' + error.message + '</p>';
                }}
            }}

            // Standalone "Loan Calculator": asset-independent. Opens with
            // sensible defaults and prices on demand; ignores any asset id
            // passed by the menu. assetClass ('residential'|'commercial')
            // selects the server-side term cap (commercial = 7 years).
            async function showStandalone(assetClass, originAssetId) {{
                console.log('[LoanPricer] Opening standalone calculator', assetClass);
                standaloneMode = true;
                standaloneAssetClass = (assetClass === 'commercial') ? 'commercial' : 'residential';
                currentAssetId = null;
                standaloneOriginAssetId = originAssetId || null;
                createPanel();
                buildForm();
                var titleText = (standaloneAssetClass === 'commercial')
                    ? 'Loan Calculator (Commercial — max 7y)' : 'Loan Calculator';
                document.getElementById('loan-pricer-title').textContent = titleText;
                populateInputs(STANDALONE_DEFAULTS);
                lpPanel.style.display = 'flex';
                // Pull the origin asset's modelled flood spread + income basis
                // (if any) before the first price so the flood leg reflects the
                // real hazard curve (not the flood-category fallback) and the
                // borrower income reflects the asset rather than the default.
                await loadAssetFloodSpread();
                await loadAssetIncome();
                // Residential income is a fixed borrower figure, so seed the
                // editable field with it; commercial income is derived from the
                // yield server-side and shown via the repriced inputs.
                if (assetGrossIncome != null) {{
                    var incEl = document.getElementById('lp-gross_annual_income');
                    if (incEl) incEl.value = assetGrossIncome;
                }}
                reprice();
            }}

            // Residential and commercial menus use distinct action names
            // (matching the viewPropertyStorms / viewCommercialStorms
            // convention); both resolve to the same self-routing panel.
            window.viewLoanPricer = showPanel;
            window.viewCommercialLoanPricer = showPanel;
            // Standalone launchers — distinct names so property/commercial
            // menu actions stay disjoint. Residential is uncapped; commercial
            // caps the term at 7 years server-side.
            window.openLoanCalculator = function(assetId) {{ showStandalone('residential', assetId); }};
            window.openCommercialLoanCalculator = function(assetId) {{ showStandalone('commercial', assetId); }};
            window.LoanPricerPanel = {{
                show: showPanel,
                showStandalone: showStandalone,
                hide: hidePanel
            }};

            console.log('Loan pricer panel ready');
        }})();
        </script>
        """
