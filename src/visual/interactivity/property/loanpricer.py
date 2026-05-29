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
                return 'GBP ' + v.toLocaleString('en-GB', {{maximumFractionDigits: 0}});
            }}

            function fmtPct(v) {{
                if (typeof v !== 'number' || isNaN(v)) return 'N/A';
                return (v * 100).toFixed(2) + '%';
            }}

            function fmtNum(v, dp) {{
                if (typeof v !== 'number' || isNaN(v)) return 'N/A';
                return v.toFixed(dp === undefined ? 2 : dp);
            }}

            function buildForm() {{
                var form = document.getElementById('loan-pricer-form');
                var html = '<div style="font-weight:700;font-size:12px;color:#1565C0;' +
                    'border-bottom:1px solid #BBDEFB;padding-bottom:4px;margin-bottom:8px;">' +
                    'Loan Inputs</div>';
                FIELDS.forEach(function(f) {{
                    html += '<div style="margin-bottom:6px;">' +
                        '<label style="display:block;color:#666;font-size:11px;margin-bottom:2px;">' +
                        f.label + '</label>' +
                        '<input id="' + f.id + '" type="number" step="any" ' +
                        'style="width:100%;box-sizing:border-box;padding:4px 6px;' +
                        'border:1px solid #ccc;border-radius:4px;font-size:13px;"></div>';
                }});
                // Flood risk dropdown
                html += '<div style="margin-bottom:10px;">' +
                    '<label style="display:block;color:#666;font-size:11px;margin-bottom:2px;">' +
                    'Flood Risk Category</label>' +
                    '<select id="lp-flood_risk_category" ' +
                    'style="width:100%;box-sizing:border-box;padding:4px 6px;' +
                    'border:1px solid #ccc;border-radius:4px;font-size:13px;">';
                FLOOD_OPTIONS.forEach(function(o) {{
                    html += '<option value="' + o + '">' + o + '</option>';
                }});
                html += '</select></div>';
                html += '<button id="lp-reprice-btn" ' +
                    'style="width:100%;padding:8px;background:#1565C0;color:white;' +
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
                return ov;
            }}

            function renderResults(data) {{
                var p = (data && data.pricing) || {{}};
                var rows = [
                    ['Fair Value', fmtCurrency(p.mortgage_value), '#1B5E20'],
                    ['Discount to Par', fmtCurrency(p.discount_to_par), '#C62828'],
                    ['Discount %', fmtNum(p.discount_percentage, 2) + '%', '#C62828'],
                    ['Credit Spread', fmtPct(p.credit_spread), '#333'],
                    ['LTV Ratio', fmtPct(p.ltv_ratio), '#333'],
                    ['LTV Factor', fmtNum(p.ltv_factor), '#333'],
                    ['Flood Risk Factor', fmtNum(p.flood_risk_factor), '#333'],
                    ['Affordability Ratio', fmtPct(p.affordability_ratio), '#333'],
                    ['Monthly Payment', fmtCurrency(p.monthly_payment), '#333'],
                    ['Annual Payment', fmtCurrency(p.annual_payment), '#333'],
                    ['PV Cashflows', fmtCurrency(p.pv_cashflows), '#333'],
                    ['PV Losses', fmtCurrency(p.pv_losses), '#333']
                ];
                var html = '<div style="font-weight:700;font-size:12px;color:#1565C0;' +
                    'border-bottom:1px solid #BBDEFB;padding-bottom:4px;margin-bottom:8px;">' +
                    'Pricing Results</div>';
                rows.forEach(function(r) {{
                    html += '<div style="display:flex;justify-content:space-between;padding:3px 0;' +
                        'border-bottom:1px solid #f5f5f5;">' +
                        '<span style="color:#666;">' + r[0] + '</span>' +
                        '<span style="font-weight:600;color:' + r[2] + ';">' + r[1] + '</span></div>';
                }});
                document.getElementById('loan-pricer-results').innerHTML = html;
            }}

            function endpointFor(assetId) {{
                var cfg = window.__BACKEND_CONFIG || {{}};
                var baseUrl = cfg.url || '';
                var path = (assetId.indexOf('CPROP-') === 0)
                    ? '/api/v1/commercial/' : '/api/v1/properties/';
                return baseUrl + path + assetId + '/loan-pricer';
            }}

            async function reprice() {{
                if (!currentAssetId) return;
                var btn = document.getElementById('lp-reprice-btn');
                if (btn) {{ btn.disabled = true; btn.textContent = 'Pricing...'; }}
                try {{
                    var overrides = readOverrides();
                    var response = await fetch(endpointFor(currentAssetId), {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        mode: 'cors',
                        body: JSON.stringify({{overrides: overrides}})
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

            // Residential and commercial menus use distinct action names
            // (matching the viewPropertyStorms / viewCommercialStorms
            // convention); both resolve to the same self-routing panel.
            window.viewLoanPricer = showPanel;
            window.viewCommercialLoanPricer = showPanel;
            window.LoanPricerPanel = {{
                show: showPanel,
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
