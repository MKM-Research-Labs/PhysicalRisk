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

// The PRS trade commit path — money and trade state, so first in the Phase 3
// order. ghc_prs_commit.js is a concat FRAGMENT, not a module: the Python
// loader splices it into a larger IIFE, so it reads isCloseOut, hazardData
// and computePRSCashflows as free identifiers from that enclosing scope.
// Staging them as globals before require() reproduces that scope faithfully
// enough to exercise the real code rather than a rewritten copy of it.

const FRAGMENT = '../../src/static/js/gauge/gaugehc/ghc_prs_commit';

const CASHFLOWS = {
    trigger: 'severe',
    notional: 5000000,
    tenor: 3,
    maturityDate: '2029-09-04',
    spreadBps: 78.44,
    fairSpreadBps: 80.0,
    npv: -1234.5,
    totalPremPV: 10000,
    totalProtPV: 8765.5,
    riskyAnnuity: 2.85,
    yieldCurve: 'GBP-SONIA',
    recovery: 0.4,
    isPayer: true,
    periods: [{ n: 1 }, { n: 2 }, { n: 3 }],
};

function loadFragment(overrides = {}) {
    global.isCloseOut = overrides.isCloseOut || false;
    global.closeOutSwapId = overrides.closeOutSwapId || null;
    global.closeOutIsPayer = overrides.closeOutIsPayer || false;
    global.hazardData = 'hazardData' in overrides
        ? overrides.hazardData
        : { gauge_id: 'GAUGE-1f4e46a9', gauge_name: 'Kingston' };
    global.computePRSCashflows = overrides.computePRSCashflows
        || jest.fn(() => CASHFLOWS);
    jest.isolateModules(() => { require(FRAGMENT); });
    return window.commitPRSTrade;
}

function commitResponse(body) {
    return { json: () => Promise.resolve(body) };
}

