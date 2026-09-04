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

// The property PRS commit path — the second money path named in the Phase 3
// order. Like its gauge twin, phc_prs_tail.js is a concat fragment reading
// phcData, phcPanel and computePropertyPRSCashflows from the IIFE the Python
// loader splices it into, so the test stages those before requiring it.

const FRAGMENT = '../../src/static/js/property/phc_prs_tail';

const CASHFLOWS = {
    triggerKey: 'moderate',
    notional: 750000,
    tenor: 5,
    spreadBps: 120.5,
    fairSpreadBps: 118.0,
    npv: 402.75,
    totalPremPV: 9000,
    totalProtPV: 8597.25,
    riskyAnnuity: 4.4,
    yieldCurve: 'GBP-SONIA',
    recovery: 0.4,
    avgBasis: -12.3,
    gaugeComponents: [{ gauge_id: 'GAUGE-aaa', weight: 0.7 }],
    periods: [{ n: 1 }, { n: 2 }],
    selectedZone: 'Zone 3a',
    actualZone: 'Zone 2',
    terrainDelta: 4.5,
};

function loadFragment(overrides = {}) {
    global.computePropertyPRSCashflows = overrides.computePropertyPRSCashflows
        || jest.fn(() => ({ ...CASHFLOWS, ...(overrides.cashflows || {}) }));
    global.phcData = 'phcData' in overrides
        ? overrides.phcData
        : { nearest_gauges: [{ gauge_id: 'GAUGE-bbb', gauge_name: 'Teddington' }] };
    global.phcPanel = 'phcPanel' in overrides
        ? overrides.phcPanel
        : { dataset: { propertyId: 'PROP-c52188a4' } };
    jest.isolateModules(() => { require(FRAGMENT); });
    return window.commitPropertyPRSTrade;
}

const respond = (body) => ({ json: () => Promise.resolve(body) });

describe('commitPropertyPRSTrade', () => {
    let adminFetch;

    beforeEach(() => {
        document.body.innerHTML = `
            <button id="phc-commit-btn">Commit</button>
            <select id="phc-counterparty">
              <option value="CTPY-REIT-001">Landsec REIT</option>
            </select>
            <div id="phc-status"></div>`;
        window.__BACKEND_CONFIG = { url: 'http://localhost:5013' };
        adminFetch = jest.fn(() => Promise.resolve(
            respond({ status: 'success', swap_id: 'PSWAP-001' })));
        window.__mkmAdminFetch = adminFetch;
        global.fetch = jest.fn(() => Promise.resolve(
            respond({ status: 'success', gauge_ids: ['GAUGE-aaa'] })));
        window.showSuccess = jest.fn();
        window.showError = jest.fn();
        window.setActiveGauges = jest.fn();
        window._tdPreBlotter = { stale: true };
        jest.spyOn(console, 'error').mockImplementation(() => {});
    });

    afterEach(() => {
        jest.restoreAllMocks();
        delete window.PropertyPDFPanel;
    });

    test('posts the priced property trade with its zone and basis fields', async () => {
        await loadFragment()();

        const [url, opts] = adminFetch.mock.calls[0];
        expect(url).toBe('http://localhost:5013/api/v1/prs/commit');
        const payload = JSON.parse(opts.body);
        expect(payload).toMatchObject({
            property_id: 'PROP-c52188a4',
            counterparty_id: 'CTPY-REIT-001',
            notional: 750000,
            spread_bps: 120.5,
            avg_basis_bps: -12.3,
            ea_flood_zone: 'Zone 3a',
            ea_flood_zone_actual: 'Zone 2',
            terrain_delta_bps: 4.5,
        });
    });

    test('the trigger key is mapped to the wire name', async () => {
        // 'moderate' is the UI's word; the API speaks 'warning'.
        await loadFragment()();
        expect(JSON.parse(adminFetch.mock.calls[0][1].body).trigger)
            .toBe('warning');
    });

    test('an unmapped trigger key passes through unchanged', async () => {
        await loadFragment({ cashflows: { triggerKey: 'catastrophic' } })();
        expect(JSON.parse(adminFetch.mock.calls[0][1].body).trigger)
            .toBe('catastrophic');
    });

    test('the primary gauge component wins over the nearest gauge', async () => {
        await loadFragment()();
        expect(JSON.parse(adminFetch.mock.calls[0][1].body).gauge_id)
            .toBe('GAUGE-aaa');
    });

    test('it falls back to the nearest gauge when no components are priced', async () => {
        await loadFragment({ cashflows: { gaugeComponents: [] } })();
        const payload = JSON.parse(adminFetch.mock.calls[0][1].body);
        expect(payload.gauge_id).toBe('GAUGE-bbb');
        expect(payload.gauge_name).toBe('Teddington');
    });

    test('a property with no gauge at all is never committed', async () => {
        // Without a gauge the trade has nothing to settle against, so this
        // must fail loudly rather than post an empty gauge_id.
        const commit = loadFragment({
            cashflows: { gaugeComponents: [] },
            phcData: { nearest_gauges: [] },
        });
        await commit();

        expect(adminFetch).not.toHaveBeenCalled();
        expect(window.showError).toHaveBeenCalledWith(
            expect.stringContaining('gauge_id is required'));
        expect(document.getElementById('phc-commit-btn').disabled).toBe(false);
    });

    test('the gauge name falls back to the id when unnamed', async () => {
        await loadFragment({
            phcData: { nearest_gauges: [{ gauge_id: 'GAUGE-bbb' }] },
        })();
        expect(JSON.parse(adminFetch.mock.calls[0][1].body).gauge_name)
            .toBe('GAUGE-aaa');
    });

    test('a rejected commit restores the button and reports the reason', async () => {
        adminFetch.mockResolvedValue(respond({
            status: 'error', message: 'REIT counterparty not permitted' }));

        await loadFragment()();

        const btn = document.getElementById('phc-commit-btn');
        expect(btn.disabled).toBe(false);
        expect(btn.textContent).toBe('Commit');
        expect(window.showError).toHaveBeenCalledWith(
            expect.stringContaining('REIT counterparty not permitted'));
    });

    test('the confirmation PDF opens in a window without the panel', async () => {
        window.open = jest.fn();
        adminFetch.mockResolvedValue(respond({
            status: 'success', swap_id: 'PSWAP-002', pdf_base64: 'JVBERi0=' }));

        await loadFragment()();

        expect(window.open).toHaveBeenCalledWith(
            'http://localhost:5013/api/v1/prs/trades/PSWAP-002/pdf', '_blank');
    });

    test('committing invalidates the cached blotter', async () => {
        await loadFragment()();
        expect(window._tdPreBlotter).toBeNull();
        expect(document.getElementById('phc-status').textContent)
            .toContain('PSWAP-001');
    });

    test('a failed active-gauge refresh does not undo the commit', async () => {
        global.fetch = jest.fn(() => Promise.reject(new Error('network')));
        await loadFragment()();
        expect(window.showSuccess).toHaveBeenCalled();
        expect(window.showError).not.toHaveBeenCalled();
        expect(window._tdPreBlotter).toBeNull();
    });
});
