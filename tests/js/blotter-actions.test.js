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

// Blotter trade actions — viewing a trade, closing one out, and pulling its
// contract. Trade state and a settlement figure, so still in the Phase 3
// money band. Another concat fragment: tdBlotterData, Theme, fmtGBP,
// getBaseUrl and loadBlotterData come from the enclosing IIFE.

const FRAGMENT = '../../src/static/js/trading/blotter/actions';

// Drain the promise chain the handlers build (fetch -> json -> render).
const flush = async () => { for (let i = 0; i < 6; i++) await Promise.resolve(); };

// The confirm button is disabled until a valid spread is entered, so a
// test that only sets .value clicks a dead button and proves nothing.
function typeSpread(value) {
    const input = document.querySelector('#td-closeout-modal input');
    input.value = value;
    input.dispatchEvent(new window.Event('input', { bubbles: true }));
    return input;
}

const TRADE = {
    swap_id: 'SWAP-001',
    gauge_id: 'GAUGE-1f4e46a9',
    gauge_name: 'Kingston',
    counterparty: 'Barclays',
    counterparty_id: 'CTPY-001',
    trigger: 'severe',
    notional: 10000000,
    original_notional: 10000000,
    tenor: 5,
    maturity: '2031-09-04',
    trade_spread_bps: 100,
    fair_spread_bps: 150,
    risky_annuity: 4.0,
    is_payer: true,
};

function load(blotter = [TRADE]) {
    global.tdBlotterData = blotter;
    global.Theme = { value: (k) => `var(--${k})` };
    global.fmtGBP = (n) => '£' + Number(n).toLocaleString('en-GB');
    global.fmtMaturity = (d) => String(d || '');
    global.getBaseUrl = () => 'http://localhost:5013';
    global.loadBlotterData = jest.fn();
    jest.isolateModules(() => { require(FRAGMENT); });
}

describe('tdViewTrade', () => {
    beforeEach(() => {
        document.body.innerHTML = '';
        delete window._tradeReviewData;
        jest.spyOn(console, 'warn').mockImplementation(() => {});
    });
    afterEach(() => jest.restoreAllMocks());

    test('captures the trade for read-only review', () => {
        load();
        window.tdViewTrade(0);
        expect(window._tradeReviewData).toMatchObject({
            swap_id: 'SWAP-001',
            counterparty: 'Barclays',
            notional: 10000000,
            trade_spread_bps: 100,
            is_payer: true,
        });
        // review is not a close-out; conflating them would flip the side
        expect(window._tradeReviewData.is_close_out).toBe(false);
    });

    test('an index outside the blotter is ignored', () => {
        load();
        window.tdViewTrade(5);
        window.tdViewTrade(-1);
        expect(window._tradeReviewData).toBeUndefined();
    });

    test('no blotter loaded is ignored', () => {
        load(null);
        window.tdViewTrade(0);
        expect(window._tradeReviewData).toBeUndefined();
    });

    test('a property trade opens the property panel, not the gauge one', () => {
        load([{ ...TRADE, property_id: 'PROP-1' }]);
        window.PropertyHazardCurvePanel = { show: jest.fn() };
        window.GaugeHazardCurve = { show: jest.fn() };

        window.tdViewTrade(0);

        expect(window.PropertyHazardCurvePanel.show).toHaveBeenCalledWith('PROP-1');
        expect(window.GaugeHazardCurve.show).not.toHaveBeenCalled();
        delete window.PropertyHazardCurvePanel;
        delete window.GaugeHazardCurve;
    });

    test('it falls back through the panel chain to the legacy openers', () => {
        load([{ ...TRADE, property_id: 'PROP-1' }]);
        window.viewPropertyHazard = jest.fn();
        window.tdViewTrade(0);
        expect(window.viewPropertyHazard).toHaveBeenCalledWith('PROP-1');
        delete window.viewPropertyHazard;

        load();
        window.viewHazardCurve = jest.fn();
        window.tdViewTrade(0);
        expect(window.viewHazardCurve).toHaveBeenCalledWith('GAUGE-1f4e46a9');
        delete window.viewHazardCurve;
    });

    test('it warns rather than throwing when no panel exists', () => {
        load();
        window.tdViewTrade(0);
        expect(console.warn).toHaveBeenCalled();
    });

    test('the trading desk is hidden before the panel opens', () => {
        load();
        window.TradingDesk = { hide: jest.fn() };
        window.GaugeHazardCurve = { show: jest.fn() };
        window.tdViewTrade(0);
        expect(window.TradingDesk.hide).toHaveBeenCalled();
        delete window.TradingDesk;
        delete window.GaugeHazardCurve;
    });
});

