// Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
//
// This software is licensed by MKM Research Labs for non-commercial 
// research and educational use only. Any commercial use, including 
// but not limited to use in or for products or services offered for sale, 
// internal business operations intended for commercial advantage, or
// research and development conducted for a commercial entity, is expressly
// prohibited unless separately authorized in writing by MKM Research Labs.
//
// Use, reproduction, distribution, or modification of this code is subject to the
// terms and conditions of the license agreement provided with this software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

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
                    // Independent peril legs: forward the asset's fire/seismic
                    // spreads so the server can fold them into the all-in coupon
                    // by root-sum-of-squares when their toggle (include_fire /
                    // include_seismic, set by readOverrides) is on.
                    if (standaloneMode) {{
                        if (assetFireSpreadBps != null) {{
                            overrides.fire_spread_bps = assetFireSpreadBps;
                        }}
                        if (assetSeismicSpreadBps != null) {{
                            overrides.seismic_spread_bps = assetSeismicSpreadBps;
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
                // Mutual exclusion: this and the property hazard panel are both
                // centered z-index 2000 modals and would intercept each other's
                // clicks if both stayed open. Close the property panel first.
                if (window.PropertyHazardCurvePanel && window.PropertyHazardCurvePanel.hide)
                    window.PropertyHazardCurvePanel.hide();
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
                if (window.PropertyHazardCurvePanel && window.PropertyHazardCurvePanel.hide)
                    window.PropertyHazardCurvePanel.hide();
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
        
