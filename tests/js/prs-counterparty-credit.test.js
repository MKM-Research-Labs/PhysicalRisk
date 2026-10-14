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

// prsCounterpartyCredit — the credit line beside the PRS pricer's counterparty
// dropdown (MKM-XV-001). A rating proxy must say so: it is not a market quote.

const FRAGMENT = '../../src/static/js/gauge/gaugehc/ghc_prs_controls';

function load() { jest.isolateModules(() => { require(FRAGMENT); }); }

describe('prsCounterpartyCredit', () => {
    beforeEach(load);

    test('a market curve shows its spread, recovery and date', () => {
        expect(window.prsCounterpartyCredit({cds_5y_bps: 80.4, recovery: 0.35,
            credit_source: 'Market', credit_as_of: '2026-10-14'}))
            .toBe('CDS 5y 80bp \u00b7 R 35% \u00b7 market 2026-10-14');
    });

    test('a rating proxy is labelled as one', () => {
        const html = window.prsCounterpartyCredit({cds_5y_bps: 120, recovery: 0.4,
            credit_source: 'RatingProxy'});
        expect(html).toContain('120bp');
        expect(html).toContain('<em>rating proxy</em>');
    });

    test('no counterparty or no spread shows nothing', () => {
        expect(window.prsCounterpartyCredit(undefined)).toBe('');
        expect(window.prsCounterpartyCredit({credit_rating: 'A'})).toBe('');
    });
});
