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
// Backend communication handler for interactive map functionality.

(function(root) {
    'use strict';

    function createBackendHandler(config) {
        config = config || {};
        
        var BACKEND = {
            // If config.url is explicitly provided, use it; otherwise use empty string
            // so we talk to the same origin the page was served from.
            url: (typeof config.url === 'string') ? config.url : '',
            endpoints: config.endpoints || {},
            timeout: config.timeout || 30000
};

        async function callAPI(endpoint, data, successMsg) {
            console.log('API:', endpoint, data);

            try {
                if (root.showLoading) root.showLoading('Processing request...');

                var response = await fetch(BACKEND.url + endpoint, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json', 'Accept': 'application/json'},
                    body: JSON.stringify(data),
                    mode: 'cors'
                });

                if (!response.ok) {
                    throw new Error('HTTP ' + response.status + ': ' + await response.text());
                }

                var result = await response.json();

                if (result.status === 'success') {
                    if (root.showSuccess) root.showSuccess(successMsg + (result.message ? '\n' + result.message : ''));
                    if (result.file_path) {
                        setTimeout(function() {
                            if (root.showInfo) root.showInfo('Saved to: ' + result.file_path);
                        }, 2000);
                    }
                    return result;
                } else {
                    if (root.showError) root.showError(result.message || 'Operation failed');
                    return null;
                }
            } catch (error) {
                console.error('API error:', error);

                var msg = 'Request failed';
                if (error.message.includes('fetch')) {
                    msg = 'Cannot connect to server at ' + BACKEND.url;
                } else if (error.message.includes('CORS')) {
                    msg = 'CORS error - check server configuration';
                } else {
                    msg = error.message;
                }

                if (root.showError) root.showError(msg);
                return null;
            }
        }

        function _generateReport(endpoint, idParam, panelClass, eventName) {
            return async function(id) {
                if (!id) {
                    if (root.showError) root.showError(idParam + ' not found');
                    return;
                }
                var payload = {};
                payload[idParam] = id;
                var result = await callAPI(endpoint, payload, panelClass.replace('PDFPanel', '') + ' report generated!');
                if (result && result.pdf_base64) {
                    if (root[panelClass] && typeof root[panelClass].show === 'function') {
                        root[panelClass].show(id, result.pdf_base64);
                    } else {
                        var event = new CustomEvent(eventName, {
                            detail: { pdfBase64: result.pdf_base64 },
                            bubbles: true
                        });
                        event.detail[idParam] = id;
                        root.document.dispatchEvent(event);
                    }
                }
                return result;
            };
        }

        var generateReport = _generateReport(
            BACKEND.endpoints.property_report, 'propertyId', 'PropertyPDFPanel', 'propertyPdfReady'
        );
        var generateGaugeReport = _generateReport(
            BACKEND.endpoints.gauge_report, 'gaugeId', 'GaugePDFPanel', 'gaugePdfReady'
        );
        var generateMortgageReport = _generateReport(
            BACKEND.endpoints.mortgage_report, 'propertyId', 'PropertyPDFPanel', 'propertyPdfReady'
        );
        var generateCommercialReport = _generateReport(
            BACKEND.endpoints.commercial_report, 'propertyId', 'PropertyPDFPanel', 'propertyPdfReady'
        );

        function viewGaugeStorms(gaugeId) {
            if (!gaugeId) {
                if (root.showError) root.showError('Gauge ID not found');
                return;
            }

            if (root.GaugeStormAnalysis && typeof root.GaugeStormAnalysis.show === 'function') {
                root.GaugeStormAnalysis.show(gaugeId);
            } else {
                console.log('Requesting storm analysis for:', gaugeId);
                var event = new CustomEvent('gaugeStormRequested', {
                    detail: { gaugeId: gaugeId },
                    bubbles: true
                });
                root.document.dispatchEvent(event);

                if (root.showInfo) root.showInfo('Loading storm scenarios for ' + gaugeId + '...');
            }
        }

        function viewHazardCurve(gaugeId) {
            if (!gaugeId) {
                if (root.showError) root.showError('Gauge ID not found');
                return;
            }

            if (root.GaugeHazardCurve && typeof root.GaugeHazardCurve.show === 'function') {
                root.GaugeHazardCurve.show(gaugeId);
            } else {
                console.log('Requesting hazard curve for:', gaugeId);
                var event = new CustomEvent('hazardCurveRequested', {
                    detail: { gaugeId: gaugeId },
                    bubbles: true
                });
                root.document.dispatchEvent(event);

                if (root.showInfo) root.showInfo('Loading hazard curve for ' + gaugeId + '...');
            }
        }

        function viewGaugeHistory(gaugeId) {
            if (!gaugeId) {
                if (root.showError) root.showError('Gauge ID not found');
                return;
            }

            if (root.GaugeGraphInteraction && typeof root.GaugeGraphInteraction.show === 'function') {
                root.GaugeGraphInteraction.show(gaugeId);
            } else {
                console.log('Requesting gauge history for:', gaugeId);
                var event = new CustomEvent('gaugeHistoryRequested', {
                    detail: { gaugeId: gaugeId },
                    bubbles: true
                });
                root.document.dispatchEvent(event);

                if (root.showInfo) root.showInfo('Loading history for ' + gaugeId + '...');
            }
        }

        function viewPropertyStorms(propertyId) {
            if (!propertyId) {
                if (root.showError) root.showError('Property ID not found');
                return;
            }

            if (root.PropertyStormAnalysis && typeof root.PropertyStormAnalysis.show === 'function') {
                root.PropertyStormAnalysis.show(propertyId);
            } else {
                console.log('Requesting property storm analysis for:', propertyId);
                var event = new CustomEvent('propertyStormRequested', {
                    detail: { propertyId: propertyId },
                    bubbles: true
                });
                root.document.dispatchEvent(event);

                if (root.showInfo) root.showInfo('Loading storm scenarios for ' + propertyId + '...');
            }
        }

        function viewPropertyHazard(propertyId) {
            if (!propertyId) {
                if (root.showError) root.showError('Property ID not found');
                return;
            }

            if (root.PropertyHazardCurvePanel && typeof root.PropertyHazardCurvePanel.show === 'function') {
                root.PropertyHazardCurvePanel.show(propertyId);
            } else {
                console.log('Requesting property hazard curve for:', propertyId);
                var event = new CustomEvent('propertyHazardRequested', {
                    detail: { propertyId: propertyId },
                    bubbles: true
                });
                root.document.dispatchEvent(event);

                if (root.showInfo) root.showInfo('Loading PRS pricing for ' + propertyId + '...');
            }
        }

        function showGaugeBlotter(gaugeId, gaugeName) {
            if (!gaugeId) {
                if (root.showError) root.showError('Gauge ID not found');
                return;
            }

            // Open Trading Desk → Blotter tab → filtered by gauge
            if (root.TradingDesk && typeof root.TradingDesk.show === 'function') {
                root.TradingDesk.show();
                // Small delay to let panel render, then apply filter
                setTimeout(function() {
                    if (root.tdApplyFilter) {
                        var f = {gauge_id: gaugeId};
                        if (gaugeName) f.gauge_name = gaugeName;
                        root.tdApplyFilter(f);
                    }
                }, 300);
            } else {
                if (root.showInfo) root.showInfo('Trading desk not available');
            }
        }

        function viewPropertyDetails(propertyId) {
            return generateReport(propertyId);
        }

        function viewCommercialDetails(propertyId) {
            // "Commercial Details" right-click action → reuse the
            // PDF-report code path.
            return generateCommercialReport(propertyId);
        }

        function viewCommercialStorms(propertyId) {
            // "View Storm Scenarios" on a commercial marker. The
            // PropertyStormAnalysis panel itself detects the CPROP-
            // prefix and fetches /api/v1/commercial/<id>/storms instead
            // of the residential endpoint, so this handler is the same
            // shape as viewPropertyStorms — no per-asset-type branching
            // here.
            if (!propertyId) {
                if (root.showError) root.showError('Property ID not found');
                return;
            }
            if (root.PropertyStormAnalysis && typeof root.PropertyStormAnalysis.show === 'function') {
                root.PropertyStormAnalysis.show(propertyId);
            } else {
                var event = new CustomEvent('propertyStormRequested', {
                    detail: { propertyId: propertyId },
                    bubbles: true
                });
                root.document.dispatchEvent(event);
                if (root.showInfo) root.showInfo('Loading storm scenarios for ' + propertyId + '...');
            }
        }

        async function checkBackendHealth() {
            try {
                var response = await fetch(BACKEND.endpoints.health_check, {
                    method: 'GET',
                    mode: 'cors',
                    headers: {'Accept': 'application/json'}
                });

                if (response.ok) {
                    console.log('Backend healthy');
                    return true;
                }
                console.log('Backend error:', response.status);
                return false;
            } catch (e) {
                console.log('Backend unreachable:', e.message);
                return false;
            }
        }


        function getMapInstance() {
            var mapKey = Object.keys(root).find(function(k) { return k.startsWith('map_'); });
            if (mapKey) return root[mapKey];
            if (typeof root.map !== 'undefined') return root.map;
            if (typeof root.mapInstance !== 'undefined') return root.mapInstance;
            return null;
        }

        return {
            callAPI: callAPI,
            generateReport: generateReport,
            generateGaugeReport: generateGaugeReport,
            generateMortgageReport: generateMortgageReport,
            generateCommercialReport: generateCommercialReport,
            viewGaugeStorms: viewGaugeStorms,
            viewHazardCurve: viewHazardCurve,
            viewGaugeHistory: viewGaugeHistory,
            viewPropertyStorms: viewPropertyStorms,
            viewPropertyHazard: viewPropertyHazard,
            viewPropertyDetails: viewPropertyDetails,
            viewCommercialDetails: viewCommercialDetails,
            viewCommercialStorms: viewCommercialStorms,
            showGaugeBlotter: showGaugeBlotter,
            checkBackendHealth: checkBackendHealth,
            getMapInstance: getMapInstance
        };
    }

    // Node.js / Jest export
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = { createBackendHandler: createBackendHandler };
    }

    // Browser auto-init
    if (typeof root !== 'undefined' && root.document && root.__BACKEND_CONFIG) {
        var api = createBackendHandler(root.__BACKEND_CONFIG);
        root.generateReport = api.generateReport;
        root.generateGaugeReport = api.generateGaugeReport;
        root.generateMortgageReport = api.generateMortgageReport;
        root.generateCommercialReport = api.generateCommercialReport;
        root.viewGaugeStorms = api.viewGaugeStorms;
        root.viewHazardCurve = api.viewHazardCurve;
        root.viewGaugeHistory = api.viewGaugeHistory;
        root.viewPropertyStorms = api.viewPropertyStorms;
        root.viewPropertyHazard = api.viewPropertyHazard;
        root.viewPropertyDetails = api.viewPropertyDetails;
        root.viewCommercialDetails = api.viewCommercialDetails;
        root.viewCommercialStorms = api.viewCommercialStorms;
        root.showGaugeBlotter = api.showGaugeBlotter;
        root.checkBackendHealth = api.checkBackendHealth;
        root.getMapInstance = api.getMapInstance;
        if (root.console) root.console.log('Backend handler ready:', root.__BACKEND_CONFIG.url);
        setTimeout(api.checkBackendHealth, 1000);
    }

})(typeof window !== 'undefined' ? window : (typeof global !== 'undefined' ? global : this));
