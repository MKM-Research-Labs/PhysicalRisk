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

"""Loan Pricer JS template — part 2 of 4.

Byte-exact slice of the original LOAN_PRICER_JS_TEMPLATE string,
reassembled in __init__.py. Literal JS braces stay doubled for
``str.format``; do not edit the split boundaries by hand.
"""

PART = r'''            function selectHtml(id, label, options) {{
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
                    // PRS hazard scenario: which modelled peril spread drives
                    // the coupon's hazard leg. Only meaningful when launched
                    // from an asset (its fan supplies the spreads); otherwise
                    // the chosen scenario falls back to the category lookup.
                    html += selectHtml('lp-prs_scenario', 'PRS Hazard Scenario', PRS_SCENARIOS);
                    // User-defined contractual coupon. Seeded with the model-
                    // derived coupon on the first price; editing it overrides the
                    // rate the borrower pays, while the model coupon stays visible
                    // in the build-up as the "Original Contractual Coupon".
                    html += '<div style="margin-bottom:6px;">' +
                        '<label style="display:block;color:#666;font-size:11px;margin-bottom:2px;">' +
                        'Contractual Coupon (%)</label>' +
                        '<input id="lp-contractual_coupon" type="number" step="any" ' +
                        'style="width:100%;box-sizing:border-box;padding:4px 6px;' +
                        'border:1px solid #ccc;border-radius:4px;font-size:13px;"></div>';
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
                var cr = document.getElementById('lp-credit_rating');
                if (cr && cr.value) ov.credit_rating = cr.value;
                var ps = document.getElementById('lp-prs_scenario');
                if (ps && ps.value) ov.prs_scenario = ps.value;
                // User-defined contractual coupon (shown as %, sent as a decimal).
                // Overrides the model-derived coupon as the rate the borrower pays.
                var cc = document.getElementById('lp-contractual_coupon');
                if (cc && cc.value !== '') {{
                    var ccNum = parseFloat(cc.value);
                    if (!isNaN(ccNum)) ov.contractual_coupon = ccNum / 100;
                }}
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
                    ['PV Cashflows', fmtCurrency(p.pv_cashflows), '#333']
                ];
                var html = '';
                // Coupon build-up (standalone calculator only): show how the
                // contractual coupon decomposes into risk-free + credit + hazard.
                var c = data && data.coupon;
                if (c) {{
                    // Seed the user-defined contractual coupon field with the
                    // model-derived coupon on the first price (when still empty),
                    // so the left panel opens on the model value and the user can
                    // adjust from there. A non-empty field is the user's own input
                    // and is left untouched on re-price.
                    var ccEl = document.getElementById('lp-contractual_coupon');
                    if (ccEl && ccEl.value === '' && typeof c.rate === 'number') {{
                        ccEl.value = (c.rate * 100).toFixed(2);
                    }}
                    // The flood leg is PRS-priced; the label notes whether it
                    // came from the asset's own hazard curve or the category
                    // fallback. When opened from an asset, deep-link the leg to
                    // that asset's PRS pricer panel so the user can drill in.
                    var fromAsset = (c.flood_priced_by || '').indexOf('asset') >= 0;
                    var floodLabel = fromAsset
                        ? 'Flood Hazard (PRS \u00b7 asset curve)'
                        : 'Flood Hazard (PRS \u00b7 category)';
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
                        ? 'Wind Hazard (PRS \u00b7 combined)'
                        : 'Wind Hazard (static)';
                    var couponRows = [
                        ['Original Contractual Coupon', fmtPct(c.rate), '#0D47A1'],
                        ['Risk-free (curve)', fmtPct(c.risk_free), '#333'],
                        ['Credit Spread (' + (c.credit_rating || '') + ')', fmtPct(c.credit_spread), '#333']
                    ];
                    // When the user picked a PRS scenario the coupon carries a
                    // single hazard leg (that scenario's modelled spread); show
                    // it as one labelled row. Otherwise fall back to the legacy
                    // flood + wind two-leg decomposition.
                    if (c.prs_scenario) {{
                        var SCEN_LABELS = {{
                            flo: 'Flood only', bri: 'Flood only \u00b7 BRI resilience',
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

'''
