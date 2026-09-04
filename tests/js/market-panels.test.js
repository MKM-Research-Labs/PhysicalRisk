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

// Market tab state and the two history overlays.
//
// tdSelectGauge and tdCurveModeChanged decide which curve the market tab is
// editing — and therefore which curve a subsequent commit writes. The history
// overlays are modal, so their close paths matter: a leaked overlay sits on
// top of the desk and swallows every later click, which is how one failing
// test cascades into twenty-four (seen in the loan-pricer leak, 2026-08).

const SETUP = '../../src/static/js/trading/market/setup';
const CURVE_HISTORY = '../../src/static/js/trading/market/actions/curve_history';
const PL_HISTORY = '../../src/static/js/trading/market/actions/pl_history';

function baseGlobals() {
    // The real Theme also exposes ramp(); setup.js reads a colour ramp.
    global.Theme = {
        value: (k) => `var(--${k})`,
        ramp: () => ({}),
    };
    global.fmtGBP = (n) => String(n);
    global.renderGaugeList = jest.fn();
    global.renderCurveChart = jest.fn();
    global.tdCurveMode = 'yield';
    global.tdSelectedGauge = null;
    global.tdMarketData = {};
    global.tdHistoryCharts = [];
    global.tdHistoryTrigColors = {severe: 'red'};
    global.tdPLHistChart = null;
    global.getBaseUrl = () => 'http://localhost:5013';
}

describe('market tab selection', () => {
    // tdCurveMode and tdSelectedGauge are module-local `var`s in setup.js, so
    // the state is not observable from here. What IS observable is which
    // renderer the mode routes to — renderYieldCurve and renderHazardCurve
    // live in sibling fragments, so they can be staged as globals. Routing is
    // the behaviour that matters anyway: it decides which curve the tab is
    // editing, and therefore which curve a later commit writes.
    beforeEach(() => {
        document.body.innerHTML =
            '<div id="td-market-chart-area"></div>' +
            '<div id="td-market-inputs"></div>' +
            '<span id="td-curve-label"></span>' +
            '<div id="td-market-info"></div>' +
            '<div id="td-gauge-list"></div>';
        baseGlobals();
        global.renderYieldCurve = jest.fn();
        global.renderHazardCurve = jest.fn();
        jest.isolateModules(() => { require(SETUP); });
    });

    test('yield mode routes to the yield renderer', () => {
        window.tdCurveModeChanged('yield');
        expect(global.renderYieldCurve).toHaveBeenCalled();
        expect(global.renderHazardCurve).not.toHaveBeenCalled();
    });

    test('a hazard trigger with a gauge selected routes to the hazard renderer', () => {
        window.tdCurveModeChanged('severe');
        window.tdSelectGauge('GAUGE-1');
        expect(global.renderHazardCurve).toHaveBeenCalled();
    });

    test('a hazard trigger with no gauge prompts instead of rendering', () => {
        // Rendering a hazard curve with no gauge selected would show the
        // previous gauge's curve under the new trigger.
        window.tdCurveModeChanged('severe');
        expect(global.renderHazardCurve).not.toHaveBeenCalled();
        expect(document.getElementById('td-market-chart-area').textContent)
            .toContain('Select a gauge');
    });

    test('selecting a gauge in yield mode is a no-op', () => {
        // Yield curves are not per-gauge, so a stray click must not change
        // what the next commit targets.
        window.tdCurveModeChanged('yield');
        global.renderYieldCurve.mockClear();
        window.tdSelectGauge('GAUGE-1');
        expect(global.renderYieldCurve).not.toHaveBeenCalled();
    });

    test('a missing chart area is tolerated', () => {
        document.body.innerHTML = '';
        expect(() => window.tdCurveModeChanged('yield')).not.toThrow();
    });
});

describe('curve history overlay', () => {
    beforeEach(() => {
        document.body.innerHTML = '';
        baseGlobals();
        window.showError = jest.fn();
        global.fetch = jest.fn(() => new Promise(() => {}));
        jest.isolateModules(() => { require(CURVE_HISTORY); });
    });

    test('it refuses to open in yield mode', () => {
        global.tdCurveMode = 'yield';
        global.tdSelectedGauge = 'GAUGE-1';
        window.tdShowCurveHistory();
        expect(window.showError).toHaveBeenCalledWith(
            expect.stringContaining('Select a hazard trigger'));
        expect(document.getElementById('td-history-overlay')).toBeNull();
    });

    test('it refuses to open with no gauge selected', () => {
        global.tdCurveMode = 'severe';
        global.tdSelectedGauge = null;
        window.tdShowCurveHistory();
        expect(window.showError).toHaveBeenCalled();
        expect(document.getElementById('td-history-overlay')).toBeNull();
    });

    test('it opens for a selected gauge and names it', () => {
        global.tdCurveMode = 'severe';
        global.tdSelectedGauge = 'GAUGE-1';
        global.tdMarketData = {'GAUGE-1': {gauge_name: 'Kingston'}};

        window.tdShowCurveHistory();

        const overlay = document.getElementById('td-history-overlay');
        expect(overlay).not.toBeNull();
        expect(overlay.textContent).toContain('Kingston');
        expect(overlay.textContent).toContain('Severe');
    });

    test('an unnamed gauge falls back to its id', () => {
        global.tdCurveMode = 'severe';
        global.tdSelectedGauge = 'GAUGE-9';
        global.tdMarketData = {};
        window.tdShowCurveHistory();
        expect(document.getElementById('td-history-overlay').textContent)
            .toContain('GAUGE-9');
    });

    test('closing removes the overlay', () => {
        // tdHistoryCharts is module-local, so the chart teardown cannot be
        // observed from here; the overlay's removal is what a leaked modal
        // would show up as anyway.
        window.tdShowCurveHistory();
        window.tdCloseCurveHistory();
        expect(document.getElementById('td-history-overlay')).toBeNull();
    });

    test('closing twice is harmless', () => {
        window.tdCloseCurveHistory();
        expect(() => window.tdCloseCurveHistory()).not.toThrow();
    });

    test('closing is idempotent for a reopened overlay', () => {
        window.tdShowCurveHistory();
        window.tdCloseCurveHistory();
        window.tdShowCurveHistory();
        window.tdCloseCurveHistory();
        expect(document.getElementById('td-history-overlay')).toBeNull();
    });
});

describe('P&L history overlay', () => {
    beforeEach(() => {
        document.body.innerHTML = '';
        baseGlobals();
        global.fetch = jest.fn(() => new Promise(() => {}));
        jest.isolateModules(() => { require(PL_HISTORY); });
    });

    test('it opens an overlay', () => {
        window.tdShowPLHistory();
        expect(document.getElementById('td-plhist-overlay')).not.toBeNull();
    });

    test('clicking the backdrop closes it', () => {
        // Clicking the modal body must not close it; only the scrim.
        window.tdShowPLHistory();
        const overlay = document.getElementById('td-plhist-overlay');
        overlay.firstChild.dispatchEvent(
            new window.MouseEvent('click', {bubbles: true}));
        expect(document.getElementById('td-plhist-overlay')).not.toBeNull();

        overlay.dispatchEvent(new window.MouseEvent('click', {bubbles: true}));
        expect(document.getElementById('td-plhist-overlay')).toBeNull();
    });

    test('closing removes the overlay', () => {
        window.tdShowPLHistory();
        window.tdClosePLHistory();
        expect(document.getElementById('td-plhist-overlay')).toBeNull();
    });

    test('closing with no overlay open is harmless', () => {
        expect(() => window.tdClosePLHistory()).not.toThrow();
    });
});