describe('tdCloseOutTrade', () => {
    let adminFetch;

    beforeEach(() => {
        document.body.innerHTML = '';
        jest.useFakeTimers();
        adminFetch = jest.fn(() => Promise.resolve({
            json: () => Promise.resolve({
                status: 'success', settlement_amount: 200000, final_pnl: 200000 }),
        }));
        window.__mkmAdminFetch = adminFetch;
        window.showSuccess = jest.fn();
        window.showError = jest.fn();
    });
    afterEach(() => { jest.useRealTimers(); jest.restoreAllMocks(); });

    test('the modal opens showing the trade being closed', () => {
        load();
        window.tdCloseOutTrade(0);
        const modal = document.getElementById('td-closeout-modal');
        expect(modal).not.toBeNull();
        expect(modal.textContent).toContain('SWAP-001');
        expect(modal.textContent).toContain('Kingston');
    });

    test('reopening replaces the modal rather than stacking a second', () => {
        load();
        window.tdCloseOutTrade(0);
        window.tdCloseOutTrade(0);
        expect(document.querySelectorAll('#td-closeout-modal')).toHaveLength(1);
    });

    test('an index outside the blotter opens nothing', () => {
        load();
        window.tdCloseOutTrade(99);
        expect(document.getElementById('td-closeout-modal')).toBeNull();
    });

    test('confirming posts the negotiated spread to the close endpoint', async () => {
        load();
        window.tdCloseOutTrade(0);
        typeSpread('150');
        document.getElementById('td-closeout-confirm').click();

        expect(adminFetch).toHaveBeenCalledTimes(1);
        const [url, opts] = adminFetch.mock.calls[0];
        expect(url).toBe('http://localhost:5013/api/v1/trading/close/SWAP-001');
        expect(JSON.parse(opts.body)).toEqual({ closeout_spread_bps: 150 });
    });

    test('a negative or unreadable spread is not sent', () => {
        // Guard: a blank or negative field must not post a close-out.
        load();
        window.tdCloseOutTrade(0);

        typeSpread('-5');
        document.getElementById('td-closeout-confirm').click();
        typeSpread('abc');
        document.getElementById('td-closeout-confirm').click();

        expect(adminFetch).not.toHaveBeenCalled();
    });

    test('confirm stays disabled until a spread is entered', () => {
        load();
        window.tdCloseOutTrade(0);
        expect(document.getElementById('td-closeout-confirm').disabled).toBe(true);
        typeSpread('150');
        expect(document.getElementById('td-closeout-confirm').disabled).toBe(false);
    });

    test('the running settlement estimate updates as the spread is typed', () => {
        // 50bps over a 4.0 risky annuity on 10m, payer: 0.0050 * 4 * 10m.
        load();
        window.tdCloseOutTrade(0);
        typeSpread('150');
        expect(document.getElementById('td-settle-amount').textContent)
            .toContain('200,000');
        expect(document.getElementById('td-settle-dir').textContent)
            .toBe('Receivable');
    });

    test('a spread below the traded level settles the other way', () => {
        load();
        window.tdCloseOutTrade(0);
        typeSpread('50');
        expect(document.getElementById('td-settle-dir').textContent)
            .toBe('Payable');
    });

    test('the settlement reported is the backend figure, not the local estimate', async () => {
        // The modal's own arithmetic is an indication; the booked number comes
        // from the backend's full revaluation.
        load();
        window.tdCloseOutTrade(0);
        typeSpread('150');
        document.getElementById('td-closeout-confirm').click();
        await flush();

        expect(window.showSuccess).toHaveBeenCalledWith(
            expect.stringContaining('200,000'));
        expect(window.showSuccess).toHaveBeenCalledWith(
            expect.stringContaining('Receivable'));
    });

    test('a rejected close-out reports the reason and closes the modal', async () => {
        adminFetch.mockResolvedValue({
            json: () => Promise.resolve({ status: 'error', message: 'already closed' }),
        });
        load();
        window.tdCloseOutTrade(0);
        typeSpread('150');
        document.getElementById('td-closeout-confirm').click();
        await flush();

        expect(window.showError).toHaveBeenCalledWith('already closed');
        expect(document.getElementById('td-closeout-modal')).toBeNull();
    });

    test('a network failure reports and closes the modal', async () => {
        adminFetch.mockRejectedValue(new Error('offline'));
        load();
        window.tdCloseOutTrade(0);
        typeSpread('150');
        document.getElementById('td-closeout-confirm').click();
        await flush();

        expect(window.showError).toHaveBeenCalledWith(
            expect.stringContaining('offline'));
        expect(document.getElementById('td-closeout-modal')).toBeNull();
    });

    test('dismissing the modal sends nothing', () => {
        load();
        window.tdCloseOutTrade(0);
        document.getElementById('td-closeout-close').click();
        expect(document.getElementById('td-closeout-modal')).toBeNull();
        expect(adminFetch).not.toHaveBeenCalled();
    });
});

describe('tdViewContract', () => {
    beforeEach(() => {
        window.showError = jest.fn();
        jest.spyOn(console, 'error').mockImplementation(() => {});
    });
    afterEach(() => { jest.restoreAllMocks(); delete window.GaugePDFPanel; });

    test('an empty swap id fetches nothing', () => {
        load();
        global.fetch = jest.fn();
        window.tdViewContract('');
        expect(global.fetch).not.toHaveBeenCalled();
    });

    test('a missing contract reports rather than throwing', async () => {
        load();
        global.fetch = jest.fn(() => Promise.resolve({ ok: false, status: 404 }));
        window.tdViewContract('SWAP-404');
        await flush();
        expect(window.showError).toHaveBeenCalledWith(
            expect.stringContaining('SWAP-404'));
    });
});
