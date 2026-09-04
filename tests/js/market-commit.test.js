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

// tdCommitMarket — writes curve changes that revalue the whole book.
//
// It queues the dirty yield curve and every dirty hazard key, then POSTs them
// one at a time, accumulating the P&L impact and clearing each dirty flag only
// on a successful response. Nothing here was tested, so a change that dropped
// a queued curve, cleared a flag after a failure, or double-sent one would
// have shown up as a book revalued against curves that were never saved.

const FRAGMENT = '../../src/static/js/trading/market/actions/commit';

// Each commit costs several microtasks (fetch -> json -> handler -> next),
// so a short flush stops the queue partway and undercounts the calls.
const flush = async () => { for (let i = 0; i < 40; i++) await Promise.resolve(); };

function load(state = {}) {
    global.tdYieldDirty = state.yieldDirty || false;
    global.tdYieldCurve = state.yieldCurve || {'1': 0.04, '5': 0.045};
    global.tdHazardDirtyKeys = state.hazardDirty || {};
    global.tdHazardTS = state.hazardTS || {};
    global.fmtGBP = (n) => '£' + Number(n).toLocaleString('en-GB');
    global.Theme = { value: (k) => `var(--${k})` };
    global.getBaseUrl = () => 'http://localhost:5013';
    global.loadMarketData = jest.fn();
    global.switchTab = jest.fn();
    global.tdMarketChart = null;
    jest.isolateModules(() => { require(FRAGMENT); });
}

const ok = (body) => ({ json: () => Promise.resolve(body) });