describe('commitPRSTrade', () => {
    let adminFetch;

    beforeEach(() => {
        document.body.innerHTML = `
            <button id="prs-commit-btn">Commit</button>
            <select id="prs-counterparty">
              <option value="CTPY-001">Barclays</option>
            </select>
            <div id="hazard-status"></div>
            <button id="hazard-blotter-link" disabled></button>`;
        window.__BACKEND_CONFIG = { url: 'http://localhost:5013' };
        adminFetch = jest.fn(() => Promise.resolve(
            commitResponse({ status: 'success', swap_id: 'SWAP-001' })));
        window.__mkmAdminFetch = adminFetch;
        global.fetch = jest.fn(() => Promise.resolve(
            commitResponse({ status: 'success', gauge_ids: ['GAUGE-1f4e46a9'] })));
        window.showSuccess = jest.fn();
        window.showError = jest.fn();
        window.setActiveGauges = jest.fn();
        window._tdPreBlotter = { stale: true };
        jest.spyOn(console, 'error').mockImplementation(() => {});
    });

    afterEach(() => {
        jest.restoreAllMocks();
        delete window.GaugePDFPanel;
        delete window.PropertyPDFPanel;
    });

    test('posts the priced trade to the commit endpoint', async () => {
        await loadFragment()();

        expect(adminFetch).toHaveBeenCalledTimes(1);
        const [url, opts] = adminFetch.mock.calls[0];
        expect(url).toBe('http://localhost:5013/api/v1/prs/commit');
        expect(opts.method).toBe('POST');

        const payload = JSON.parse(opts.body);
        expect(payload).toMatchObject({
            gauge_id: 'GAUGE-1f4e46a9',
            gauge_name: 'Kingston',
            counterparty_id: 'CTPY-001',
            counterparty_name: 'Barclays',
            trigger: 'severe',
            notional: 5000000,
            tenor: 3,
            spread_bps: 78.44,
            npv: -1234.5,
            payer: true,
        });
        expect(payload.cashflows).toHaveLength(3);
    });

    test('an unpriceable trade is never sent', async () => {
        // computePRSCashflows returning null is the guard against committing
        // a trade the pricer could not value.
        const commit = loadFragment({ computePRSCashflows: jest.fn(() => null) });
        await commit();

        expect(adminFetch).not.toHaveBeenCalled();
        expect(document.getElementById('prs-commit-btn').disabled).toBe(false);
    });

    test('the button is disabled while the commit is in flight', async () => {
        let release;
        adminFetch.mockImplementation(() => new Promise((res) => {
            release = () => res(commitResponse({ status: 'success', swap_id: 'S1' }));
        }));

        const pending = loadFragment()();
        expect(document.getElementById('prs-commit-btn').disabled).toBe(true);
        expect(document.getElementById('prs-commit-btn').textContent)
            .toBe('Committing...');
        release();
        await pending;
    });

    test('a close-out carries the original swap id and flips the side', async () => {
        await loadFragment({
            isCloseOut: true,
            closeOutSwapId: 'SWAP-ORIG',
            closeOutIsPayer: false,
        })();

        const payload = JSON.parse(adminFetch.mock.calls[0][1].body);
        expect(payload.close_out_of).toBe('SWAP-ORIG');
        // the close-out takes the ORIGINAL trade's side, not the pricer's
        expect(payload.payer).toBe(false);
        expect(window.showSuccess).toHaveBeenCalledWith(
            expect.stringContaining('SWAP-ORIG'));
    });

    test('a rejected commit restores the button and reports the reason', async () => {
        adminFetch.mockResolvedValue(commitResponse({
            status: 'error', message: 'counterparty limit breached' }));

        await loadFragment()();

        const btn = document.getElementById('prs-commit-btn');
        expect(btn.disabled).toBe(false);
        expect(btn.textContent).toBe('Commit');
        expect(window.showError).toHaveBeenCalledWith(
            expect.stringContaining('counterparty limit breached'));
        expect(window.showSuccess).not.toHaveBeenCalled();
    });

    test('a rejected close-out restores the close-out label', async () => {
        adminFetch.mockResolvedValue(commitResponse({ status: 'error' }));
        await loadFragment({ isCloseOut: true, closeOutSwapId: 'S9' })();
        expect(document.getElementById('prs-commit-btn').textContent)
            .toBe('Close Out');
    });

    test('the confirmation PDF goes to the gauge panel when present', async () => {
        adminFetch.mockResolvedValue(commitResponse({
            status: 'success', swap_id: 'SWAP-001', pdf_base64: 'JVBERi0=' }));
        window.GaugePDFPanel = { show: jest.fn() };
        window.PropertyPDFPanel = { show: jest.fn() };

        await loadFragment()();

        expect(window.GaugePDFPanel.show)
            .toHaveBeenCalledWith('SWAP-001', 'JVBERi0=');
        expect(window.PropertyPDFPanel.show).not.toHaveBeenCalled();
    });

    test('it falls back to the property panel, then to a new window', async () => {
        adminFetch.mockResolvedValue(commitResponse({
            status: 'success', swap_id: 'SWAP-001', pdf_base64: 'JVBERi0=' }));
        window.PropertyPDFPanel = { show: jest.fn() };
        await loadFragment()();
        expect(window.PropertyPDFPanel.show).toHaveBeenCalled();

        jest.clearAllMocks();
        delete window.PropertyPDFPanel;
        window.open = jest.fn();
        adminFetch.mockResolvedValue(commitResponse({
            status: 'success', swap_id: 'SWAP-002', pdf_base64: 'JVBERi0=' }));
        await loadFragment()();
        expect(window.open).toHaveBeenCalledWith(
            'http://localhost:5013/api/v1/prs/trades/SWAP-002/pdf', '_blank');
    });

    test('committing invalidates the cached blotter', async () => {
        // A stale blotter after a commit shows a book missing the trade just
        // written, which is the kind of wrong a trader acts on.
        await loadFragment()();
        expect(window._tdPreBlotter).toBeNull();
    });

    test('the active-gauge refresh enables the blotter link', async () => {
        await loadFragment()();
        expect(window.setActiveGauges)
            .toHaveBeenCalledWith(['GAUGE-1f4e46a9']);
        expect(document.getElementById('hazard-blotter-link').disabled)
            .toBe(false);
    });

    test('a failed active-gauge refresh does not undo the commit', async () => {
        // The trade is already written; a failure refreshing a sidebar must
        // not report the commit as failed.
        global.fetch = jest.fn(() => Promise.reject(new Error('network')));

        await loadFragment()();

        expect(window.showSuccess).toHaveBeenCalled();
        expect(window.showError).not.toHaveBeenCalled();
        expect(document.getElementById('hazard-status').textContent)
            .toContain('SWAP-001');
    });

    test('a missing hazard payload commits with empty gauge fields', async () => {
        await loadFragment({ hazardData: null })();
        const payload = JSON.parse(adminFetch.mock.calls[0][1].body);
        expect(payload.gauge_id).toBe('');
        expect(payload.gauge_name).toBe('');
    });
});
