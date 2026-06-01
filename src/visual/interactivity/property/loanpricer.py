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
Loan Pricer popup panel for property and commercial markers.

Provides an editable set of loan inputs (balance, value, rate, term, flood
risk, …) and prices them live against the server-side LoanPricer via the
``/loan-pricer`` route. Residential (PROP-) and commercial (CPROP-) assets
share one panel; the asset-id prefix selects the endpoint.
"""

from typing import Any, Dict

import folium


class LoanPricerPanel:
    """Handler for the interactive Loan Pricer popup."""

    def __init__(self,
                 panel_width: str = "720px",
                 panel_height: str = "560px"):
        self.panel_width = panel_width
        self.panel_height = panel_height

    def get_js(self) -> str:
        """Generate JavaScript for the loan pricer panel."""
        return f"""
        <script>
        (function() {{
            var PANEL_W = '{self.panel_width}';
            var PANEL_H = '{self.panel_height}';
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
                flood_risk_category: 'Medium',
                wind_risk_category: 'Medium'
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
            var FLOOD_OPTIONS = ['Very low', 'Low', 'Medium', 'High', 'Very high'];
            var WIND_OPTIONS = ['Very low', 'Low', 'Medium', 'High', 'Very high'];
            var CREDIT_RATINGS = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC'];

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
                    h += '<option value="' + o + '">' + o + '</option>';
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
                // borrower credit rating + flood/wind hazard categories.
                if (standaloneMode) {{
                    html += selectHtml('lp-credit_rating', 'Borrower Credit Rating', CREDIT_RATINGS);
                }}
                html += selectHtml('lp-flood_risk_category', 'Flood Risk Category', FLOOD_OPTIONS);
                if (standaloneMode) {{
                    html += selectHtml('lp-wind_risk_category', 'Wind Risk Category', WIND_OPTIONS);
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
                var fr = document.getElementById('lp-flood_risk_category');
                if (fr && inputs.flood_risk_category) fr.value = inputs.flood_risk_category;
                var wr = document.getElementById('lp-wind_risk_category');
                if (wr && inputs.wind_risk_category) wr.value = inputs.wind_risk_category;
                var cr = document.getElementById('lp-credit_rating');
                if (cr && inputs.credit_rating) cr.value = inputs.credit_rating;
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
                var fr = document.getElementById('lp-flood_risk_category');
                if (fr && fr.value) ov.flood_risk_category = fr.value;
                var wr = document.getElementById('lp-wind_risk_category');
                if (wr && wr.value) ov.wind_risk_category = wr.value;
                var cr = document.getElementById('lp-credit_rating');
                if (cr && cr.value) ov.credit_rating = cr.value;
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
                    var couponRows = [
                        ['Contractual Coupon', fmtPct(c.rate), '#0D47A1'],
                        ['Risk-free (curve)', fmtPct(c.risk_free), '#333'],
                        ['Credit Spread (' + (c.credit_rating || '') + ')', fmtPct(c.credit_spread), '#333'],
                        [floodLabel, fmtPct(c.flood_spread), '#333'],
                        ['Wind Hazard (static)', fmtPct(c.wind_spread), '#333']
                    ];
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
            async function loadAssetFloodSpread() {{
                assetFloodSpreadBps = null;
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
                    }}
                }} catch (e) {{
                    console.warn('[LoanPricer] asset flood spread unavailable', e);
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
                // Pull the origin asset's modelled flood spread (if any) before
                // the first price so the flood leg reflects the real hazard
                // curve rather than the flood-category fallback.
                await loadAssetFloodSpread();
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

    def add_to_map(self, folium_map: folium.Map) -> None:
        """Add loan pricer panel to a Folium map."""
        folium_map.get_root().html.add_child(folium.Element(self.get_js()))

    def get_statistics(self) -> Dict[str, Any]:
        return {
            'panel_width': self.panel_width,
            'panel_height': self.panel_height,
        }
