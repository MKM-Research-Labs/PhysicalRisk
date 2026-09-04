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

// showMaturityPopup — the PRS maturity schedule the trader checks before
// choosing a tenor. It renders 1Y-5Y with the actual roll-adjusted maturity
// and the true year fraction, which is what makes a "5Y" trade not exactly
// five years. currentRollDate, computeMaturityDate and formatMaturityDate
// come from a sibling fragment.

const FRAGMENT = '../../src/static/js/gauge/gaugehc/ghc_prs_controls';

const DAY = 86400000;

function load() {
    // Deterministic stand-ins for the roll-date helpers: maturity is exactly
    // t years on, so the rendered year fraction is predictable.
    global.currentRollDate = (today) => new Date(today.getTime() + 30 * DAY);
    global.computeMaturityDate = (t, today) =>
        new Date(today.getTime() + t * 365.25 * DAY);
    global.formatMaturityDate = (d) => d.toISOString().slice(0, 10);
    global.Theme = { value: (k) => `var(--${k})`, ramp: () => ({}) };
    document.body.innerHTML = '';
    jest.isolateModules(() => { require(FRAGMENT); });
}

const popup = () => document.getElementById('maturity-popup');

describe('showMaturityPopup', () => {
    beforeEach(load);

    test('it renders a row for every tenor from 1Y to 5Y', () => {
        window.showMaturityPopup();
        const text = popup().textContent;
        ['1Y', '2Y', '3Y', '4Y', '5Y'].forEach((t) =>
            expect(text).toContain(t));
    });

    test('it shows the roll date it is measuring from', () => {
        window.showMaturityPopup();
        expect(popup().textContent).toContain('Roll:');
    });

    test('the actual year fraction is shown, not the nominal tenor', () => {
        // The whole point of the table: a 5Y trade matures on a roll date, so
        // the real term is not 5.00 years. Here the stubs make it exact, which
        // proves the arithmetic runs rather than printing the tenor back.
        window.showMaturityPopup();
        const text = popup().textContent;
        expect(text).toContain('1.00y');
        expect(text).toContain('5.00y');
    });

    test('calling it again closes the popup rather than stacking one', () => {
        // It is a toggle: the control that opens it is the same one the
        // trader clicks to dismiss it.
        window.showMaturityPopup();
        expect(popup()).not.toBeNull();
        window.showMaturityPopup();
        expect(popup()).toBeNull();
    });

    test('a third call reopens it', () => {
        window.showMaturityPopup();
        window.showMaturityPopup();
        window.showMaturityPopup();
        expect(popup()).not.toBeNull();
        expect(document.querySelectorAll('#maturity-popup')).toHaveLength(1);
    });

    test('the close button removes it', () => {
        window.showMaturityPopup();
        popup().querySelector('button').click();
        expect(popup()).toBeNull();
    });
});