describe('tdCommitMarket', () => {
    let adminFetch;

    beforeEach(() => {
        document.body.innerHTML = '<button id="td-commit-btn">Commit</button>';
        adminFetch = jest.fn(() => Promise.resolve(ok({
            status: 'success', total_pnl_impact: 1000, affected_trades: 4 })));
        window.__mkmAdminFetch = adminFetch;
        window.showSuccess = jest.fn();
        window.showError = jest.fn();
        window.refreshMainMapFS01 = jest.fn();
        jest.spyOn(console, 'log').mockImplementation(() => {});
        jest.spyOn(console, 'warn').mockImplementation(() => {});
        jest.spyOn(console, 'error').mockImplementation(() => {});
        jest.useFakeTimers();
    });

    afterEach(() => { jest.useRealTimers(); jest.restoreAllMocks(); });

    test('a clean book commits nothing and says so', async () => {
        // The guard that matters most: with no dirty curves there is nothing
        // to save, and posting an empty commit would revalue the book against
        // curves nobody changed.
        load();
        window.tdCommitMarket();
        await flush();

        expect(adminFetch).not.toHaveBeenCalled();
        expect(window.showError).toHaveBeenCalledWith(
            expect.stringContaining('No curve changes'));
        expect(document.getElementById('td-commit-btn').disabled).toBe(false);
    });

    test('a dirty yield curve is posted to the yield endpoint', async () => {
        load({ yieldDirty: true, yieldCurve: {'1': 0.04, '5': 0.05} });
        window.tdCommitMarket();
        await flush();

        expect(adminFetch).toHaveBeenCalledTimes(1);
        const [url, opts] = adminFetch.mock.calls[0];
        expect(url).toContain('/api/v1/trading/yield-curve/commit');
        expect(JSON.parse(opts.body)).toEqual({rates: {'1': 0.04, '5': 0.05}});
        expect(opts.cache).toBe('no-store');
    });

    test('each dirty hazard key is posted with its gauge and trigger', async () => {
        load({
            hazardDirty: {'GAUGE-1:severe': true, 'GAUGE-2:warning': true},
            hazardTS: {'GAUGE-1': {severe: {'1': 0.01}},
                       'GAUGE-2': {warning: {'1': 0.02}}},
        });
        window.tdCommitMarket();
        await flush();

        expect(adminFetch).toHaveBeenCalledTimes(2);
        const bodies = adminFetch.mock.calls.map(c => JSON.parse(c[1].body));
        expect(bodies).toEqual(expect.arrayContaining([
            {gauge_id: 'GAUGE-1', trigger: 'severe', rates: {'1': 0.01}},
            {gauge_id: 'GAUGE-2', trigger: 'warning', rates: {'1': 0.02}},
        ]));
    });

    test('a key marked clean is not sent', async () => {
        load({
            hazardDirty: {'GAUGE-1:severe': true, 'GAUGE-2:warning': false},
            hazardTS: {'GAUGE-1': {severe: {'1': 0.01}}},
        });
        window.tdCommitMarket();
        await flush();
        expect(adminFetch).toHaveBeenCalledTimes(1);
    });

    test('commits are sent one at a time, not in parallel', async () => {
        // Sequential ordering is load-bearing: each response carries the
        // running P&L impact, and overlapping them would interleave the
        // accumulation.
        let inFlight = 0, maxInFlight = 0;
        adminFetch.mockImplementation(() => {
            inFlight += 1;
            maxInFlight = Math.max(maxInFlight, inFlight);
            return Promise.resolve(ok({status: 'success'})).then(r => {
                inFlight -= 1;
                return r;
            });
        });
        load({
            yieldDirty: true,
            hazardDirty: {'GAUGE-1:severe': true, 'GAUGE-2:severe': true},
            hazardTS: {'GAUGE-1': {severe: {}}, 'GAUGE-2': {severe: {}}},
        });
        window.tdCommitMarket();
        await flush();

        expect(adminFetch).toHaveBeenCalledTimes(3);
        expect(maxInFlight).toBe(1);
    });

    test('the dirty flags clear only after every commit succeeds', async () => {
        load({ yieldDirty: true });
        window.tdCommitMarket();
        await flush();

        expect(global.tdYieldDirty).toBe(false);
        expect(global.tdHazardDirtyKeys).toEqual({});
        expect(global.loadMarketData).toHaveBeenCalled();
    });

    test('DEFECT: a rejected commit still clears its dirty flag', async () => {
        // Pinning current behaviour, which is wrong.
        //
        // The per-commit handler correctly leaves the flag alone on failure,
        // but the completion branch then runs `tdYieldDirty = false;
        // tdHazardDirtyKeys = {}` unconditionally and reports success. So a
        // refused commit produces an error toast AND a "Committed 1 curve(s)"
        // toast, with every dirty flag cleared — the edit is silently lost and
        // the UI shows saved while the server holds the old curve.
        //
        // Left as-is deliberately: changing what a trading commit does with a
        // partial failure is a product decision, not a test fix. Change this
        // assertion when that decision is made.
        adminFetch.mockResolvedValue(ok({status: 'error', message: 'refused'}));
        load({ hazardDirty: {'GAUGE-1:severe': true},
               hazardTS: {'GAUGE-1': {severe: {'1': 0.01}}} });

        window.tdCommitMarket();
        await flush();

        expect(window.showError).toHaveBeenCalledWith('refused');
        expect(global.tdHazardDirtyKeys['GAUGE-1:severe']).toBeUndefined();
        // ...and it claims success in the same breath:
        expect(window.showSuccess).toHaveBeenCalledWith(
            expect.stringContaining('Committed 1 curve(s)'));
    });

    test('a network failure restores the button and reports it', async () => {
        adminFetch.mockRejectedValue(new Error('offline'));
        load({ yieldDirty: true });

        window.tdCommitMarket();
        await flush();

        expect(window.showError).toHaveBeenCalledWith(
            expect.stringContaining('offline'));
        const btn = document.getElementById('td-commit-btn');
        expect(btn.disabled).toBe(false);
        expect(btn.textContent).toBe('Commit');
    });

    test('the reported P&L impact comes from the server', async () => {
        adminFetch.mockResolvedValue(ok({
            status: 'success', total_pnl_impact: 12345, affected_trades: 7 }));
        load({ yieldDirty: true });

        window.tdCommitMarket();
        await flush();

        expect(window.showSuccess).toHaveBeenCalledWith(
            expect.stringContaining('12,345'));
        expect(window.showSuccess).toHaveBeenCalledWith(
            expect.stringContaining('7 trades revalued'));
    });

    test('a successful commit moves the user to the blotter', async () => {
        load({ yieldDirty: true });
        window.tdCommitMarket();
        await flush();
        jest.advanceTimersByTime(400);
        expect(global.switchTab).toHaveBeenCalledWith('blotter');
        expect(window.refreshMainMapFS01).toHaveBeenCalled();
    });
});
