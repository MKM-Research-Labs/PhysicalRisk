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

// validatePrsSpread — the control that stops a bad spread being priced.
//
// The input carries min="0" max="1000", but those are native form constraints
// and nothing in the panel submits a form, so they never fired. A negative
// spread priced, committed, and was written into the trade as a negative
// FixedLegRate. Bounds are read from the input's own min/max so there is one
// source of truth in the DOM.

const FRAGMENT = '../../src/static/js/gauge/gaugehc/ghc_prs_controls';

function load() {
    document.body.innerHTML =
        '<div>' +
        '  <input id="prs-spread" type="number" value="100" min="0" max="1000">' +
        '</div>' +
        '<button id="prs-commit-btn">Commit</button>';
    global.activeTab = 0;
    global.renderPRSPricing = jest.fn();
    global.currentRollDate = (d) => d;
    global.computeMaturityDate = (t, d) => d;
    global.formatMaturityDate = (d) => 'x';
    global.Theme = { value: (k) => `var(--${k})`, ramp: () => ({}) };
    jest.isolateModules(() => { require(FRAGMENT); });
}

const setSpread = (v) => {
    const el = document.getElementById('prs-spread');
    el.value = String(v);
    return el;
};
const err = () => document.getElementById('prs-spread-error');
const commit = () => document.getElementById('prs-commit-btn');

describe('validatePrsSpread', () => {
    beforeEach(load);

    test('a spread inside the range is accepted', () => {
        setSpread(150);
        expect(global.validatePrsSpread()).toBe(true);
        expect(commit().disabled).toBe(false);
        expect(err().textContent).toBe('');
    });

    test('a negative spread is rejected and disables commit', () => {
        // The defect: -50 priced and committed with no signal at all.
        setSpread(-50);
        expect(global.validatePrsSpread()).toBe(false);
        expect(commit().disabled).toBe(true);
        expect(err().textContent).toContain('0-1000');
    });

    test('a spread above the ceiling is rejected', () => {
        setSpread(5000);
        expect(global.validatePrsSpread()).toBe(false);
        expect(commit().disabled).toBe(true);
    });

    test('the bounds themselves are tradeable', () => {
        // Inclusive: a zero spread is a real trade, and the ceiling is a
        // limit rather than a forbidden value.
        setSpread(0);
        expect(global.validatePrsSpread()).toBe(true);
        setSpread(1000);
        expect(global.validatePrsSpread()).toBe(true);
    });

    test('an empty field is not treated as zero', () => {
        // parseFloat('') is NaN and `|| 0` elsewhere turned that into a free
        // trade at no spread. Blank is incomplete input, not zero.
        setSpread('');
        expect(global.validatePrsSpread()).toBe(false);
        expect(commit().disabled).toBe(true);
    });

    test('non-numeric text is rejected', () => {
        setSpread('abc');
        expect(global.validatePrsSpread()).toBe(false);
    });

    test('correcting the value re-enables commit and clears the message', () => {
        setSpread(-50);
        global.validatePrsSpread();
        expect(commit().disabled).toBe(true);

        setSpread(120);
        global.validatePrsSpread();
        expect(commit().disabled).toBe(false);
        expect(err().textContent).toBe('');
    });

    test('each call reflects the field as it now stands', () => {
        // The `input` listener that calls this on every keystroke is attached
        // by buildPRSControls, which needs a container and four sibling
        // fragments — more fixture than one assertion earns, and the e2e
        // suite types into the real field. What is asserted here is the part
        // that makes the listener worth attaching: the validator reads the
        // current value each time rather than caching a verdict.
        setSpread(-1);
        expect(global.validatePrsSpread()).toBe(false);
        setSpread(10);
        expect(global.validatePrsSpread()).toBe(true);
        setSpread(-1);
        expect(global.validatePrsSpread()).toBe(false);
    });

    test('only one error element is ever created', () => {
        setSpread(-50);
        global.validatePrsSpread();
        global.validatePrsSpread();
        global.validatePrsSpread();
        expect(document.querySelectorAll('#prs-spread-error')).toHaveLength(1);
    });

    test('a missing spread input is not an error', () => {
        document.body.innerHTML = '';
        expect(global.validatePrsSpread()).toBe(true);
    });
});
