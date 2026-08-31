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

        (function() {
            var _cfg = window.__RLOAN_CONFIG || {};
            var PANEL_W = _cfg.panelWidth || '600px';
            var PANEL_H = _cfg.panelHeight || '520px';
            var mortPanel = null;

            function createPanel() {
                if (mortPanel) return mortPanel;

                mortPanel = document.createElement('div');
                mortPanel.id = 'mortgage-detail-panel';
                mortPanel.style.cssText =
                    'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);' +
                    'width:' + PANEL_W + ';height:' + PANEL_H + ';' +
                    'background:var(--panel);border:1px solid var(--divider);border-radius:var(--radius-lg);' +
                    'box-shadow:var(--shadow-toast);z-index:2000;' +
                    'display:none;flex-direction:column;font-family:Arial,sans-serif;';

                // Header
                var header = document.createElement('div');
                header.style.cssText =
                    'display:flex;justify-content:space-between;align-items:center;' +
                    'padding:var(--space-5) var(--space-8);border-bottom:1px solid var(--line-soft);background:var(--wash);' +
                    'border-radius:var(--radius-lg) var(--radius-lg) 0 0;';

                var title = document.createElement('span');
                title.id = 'mortgage-detail-title';
                title.style.cssText = 'font-weight:bold;font-size:var(--size-14);color:var(--text);';

                var closeBtn = document.createElement('button');
                closeBtn.innerHTML = '&times;';
                closeBtn.style.cssText =
                    'border:none;background:none;font-size:var(--size-24);cursor:pointer;' +
                    'color:var(--text-3);padding:0 var(--space-4);line-height:1;';
                closeBtn.onclick = hidePanel;

                header.appendChild(title);
                header.appendChild(closeBtn);

                // Content
                var content = document.createElement('div');
                content.id = 'mortgage-detail-content';
                content.style.cssText = 'flex:1;padding:var(--space-6) var(--space-8);overflow-y:auto;font-size:var(--size-md);';

                mortPanel.appendChild(header);
                mortPanel.appendChild(content);
                document.body.appendChild(mortPanel);

                document.addEventListener('keydown', function(e) {
                    if (e.key === 'Escape' && mortPanel.style.display !== 'none') hidePanel();
                });

                return mortPanel;
            }

            function hidePanel() {
                if (mortPanel) mortPanel.style.display = 'none';
                console.log('[Mortgage] Panel closed');
            }

            function fmt(v) {
                if (v === null || v === undefined) return 'N/A';
                return String(v);
            }

            function fmtCurrency(v) {
                if (typeof v !== 'number') return fmt(v);
                return 'GBP ' + v.toLocaleString('en-GB', {maximumFractionDigits: 0});
            }

            function fmtPct(v) {
                if (typeof v !== 'number') return fmt(v);
                if (v < 1) return (v * 100).toFixed(2) + '%';
                return v.toFixed(2) + '%';
            }

            function section(title, rows) {
                var html = '<div style="margin-bottom:var(--space-6);">' +
                    '<div style="font-weight:700;font-size:var(--size-sm);color:var(--layer-violet-soft);border-bottom:1px solid var(--layer-violet-bg);' +
                    'padding-bottom:var(--space-2);margin-bottom:var(--space-3);">' + title + '</div>';
                rows.forEach(function(r) {
                    html += '<div style="display:flex;justify-content:space-between;padding:var(--space-1) 0;">' +
                        '<span style="color:var(--text-3);">' + r[0] + '</span>' +
                        '<span style="font-weight:600;color:var(--text);">' + r[1] + '</span></div>';
                });
                html += '</div>';
                return html;
            }

            async function showPanel(propertyId) {
                console.log('[Mortgage] Opening panel for', propertyId);
                var panel = createPanel();
                var title = document.getElementById('mortgage-detail-title');
                var content = document.getElementById('mortgage-detail-content');
                title.textContent = 'Mortgage Details: ' + propertyId;
                content.innerHTML = '<p style="color:var(--muted-2);text-align:center;">Loading...</p>';
                panel.style.display = 'flex';

                try {
                    var cfg = window.__BACKEND_CONFIG || {};
                    var baseUrl = cfg.url || '';
                    var url = baseUrl + '/api/v1/properties/' + propertyId + '/rloan';
                    var response = await fetch(url, {mode: 'cors'});
                    if (!response.ok) throw new Error('HTTP ' + response.status);
                    var data = await response.json();
                    if (data.status !== 'success') throw new Error(data.message || 'No mortgage data');

                    var m = data.mortgage || {};
                    console.log('[Mortgage] Loaded mortgage data for', propertyId);
                    var hdr = m.Header || {};
                    var app = m.Application || {};
                    var fin = m.FinancialTerms || {};
                    var feat = m.Features || {};
                    var cur = m.CurrentStatus || {};
                    var bor = m.BorrowerDetails || {};
                    var risk = m.RiskAssessment || {};

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
                } catch (error) {
                    content.innerHTML = '<p style="color:var(--red);text-align:center;">Error: ' + error.message + '</p>';
                }
            }

            window.viewRLoanDetail = showPanel;
            window.RLoanDetailPanel = {
                show: showPanel,
                hide: hidePanel
            };

            console.log('Mortgage detail panel ready');
        })();
        
