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

// tdEodXvaCards — the XVA, XVA P&L and KVA-memo tiles on the EOD screen
// (MKM-XV-001). The rule worth pinning: an EOD that did not run XVA shows no
// tiles at all, never zeros, and the first EOD with XVA has no XVA P&L to show.

const FRAGMENT = '../../src/static/js/trading/eod/render';

const card = (label, value, color) => `[${label}|${value}|${color}]`;

function load() {
    global.fmtGBP = (n) => '£' + Number(n).toLocaleString('en-GB');
    global.Theme = { value: (k) => `var(--${k})` };
    jest.isolateModules(() => { require(FRAGMENT); });
}

describe('tdEodXvaCards', () => {
    beforeEach(load);

    test('an EOD without XVA shows no tiles', () => {
        expect(window.tdEodXvaCards({date: '2026-09-30', xva_total: null}, card)).toBe('');
        expect(window.tdEodXvaCards(null, card)).toBe('');
    });

    test('the first EOD with XVA shows a dash for XVA P&L', () => {
        const html = window.tdEodXvaCards(
            {xva_total: -8885.2, kva_total: -1200088.7, xva_pnl: null}, card);
        expect(html).toContain('[XVA|£-8,885|var(--loss)]');
        expect(html).toContain('[XVA P&L|\u2014|var(--muted)]');
        expect(html).toContain('[KVA memo|£-1,200,089|var(--text-3)]');
    });

    test('a later EOD shows its XVA P&L, coloured by sign', () => {
        const html = window.tdEodXvaCards(
            {xva_total: -8000, kva_total: -1.2e6, xva_pnl: 885.2}, card);
        expect(html).toContain('[XVA P&L|£885|var(--gain)]');
    });
});
