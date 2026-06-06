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

"""Loan Pricer JS template — part 3 of 4.

Byte-exact slice of the original LOAN_PRICER_JS_TEMPLATE string,
reassembled in __init__.py. Literal JS braces stay doubled for
``str.format``; do not edit the split boundaries by hand.
"""

PART = r'''            function endpointFor(assetId) {{
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
                assetScenarioSpreads = {{flo: null, bri: null, win: null, faw: null, fow: null, baw: null, bow: null}};
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
'''
