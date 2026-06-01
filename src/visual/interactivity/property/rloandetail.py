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
Mortgage detail popup panel for property markers.

Displays full mortgage information in an overlay panel,
loaded from the /api/v1/properties/{id}/rloan endpoint.
"""

from typing import Any, Dict

import folium


class RLoanDetailPanel:
    """Handler for interactive residential-loan detail popup.

    Emits JS window globals window.viewRLoanDetail and
    window.RLoanDetailPanel.
    """

    def __init__(self,
                 panel_width: str = "600px",
                 panel_height: str = "520px"):
        self.panel_width = panel_width
        self.panel_height = panel_height

    def get_js(self) -> str:
        """Generate JavaScript for mortgage detail panel."""
        return f"""
        <script>
        (function() {{
            var PANEL_W = '{self.panel_width}';
            var PANEL_H = '{self.panel_height}';
            var mortPanel = null;

            function createPanel() {{
                if (mortPanel) return mortPanel;

                mortPanel = document.createElement('div');
                mortPanel.id = 'mortgage-detail-panel';
                mortPanel.style.cssText =
                    'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);' +
                    'width:' + PANEL_W + ';height:' + PANEL_H + ';' +
                    'background:white;border:1px solid #ccc;border-radius:8px;' +
                    'box-shadow:0 4px 20px rgba(0,0,0,0.3);z-index:2000;' +
                    'display:none;flex-direction:column;font-family:Arial,sans-serif;';

                // Header
                var header = document.createElement('div');
                header.style.cssText =
                    'display:flex;justify-content:space-between;align-items:center;' +
                    'padding:10px 16px;border-bottom:1px solid #eee;background:#f8f9fa;' +
                    'border-radius:8px 8px 0 0;';

                var title = document.createElement('span');
                title.id = 'mortgage-detail-title';
                title.style.cssText = 'font-weight:bold;font-size:14px;color:#333;';

                var closeBtn = document.createElement('button');
                closeBtn.innerHTML = '&times;';
                closeBtn.style.cssText =
                    'border:none;background:none;font-size:24px;cursor:pointer;' +
                    'color:#666;padding:0 8px;line-height:1;';
                closeBtn.onclick = hidePanel;

                header.appendChild(title);
                header.appendChild(closeBtn);

                // Content
                var content = document.createElement('div');
                content.id = 'mortgage-detail-content';
                content.style.cssText = 'flex:1;padding:12px 16px;overflow-y:auto;font-size:13px;';

                mortPanel.appendChild(header);
                mortPanel.appendChild(content);
                document.body.appendChild(mortPanel);

                document.addEventListener('keydown', function(e) {{
                    if (e.key === 'Escape' && mortPanel.style.display !== 'none') hidePanel();
                }});

                return mortPanel;
            }}

            function hidePanel() {{
                if (mortPanel) mortPanel.style.display = 'none';
                console.log('[Mortgage] Panel closed');
            }}

            function fmt(v) {{
                if (v === null || v === undefined) return 'N/A';
                return String(v);
            }}

            function fmtCurrency(v) {{
                if (typeof v !== 'number') return fmt(v);
                return 'GBP ' + v.toLocaleString('en-GB', {{maximumFractionDigits: 0}});
            }}

            function fmtPct(v) {{
                if (typeof v !== 'number') return fmt(v);
                if (v < 1) return (v * 100).toFixed(2) + '%';
                return v.toFixed(2) + '%';
            }}

            function section(title, rows) {{
                var html = '<div style="margin-bottom:12px;">' +
                    '<div style="font-weight:700;font-size:12px;color:#8E44AD;border-bottom:1px solid #E8DAEF;' +
                    'padding-bottom:4px;margin-bottom:6px;">' + title + '</div>';
                rows.forEach(function(r) {{
                    html += '<div style="display:flex;justify-content:space-between;padding:2px 0;">' +
                        '<span style="color:#666;">' + r[0] + '</span>' +
                        '<span style="font-weight:600;color:#333;">' + r[1] + '</span></div>';
                }});
                html += '</div>';
                return html;
            }}

            async function showPanel(propertyId) {{
                console.log('[Mortgage] Opening panel for', propertyId);
                var panel = createPanel();
                var title = document.getElementById('mortgage-detail-title');
                var content = document.getElementById('mortgage-detail-content');
                title.textContent = 'Mortgage Details: ' + propertyId;
                content.innerHTML = '<p style="color:#999;text-align:center;">Loading...</p>';
                panel.style.display = 'flex';

                try {{
                    var cfg = window.__BACKEND_CONFIG || {{}};
                    var baseUrl = cfg.url || '';
                    var url = baseUrl + '/api/v1/properties/' + propertyId + '/rloan';
                    var response = await fetch(url, {{mode: 'cors'}});
                    if (!response.ok) throw new Error('HTTP ' + response.status);
                    var data = await response.json();
                    if (data.status !== 'success') throw new Error(data.message || 'No mortgage data');

                    var m = data.mortgage || {{}};
                    console.log('[Mortgage] Loaded mortgage data for', propertyId);
                    var hdr = m.Header || {{}};
                    var app = m.Application || {{}};
                    var fin = m.FinancialTerms || {{}};
                    var feat = m.Features || {{}};
                    var cur = m.CurrentStatus || {{}};
                    var bor = m.BorrowerDetails || {{}};
                    var risk = m.RiskAssessment || {{}};

                    var html = '';
                    html += section('Loan Summary', [
                        ['Mortgage ID', fmt(hdr.RLoanID)],
                        ['Provider', fmt(app.MortgageProvider)],
                        ['Purpose', fmt(app.LoanPurpose)],
                        ['Occupancy', fmt(app.OccupancyType)],
                        ['Application Date', fmt(app.ApplicationDate)],
                        ['Channel', fmt(app.ApplicationChannel)],
                    ]);
                    html += section('Financial Terms', [
                        ['Original Loan', fmtCurrency(fin.OriginalLoan)],
                        ['Purchase Value', fmtCurrency(fin.PurchaseValue)],
                        ['Outstanding Balance', fmtCurrency(cur.OutstandingBalance)],
                        ['Rate', fmtPct(fin.OriginalLendingRate) + ' (' + fmt(fin.OriginalRateType) + ')'],
                        ['Original LTV', fmtPct(fin.OriginalLTV)],
                        ['Current LTV', fmtPct(cur.CurrentLTV)],
                        ['Term', fmt(fin.OriginalTerm) + ' months'],
                        ['Remaining', fmt(cur.RemainingTerm) + ' months'],
                        ['Maturity', fmt(fin.MaturityDate)],
                        ['DTI Ratio', fmtPct(fin.DebtToIncomeRatio)],
                    ]);
                    html += section('Current Status', [
                        ['Account Status', fmt(cur.AccountStatus)],
                        ['Current Rate', fmtPct(cur.CurrentInterestRate)],
                        ['Default Flag', fmt(cur.DefaultFlag)],
                        ['Arrears', fmt(cur.ArrearsMonths) + ' months'],
                    ]);
                    html += section('Borrower', [
                        ['Age', fmt(bor.BorrowerAge)],
                        ['Income', fmtCurrency(bor.BorrowerIncome)],
                        ['Credit Score', fmt(bor.BorrowerCreditScore)],
                        ['Employment', fmt(bor.EmploymentType)],
                        ['Borrowers', fmt(bor.NumberOfBorrowers)],
                    ]);
                    html += section('Risk Assessment', [
                        ['Mortgage Type', fmt(feat.MortgageType)],
                        ['Repayment Type', fmt(feat.RepaymentType)],
                        ['Behavioral Score', fmt(risk.BehavioralScore)],
                        ['Prepayment Risk', fmt(risk.PrepaymentRisk)],
                        ['Flood Risk', fmt(risk.FloodRiskCategory)],
                    ]);

                    content.innerHTML = html;
                }} catch (error) {{
                    content.innerHTML = '<p style="color:#d32f2f;text-align:center;">Error: ' + error.message + '</p>';
                }}
            }}

            window.viewRLoanDetail = showPanel;
            window.RLoanDetailPanel = {{
                show: showPanel,
                hide: hidePanel
            }};

            console.log('Mortgage detail panel ready');
        }})();
        </script>
        """

    def add_to_map(self, folium_map: folium.Map) -> None:
        """Add mortgage detail panel to a Folium map."""
        folium_map.get_root().html.add_child(folium.Element(self.get_js()))

    def get_statistics(self) -> Dict[str, Any]:
        return {
            'panel_width': self.panel_width,
            'panel_height': self.panel_height,
        }
