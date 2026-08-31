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

            function selectHtml(id, label, options) {{
                var h = '<div style="margin-bottom:var(--space-3);">' +
                    '<label style="display:block;color:var(--text-3);font-size:var(--size-xs);margin-bottom:var(--space-1);">' +
                    label + '</label>' +
                    '<select id="' + id + '" ' +
                    'style="width:100%;box-sizing:border-box;padding:var(--space-2) var(--space-3);' +
                    'border:1px solid var(--divider);border-radius:var(--radius-4);font-size:var(--size-md);">';
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

            // A binary on/off button for an independent peril (fire / seismic).
            // State lives in the button's data-on attribute; setToggle reflects
            // it visually and toggleState reads it back for the overrides.
            function toggleHtml(id, label) {{
                return '<div style="margin-bottom:var(--space-3);">' +
                    '<label style="display:block;color:var(--text-3);font-size:var(--size-xs);margin-bottom:var(--space-1);">' +
                    label + '</label>' +
                    '<button id="' + id + '" type="button" data-on="0" ' +
                    'style="width:100%;box-sizing:border-box;padding:var(--space-3);border:1px solid var(--divider);' +
                    'border-radius:var(--radius-4);font-size:var(--size-md);font-weight:600;cursor:pointer;' +
                    'background:var(--sunken);color:var(--muted);">Off</button></div>';
            }}

            function setToggle(btn, on) {{
                if (!btn) return;
                btn.setAttribute('data-on', on ? '1' : '0');
                btn.textContent = on ? 'On' : 'Off';
                btn.style.background = on ? 'var(--accent-mid)' : 'var(--sunken)';
                btn.style.color = on ? 'var(--panel)' : 'var(--muted)';
                btn.style.borderColor = on ? 'var(--accent-mid)' : 'var(--divider)';
            }}

            function toggleState(id) {{
                var b = document.getElementById(id);
                return !!(b && b.getAttribute('data-on') === '1');
            }}

            function buildForm() {{
                var form = document.getElementById('loan-pricer-form');
                var html = '<div style="font-weight:700;font-size:var(--size-sm);color:var(--accent-mid);' +
                    'border-bottom:1px solid var(--accent-border);padding-bottom:var(--space-2);margin-bottom:var(--space-4);">' +
                    'Loan Inputs</div>';
                FIELDS.forEach(function(f) {{
                    // In standalone mode the coupon is derived (rating + hazard),
                    // so the contractual rate isn't a free input.
                    if (standaloneMode && f.id === 'lp-interest_rate') return;
                    html += '<div style="margin-bottom:var(--space-3);">' +
                        '<label style="display:block;color:var(--text-3);font-size:var(--size-xs);margin-bottom:var(--space-1);">' +
                        f.label + '</label>' +
                        '<input id="' + f.id + '" type="number" step="any" ' +
                        'style="width:100%;box-sizing:border-box;padding:var(--space-2) var(--space-3);' +
                        'border:1px solid var(--divider);border-radius:var(--radius-4);font-size:var(--size-md);"></div>';
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
                    // Independent perils — binary on/off. The storm/flood menu
                    // above sets the basis; fire and seismic are independent
                    // legs folded into the all-in coupon by root-sum-of-squares
                    // when toggled on (their spreads come from the asset curve).
                    html += '<div style="font-size:var(--size-xs);color:var(--muted);text-transform:uppercase;' +
                        'letter-spacing:0.5px;margin:var(--space-4) 0 var(--space-1);">Independent Perils</div>';
                    html += toggleHtml('lp-include_fire', 'Fire');
                    html += toggleHtml('lp-include_seismic', 'Seismic');
                    // User-defined contractual coupon. Seeded with the model-
                    // derived coupon on the first price; editing it overrides the
                    // rate the borrower pays, while the model coupon stays visible
                    // in the build-up as the "Original Contractual Coupon".
                    html += '<div style="margin-bottom:var(--space-3);">' +
                        '<label style="display:block;color:var(--text-3);font-size:var(--size-xs);margin-bottom:var(--space-1);">' +
                        'Contractual Coupon (%)</label>' +
                        '<input id="lp-contractual_coupon" type="number" step="any" ' +
                        'style="width:100%;box-sizing:border-box;padding:var(--space-2) var(--space-3);' +
                        'border:1px solid var(--divider);border-radius:var(--radius-4);font-size:var(--size-md);"></div>';
                }}
                html += '<button id="lp-reprice-btn" ' +
                    'style="width:100%;margin-top:var(--space-2);padding:var(--space-4);background:var(--accent-mid);color:var(--inverse);' +
                    'border:none;border-radius:var(--radius-4);font-size:var(--size-md);font-weight:600;cursor:pointer;">' +
                    'Re-price</button>';
                form.innerHTML = html;
                document.getElementById('lp-reprice-btn').onclick = reprice;
                // Wire the peril toggles: each click flips its state and reprices
                // so the all-in coupon updates live.
                ['lp-include_fire', 'lp-include_seismic'].forEach(function(id) {{
                    var b = document.getElementById(id);
                    if (!b) return;
                    b.onclick = function() {{
                        setToggle(b, b.getAttribute('data-on') !== '1');
                        reprice();
                    }};
                }});
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
                setToggle(document.getElementById('lp-include_fire'), !!inputs.include_fire);
                setToggle(document.getElementById('lp-include_seismic'), !!inputs.include_seismic);
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
                // Independent-peril toggle states (binary on/off buttons).
                ov.include_fire = toggleState('lp-include_fire');
                ov.include_seismic = toggleState('lp-include_seismic');
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
                    ['Fair Value', fmtCurrency(p.mortgage_value), 'var(--green-deep)'],
                    ['Discount to Par', fmtCurrency(p.discount_to_par), 'var(--red-dark)'],
                    ['Discount %', fmtNum(p.discount_percentage, 2) + '%', 'var(--red-dark)'],
                    ['Discount Rate', fmtPct(p.discount_rate), 'var(--text)'],
                    ['LTV Ratio', fmtPct(p.ltv_ratio), 'var(--text)'],
                    ['Monthly Payment', fmtCurrency(p.monthly_payment), 'var(--text)'],
                    ['Annual Payment', fmtCurrency(p.annual_payment), 'var(--text)'],
                    ['PV Cashflows', fmtCurrency(p.pv_cashflows), 'var(--text)']
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
                            'style="color:var(--accent-mid);text-decoration:underline;font-size:var(--size-xs);" ' +
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
                        ['Original Contractual Coupon', fmtPct(c.rate), 'var(--accent-ink)'],
                        ['Risk-free (curve)', fmtPct(c.risk_free), 'var(--text)'],
                        ['Credit Spread (' + (c.credit_rating || '') + ')', fmtPct(c.credit_spread), 'var(--text)']
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
                                'style="color:var(--accent-mid);text-decoration:underline;font-size:var(--size-xs);" ' +
                                'title="Open the PRS pricer for this asset">&#8599; PRS pricer</a>';
                        }}
                        // The flood/wind basis (pre-RSS). Falls back to the all-in
                        // for older payloads that don't carry flood_wind_base.
                        var basis = (c.flood_wind_base != null) ? c.flood_wind_base : c.hazard_spread;
                        couponRows.push([prsLabel, fmtPct(basis), 'var(--text)']);
                    }} else {{
                        couponRows.push([floodLabel, fmtPct(c.flood_spread), 'var(--text)']);
                        couponRows.push([windLabel, fmtPct(c.wind_spread), 'var(--text)']);
                    }}
                    // Independent peril legs — shown when their toggle is on, then
                    // the all-in (root-sum-of-squares of the basis + peril legs).
                    if (c.fire_included) {{
                        var fl = (c.fire_spread > 0) ? '' : ' · no asset leg';
                        couponRows.push(['Fire (independent' + fl + ')', fmtPct(c.fire_spread), 'var(--orange-deep)']);
                    }}
                    if (c.seismic_included) {{
                        var sl = (c.seismic_spread > 0) ? '' : ' · no asset leg';
                        couponRows.push(['Seismic (independent' + sl + ')', fmtPct(c.seismic_spread), Theme.value('peril-seismic-row')]);
                    }}
                    if (c.fire_included || c.seismic_included) {{
                        couponRows.push(['All-in Hazard (√Σ sq)', fmtPct(c.hazard_spread), 'var(--accent-ink)']);
                    }}
                    html += '<div style="font-weight:700;font-size:var(--size-sm);color:var(--accent-mid);' +
                        'border-bottom:1px solid var(--accent-border);padding-bottom:var(--space-2);margin-bottom:var(--space-4);">' +
                        'Coupon Build-up</div>';
                    couponRows.forEach(function(r) {{
                        html += '<div style="display:flex;justify-content:space-between;padding:var(--space-2) 0;' +
                            'border-bottom:1px solid var(--sunken);">' +
                            '<span style="color:var(--text-3);">' + r[0] + '</span>' +
                            '<span style="font-weight:600;color:' + r[2] + ';">' + r[1] + '</span></div>';
                    }});
                    html += '<div style="height:12px;"></div>';
                }}
                html += '<div style="font-weight:700;font-size:var(--size-sm);color:var(--accent-mid);' +
                    'border-bottom:1px solid var(--accent-border);padding-bottom:var(--space-2);margin-bottom:var(--space-4);">' +
                    'Pricing Results</div>';
                rows.forEach(function(r) {{
                    html += '<div style="display:flex;justify-content:space-between;padding:var(--space-2) 0;' +
                        'border-bottom:1px solid var(--sunken);">' +
                        '<span style="color:var(--text-3);">' + r[0] + '</span>' +
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

