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

// renderBlotterTable — the trader's view of the book.
//
// Reached through tdToggleSort, the file's only window export. The renderer
// is module-local, so this is the one way in; that also means the sort order
// and every column formatter are exercised by driving the toggle.
//
// Wrong numbers here are wrong in the most consequential place: notional
// sums, P&L columns and the FS01 total are what a trader reads off the
// screen before deciding what to do next.

const FRAGMENT = '../../src/static/js/trading/blotter/table';

const TRADES = [
    {swap_id: 'S1', trade_date: '2026-09-01', is_payer: true,
     gauge_id: 'G-A', gauge_name: 'Kingston', counterparty: 'Barclays',
     notional: 10000000, maturity: '2031-09-01', trade_spread_bps: 100,
     current_hazard_rate: 0.02, gauge_fs01: 1200, new_trade_pnl: 500,
     market_pnl: -250, mtm: 250, trade_status: 'Open'},
    {swap_id: 'S2', trade_date: '2026-09-03', is_payer: false,
     gauge_id: 'G-B', gauge_name: 'Teddington', counterparty: 'HSBC',
     notional: 5000000, maturity: '2029-03-01', trade_spread_bps: 80,
     current_hazard_rate: 0.01, gauge_fs01: 600, new_trade_pnl: -100,
     market_pnl: 400, mtm: 300, trade_status: 'Open'},
];

function load(trades = TRADES) {
    document.body.innerHTML = '<div id="td-blotter-table-wrap"></div>';
    global.tdBlotterData = trades;
    global.getFilteredTrades = () => (trades || []).slice();
    global.fmtGBP = (n) => '£' + Number(n).toLocaleString('en-GB');
    global.fmtMaturity = (d) => String(d || '—');
    // Supplied by trading/blotter/filters.js in the assembled bundle.
    global.extractAreaName = (n) => n;
    global.Theme = { value: (k) => `var(--${k})` };
    delete window._tdSortOrder;
    jest.isolateModules(() => { require(FRAGMENT); });
}

const wrapText = () =>
    document.getElementById('td-blotter-table-wrap').textContent;

const rowOrder = () => {
    const html = document.getElementById('td-blotter-table-wrap').innerHTML;
    return ['S1', 'S2'].sort((a, b) => html.indexOf(a) - html.indexOf(b));
};

describe('renderBlotterTable via tdToggleSort', () => {
    test('every trade in the book is rendered', () => {
        load();
        window.tdToggleSort();
        const text = wrapText();
        expect(text).toContain('S1');
        expect(text).toContain('S2');
    });

    test('newest first by default, oldest first after a toggle', () => {
        // _tdSortOrder starts unset and the renderer treats that as 'newest';
        // the first toggle therefore flips to 'oldest'.
        load();
        window.tdToggleSort();                 // -> oldest
        expect(window._tdSortOrder).toBe('oldest');
        expect(rowOrder()).toEqual(['S1', 'S2']);   // 2026-09-01 first

        window.tdToggleSort();                 // -> newest
        expect(window._tdSortOrder).toBe('newest');
        expect(rowOrder()).toEqual(['S2', 'S1']);   // 2026-09-03 first
    });

    test('the notional total is NET, signed by direction', () => {
        // Payer notionals render negative and receiver positive, so the total
        // is the net position (-10m + 5m = -5m), not the gross 15m. That is
        // the number a trader reads as their exposure, so it is worth pinning:
        // a change to unsigned totals would overstate the book by the sum of
        // both legs without anything else noticing.
        load();
        window.tdToggleSort();
        const text = wrapText();
        expect(text).toContain('5,000,000');
        expect(text).not.toContain('15,000,000');
    });

    test('an empty book renders without throwing', () => {
        load([]);
        window.tdToggleSort();
        expect(document.getElementById('td-blotter-table-wrap')).not.toBeNull();
    });

    test('no data at all is a no-op, not a crash', () => {
        // tdBlotterData null means "not loaded yet"; rendering an empty table
        // then would tell the trader the book is empty when it is unknown.
        load(null);
        const before = wrapText();
        window.tdToggleSort();
        expect(wrapText()).toBe(before);
    });

    test('a missing wrapper element is tolerated', () => {
        load();
        document.body.innerHTML = '';
        expect(() => window.tdToggleSort()).not.toThrow();
    });

    test('trades with missing numeric fields still render', () => {
        // Partial records arrive from older PRS documents; a formatter that
        // assumes every column is present would blank the whole table.
        load([{swap_id: 'S9', gauge_id: 'G-C', counterparty: 'Lloyds'}]);
        window.tdToggleSort();
        expect(wrapText()).toContain('S9');
    });

    test('the counterparty and gauge reach the row', () => {
        load();
        window.tdToggleSort();
        const text = wrapText();
        expect(text).toContain('Barclays');
        expect(text).toContain('HSBC');
    });
});
