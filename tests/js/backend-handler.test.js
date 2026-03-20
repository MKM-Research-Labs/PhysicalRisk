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

const { createBackendHandler } = require('../../src/static/js/backend-handler');

describe('BackendHandler', () => {
    let handler;
    const endpoints = {
        property_report: '/api/v1/generate_property_report',
        gauge_report: '/api/v1/generate_gauge_report',
        health_check: '/health'
    };

    beforeEach(() => {
        document.body.innerHTML = '';
        jest.clearAllMocks();
        global.fetch = jest.fn();
        global.showLoading = jest.fn();
        global.showSuccess = jest.fn();
        global.showError = jest.fn();
        global.showInfo = jest.fn();

        handler = createBackendHandler({
            url: 'http://localhost:5013',
            endpoints: endpoints,
            timeout: 30000
        });
    });

    afterEach(() => {
        delete global.showLoading;
        delete global.showSuccess;
        delete global.showError;
        delete global.showInfo;
    });

    test('callAPI() POSTs with correct headers, body, URL', async () => {
        global.fetch.mockResolvedValue({
            ok: true,
            json: () => Promise.resolve({ status: 'success', message: 'Done' })
        });

        await handler.callAPI('/api/test', { key: 'val' }, 'Test OK');

        expect(global.fetch).toHaveBeenCalledWith(
            'http://localhost:5013/api/test',
            expect.objectContaining({
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
                body: JSON.stringify({ key: 'val' }),
                mode: 'cors'
            })
        );
    });

    test('callAPI() calls showLoading before request', async () => {
        global.fetch.mockResolvedValue({
            ok: true,
            json: () => Promise.resolve({ status: 'success' })
        });

        await handler.callAPI('/api/test', {}, 'OK');
        expect(global.showLoading).toHaveBeenCalledWith('Processing request...');
    });

    test('callAPI() calls showSuccess on success response', async () => {
        global.fetch.mockResolvedValue({
            ok: true,
            json: () => Promise.resolve({ status: 'success', message: 'Report ready' })
        });

        await handler.callAPI('/api/test', {}, 'Report generated!');
        expect(global.showSuccess).toHaveBeenCalledWith(expect.stringContaining('Report generated!'));
    });

    test('callAPI() calls showError on error response', async () => {
        global.fetch.mockResolvedValue({
            ok: true,
            json: () => Promise.resolve({ status: 'error', message: 'Not found' })
        });

        await handler.callAPI('/api/test', {}, 'OK');
        expect(global.showError).toHaveBeenCalledWith('Not found');
    });

    test('callAPI() shows showInfo with file_path after delay', async () => {
        jest.useFakeTimers();
        global.fetch.mockResolvedValue({
            ok: true,
            json: () => Promise.resolve({ status: 'success', file_path: '/tmp/report.pdf' })
        });

        await handler.callAPI('/api/test', {}, 'OK');
        jest.advanceTimersByTime(2100);
        expect(global.showInfo).toHaveBeenCalledWith(expect.stringContaining('/tmp/report.pdf'));
        jest.useRealTimers();
    });

    test('callAPI() handles non-ok HTTP', async () => {
        global.fetch.mockResolvedValue({
            ok: false,
            status: 500,
            text: () => Promise.resolve('Internal Server Error')
        });

        const result = await handler.callAPI('/api/test', {}, 'OK');
        expect(result).toBeNull();
        expect(global.showError).toHaveBeenCalledWith(expect.stringContaining('HTTP 500'));
    });

    test('callAPI() handles fetch/network errors with friendly message', async () => {
        global.fetch.mockRejectedValue(new Error('fetch failed'));

        const result = await handler.callAPI('/api/test', {}, 'OK');
        expect(result).toBeNull();
        expect(global.showError).toHaveBeenCalledWith(expect.stringContaining('Cannot connect'));
    });

    test('callAPI() handles CORS errors with specific message', async () => {
        global.fetch.mockRejectedValue(new Error('CORS policy blocked'));

        const result = await handler.callAPI('/api/test', {}, 'OK');
        expect(result).toBeNull();
        expect(global.showError).toHaveBeenCalledWith(expect.stringContaining('CORS'));
    });

    test('generateReport() calls callAPI with property_report endpoint', async () => {
        global.fetch.mockResolvedValue({
            ok: true,
            json: () => Promise.resolve({ status: 'success' })
        });

        await handler.generateReport('PROP-abc123');
        expect(global.fetch).toHaveBeenCalledWith(
            expect.stringContaining('/api/v1/generate_property_report'),
            expect.objectContaining({
                body: JSON.stringify({ propertyId: 'PROP-abc123' })
            })
        );
    });

    test('generateReport(null) calls showError', async () => {
        await handler.generateReport(null);
        expect(global.showError).toHaveBeenCalledWith(expect.stringContaining('Property ID'));
        expect(global.fetch).not.toHaveBeenCalled();
    });

    test('generateGaugeReport() calls callAPI with gauge_report endpoint', async () => {
        global.fetch.mockResolvedValue({
            ok: true,
            json: () => Promise.resolve({ status: 'success' })
        });

        await handler.generateGaugeReport('GAUGE-def456');
        expect(global.fetch).toHaveBeenCalledWith(
            expect.stringContaining('/api/v1/generate_gauge_report'),
            expect.objectContaining({
                body: JSON.stringify({ gaugeId: 'GAUGE-def456' })
            })
        );
    });

    test('generateGaugeReport(null) calls showError', async () => {
        await handler.generateGaugeReport(null);
        expect(global.showError).toHaveBeenCalledWith(expect.stringContaining('Gauge ID'));
        expect(global.fetch).not.toHaveBeenCalled();
    });

    test('viewHazardCurve() dispatches hazardCurveRequested CustomEvent', () => {
        const listener = jest.fn();
        document.addEventListener('hazardCurveRequested', listener);

        handler.viewHazardCurve('GAUGE-hazard');

        expect(listener).toHaveBeenCalled();
        const event = listener.mock.calls[0][0];
        expect(event.detail.gaugeId).toBe('GAUGE-hazard');

        document.removeEventListener('hazardCurveRequested', listener);
    });

    test('viewHazardCurve(null) shows error', () => {
        handler.viewHazardCurve(null);
        expect(global.showError).toHaveBeenCalled();
    });

    test('viewHazardCurve() calls GaugeHazardCurve.show if available', () => {
        const mockShow = jest.fn();
        global.GaugeHazardCurve = { show: mockShow };

        handler.viewHazardCurve('GAUGE-test');

        expect(mockShow).toHaveBeenCalledWith('GAUGE-test');

        delete global.GaugeHazardCurve;
    });

    test('viewGaugeHistory() dispatches gaugeHistoryRequested CustomEvent', () => {
        const listener = jest.fn();
        document.addEventListener('gaugeHistoryRequested', listener);

        handler.viewGaugeHistory('GAUGE-hist');

        expect(listener).toHaveBeenCalled();
        const event = listener.mock.calls[0][0];
        expect(event.detail.gaugeId).toBe('GAUGE-hist');

        document.removeEventListener('gaugeHistoryRequested', listener);
    });

    test('viewPropertyDetails() opens correct marker popup', () => {
        const openPopup = jest.fn();
        const mockMap = {
            eachLayer: function(cb) {
                // Create a mock marker that passes instanceof check
                const marker = Object.create(L.Marker.prototype);
                marker._markerId = 'PROP-abc';
                marker.openPopup = openPopup;
                cb(marker);
            }
        };
        global.map_test = mockMap;

        handler.viewPropertyDetails('PROP-abc');
        expect(openPopup).toHaveBeenCalled();

        delete global.map_test;
    });

    test('checkBackendHealth() returns true on 200', async () => {
        global.fetch.mockResolvedValue({ ok: true });
        const result = await handler.checkBackendHealth();
        expect(result).toBe(true);
    });

    test('checkBackendHealth() calls correct endpoint URL', async () => {
        global.fetch.mockResolvedValue({ ok: true });
        await handler.checkBackendHealth();
        expect(global.fetch).toHaveBeenCalledWith(
            'http://localhost:5013/health',
            expect.objectContaining({ method: 'GET', mode: 'cors' })
        );
    });

    test('checkBackendHealth() returns false on error', async () => {
        global.fetch.mockRejectedValue(new Error('Network error'));
        const result = await handler.checkBackendHealth();
        expect(result).toBe(false);
    });

    test('checkBackendHealth() fails gracefully when health_check endpoint missing', async () => {
        const handlerNoHealth = createBackendHandler({
            url: 'http://localhost:5013',
            endpoints: { property_report: '/api/v1/generate_property_report' },
            timeout: 30000
        });
        global.fetch.mockRejectedValue(new TypeError('URL is not valid'));
        const result = await handlerNoHealth.checkBackendHealth();
        expect(result).toBe(false);
    });

    test('getMapInstance() finds window.map_* key', () => {
        const mockMap = { id: 'test-map' };
        global.map_abc123 = mockMap;

        const result = handler.getMapInstance();
        expect(result).toBe(mockMap);

        delete global.map_abc123;
    });
});
