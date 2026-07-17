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

            function _phcIsCommercial(propertyId) {
                return typeof propertyId === 'string'
                       && propertyId.indexOf('CPROP-') === 0;
            }

            async function loadData(propertyId) {
                var status = document.getElementById('phc-status');
                status.textContent = 'Loading...';

                var isCommercial = _phcIsCommercial(propertyId);
                // /api/v1/commercial/<id>/{hazard,she,shd,<id>} mirror
                // their /api/v1/properties/<id>/* counterparts — same
                // response keys.
                var apiBase = isCommercial
                    ? '/api/v1/commercial/'
                    : '/api/v1/properties/';

                try {
                    var cfg = window.__BACKEND_CONFIG || {};
                    var baseUrl = cfg.url || '';
                    var url = baseUrl + apiBase + propertyId + '/hazard';

                    var response = await fetch(url, {mode: 'cors'});
                    var result = await response.json();

                    if (!response.ok || result.status !== 'success') {
                        var msg = result.message || ('HTTP ' + response.status);
                        status.textContent = msg;
                        var content = document.getElementById('phc-chart-container');
                        if (content) {
                            content.innerHTML =
                                '<div style="text-align:center;padding:60px 20px;color:#888;">' +
                                '<p style="font-size:16px;font-weight:600;margin-bottom:12px;">No Hazard Curve Data</p>' +
                                '<p>' + msg + '</p>' +
                                '<p style="margin-top:16px;font-size:12px;color:#aaa;">' +
                                'Try re-running: <code>python app.py port --propertyts --propertyhc</code></p></div>';
                        }
                        return;
                    }

                    phcData = result.data;

                    // Fetch counterparties for PRS tab
                    try {
                        var ctpyResp = await fetch(baseUrl + '/api/v1/counterparties', {mode: 'cors'});
                        if (ctpyResp.ok) {
                            var ctpyData = await ctpyResp.json();
                            if (ctpyData.status === 'success') {
                                counterpartyData = ctpyData.counterparties || [];
                            }
                        }
                    } catch (ctpyErr) {
                        console.warn('Counterparty data not available:', ctpyErr.message);
                    }

                    // Fetch SHE/SHD/BRI flood counts and gauge severe count for basis strip
                    try {
                        var [sheResp, shdResp, briResp, stormsResp] = await Promise.all([
                            fetch(baseUrl + apiBase + propertyId + '/she', {mode: 'cors'}),
                            fetch(baseUrl + apiBase + propertyId + '/shd', {mode: 'cors'}),
                            fetch(baseUrl + apiBase + propertyId + '/bri', {mode: 'cors'}),
                            fetch(baseUrl + apiBase + propertyId + '/storms', {mode: 'cors'}),
                        ]);
                        if (sheResp.ok) {
                            var sheData = await sheResp.json();
                            if (sheData.status === 'success') phcData._she = sheData.data;
                        }
                        if (shdResp.ok) {
                            var shdData = await shdResp.json();
                            if (shdData.status === 'success') phcData._shd = shdData.data;
                        }
                        if (briResp.ok) {
                            var briData = await briResp.json();
                            if (briData.status === 'success') phcData._bri = briData.data;
                        }
                        if (stormsResp.ok) {
                            var stormsData = await stormsResp.json();
                            if (stormsData.status === 'success') {
                                phcData._severe_at_gauge = (stormsData.summary || {}).severe_at_nearest_gauge || 0;
                                phcData._storms_data = stormsData;
                            }
                        }
                    } catch (basisErr) {
                        console.warn('SHE/SHD/BRI/storms data not available:', basisErr.message);
                    }

                    console.log('[PropertyHazard] Loaded hazard data for', propertyId, '(' + phcData.flood_count + ' floods)');
                    // Ensure _propertyNames has this asset (preloader may not have finished).
                    // Residential records wrap location under PropertyHeader; commercial
                    // records wrap it under CommercialAsset. The shape differs, but the
                    // populated keys (BuildingNumber + StreetName, or BuildingName)
                    // overlap enough to extract a display string from either.
                    if (!(window._propertyNames || {})[propertyId]) {
                        try {
                            var propResp = await fetch(baseUrl + apiBase + propertyId, {mode: 'cors'});
                            if (propResp.ok) {
                                var propResult = await propResp.json();
                                var rec = propResult.property || {};
                                var loc;
                                if (isCommercial) {
                                    loc = (rec.CommercialAsset || {}).Location || {};
                                } else {
                                    loc = (rec.PropertyHeader || {}).Location || {};
                                }
                                var propAddr = (loc.BuildingName
                                    || ((loc.BuildingNumber || '') + ' '
                                        + (loc.StreetName || '')).trim());
                                if (propAddr) {
                                    if (!window._propertyNames) window._propertyNames = {};
                                    window._propertyNames[propertyId] = propAddr;
                                }
                            }
                        } catch (propErr) { /* ignore */ }
                    }
                    // Refresh title with canonical format
                    var titleEl = document.getElementById('phc-panel-title');
                    var titleLabel = isCommercial
                        ? 'Commercial PRS Pricer: '
                        : 'PRS Pricer: ';
                    if (titleEl) titleEl.textContent =
                        titleLabel + window.propertyDisplayName(propertyId);
                    buildPRSControls();
                    populateBasisStrip();
                    switchTab(activeTab);
                    var spread = (phcData.term_structure || {}).severe ? phcData.term_structure.severe.prs_spread_bps[0] : 0;
                    // Gauge severe count from storms endpoint
                    var gaugeSevere = phcData._severe_at_gauge || 0;
                    var propFloods = phcData.flood_count || 0;
                    var basisEvents = gaugeSevere - propFloods;
                    status.textContent = gaugeSevere + ' gauge severe \u2192 ' + propFloods + ' property floods | basis: ' + basisEvents + ' events | spread: ' + spread.toFixed(1) + 'bp';
                } catch (error) {
                    console.error('[PropertyHazard] Load error:', error);
                    status.textContent = 'Error: ' + error.message;
                    if (window.showError) window.showError('Could not connect to server');
                }
            }
