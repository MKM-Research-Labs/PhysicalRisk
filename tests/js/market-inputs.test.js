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

// tdCurveInputChanged — the edit that makes a curve dirty.
//
// It is the only way tdYieldDirty and tdHazardDirtyKeys are ever set, and
// those flags decide what tdCommitMarket writes. It also does the unit
// conversion: yield inputs are percent, hazard inputs are basis points, and
// swapping the two by a factor of 100 would be invisible on screen and wrong
// in the book.
//
// tdMarketNewTrade is the market tab's route into the PRS pricer.

const INPUTS = '../../src/static/js/trading/market/actions/inputs';
const NEW_TRADE = '../../src/static/js/trading/market/actions/new_trade';

function loadInputs(state = {}) {
    global.tdYieldCurve = state.yieldCurve || {};
    global.tdYieldDirty = false;
    global.tdHazardTS = state.hazardTS || {};
    global.tdHazardDirtyKeys = {};
    global.tdMarketChart = state.chart || null;
    jest.spyOn(console, 'log').mockImplementation(() => {});
    jest.isolateModules(() => { require(INPUTS); });
}

function input(attrs, value) {
    const el = document.createElement('input');
    Object.entries(attrs).forEach(([k, v]) => el.setAttribute(k, v));
    el.value = String(value);
    return el;
}

describe('tdCurveInputChanged', () => {
    afterEach(() => jest.restoreAllMocks());

    test('a yield input is read as percent and stored as a rate', () => {
        // 4.25% on screen is 0.0425 in the curve.
        loadInputs();
        window.tdCurveInputChanged(
            input({'data-tenor': '5', 'data-mode': 'yield'}, '4.25'));

        expect(global.tdYieldCurve['5']).toBeCloseTo(0.0425, 10);
        expect(global.tdYieldDirty).toBe(true);
    });

    test('a hazard input is read as basis points, not percent', () => {
        // 150bps is 0.015 — a hundred times smaller than the yield reading of
        // the same number. Getting this wrong misprices every hazard curve.
        loadInputs();
        window.tdCurveInputChanged(input({
            'data-tenor': '3', 'data-mode': 'severe',
            'data-trigger': 'severe', 'data-gauge': 'GAUGE-1'}, '150'));

        expect(global.tdHazardTS['GAUGE-1'].severe['3']).toBeCloseTo(0.015, 10);
    });

    test('editing a hazard tenor marks exactly that gauge and trigger dirty', () => {
        loadInputs();
        window.tdCurveInputChanged(input({
            'data-tenor': '1', 'data-mode': 'warning',
            'data-trigger': 'warning', 'data-gauge': 'GAUGE-2'}, '80'));

        expect(global.tdHazardDirtyKeys).toEqual({'GAUGE-2:warning': true});
        // A hazard edit must not mark the yield curve dirty, or a commit
        // would write a yield curve nobody touched.
        expect(global.tdYieldDirty).toBe(false);
    });

    test('a new gauge and trigger are created on first edit', () => {
        loadInputs({hazardTS: {}});
        window.tdCurveInputChanged(input({
            'data-tenor': '2', 'data-mode': 'alert',
            'data-trigger': 'alert', 'data-gauge': 'GAUGE-NEW'}, '40'));

        expect(global.tdHazardTS['GAUGE-NEW'].alert['2']).toBeCloseTo(0.004, 10);
    });

    test('an existing trigger keeps its other tenors', () => {
        loadInputs({hazardTS: {'GAUGE-1': {severe: {'1': 0.01, '5': 0.05}}}});
        window.tdCurveInputChanged(input({
            'data-tenor': '1', 'data-mode': 'severe',
            'data-trigger': 'severe', 'data-gauge': 'GAUGE-1'}, '200'));

        expect(global.tdHazardTS['GAUGE-1'].severe['5']).toBe(0.05);
        expect(global.tdHazardTS['GAUGE-1'].severe['1']).toBeCloseTo(0.02, 10);
    });

    test('the chart is updated in place at the right tenor index', () => {
        // In-place so the input keeps focus; the index must match the tenor
        // or the trader sees their edit land on a different point.
        const chart = {data: {datasets: [{data: [0, 0, 0, 0, 0, 0]}]},
                       update: jest.fn()};
        loadInputs({chart});
        window.tdCurveInputChanged(
            input({'data-tenor': '3', 'data-mode': 'yield'}, '4.5'));

        expect(chart.data.datasets[0].data[2]).toBe(4.5);
    });

    test('an out-of-range tenor leaves the chart alone', () => {
        const chart = {data: {datasets: [{data: [0, 0, 0, 0, 0]}]},
                       update: jest.fn()};
        loadInputs({chart});
        window.tdCurveInputChanged(input({
            'data-tenor': '9', 'data-mode': 'severe',
            'data-trigger': 'severe', 'data-gauge': 'GAUGE-1'}, '10'));

        expect(chart.data.datasets[0].data).toEqual([0, 0, 0, 0, 0]);
    });

    test('no chart yet is not an error', () => {
        loadInputs({chart: null});
        expect(() => window.tdCurveInputChanged(
            input({'data-tenor': '1', 'data-mode': 'yield'}, '3'))).not.toThrow();
    });
});

describe('tdMarketNewTrade', () => {
    beforeEach(() => {
        global.tdSelectedGauge = null;
        window.showError = jest.fn();
        jest.isolateModules(() => { require(NEW_TRADE); });
    });
    afterEach(() => {
        delete window.TradingDesk;
        delete window.GaugeHazardCurve;
        delete window.viewHazardCurve;
    });

    test('it refuses without a selected gauge', () => {
        window.tdMarketNewTrade();
        expect(window.showError).toHaveBeenCalledWith('Select a gauge first');
    });

    test('it opens the pricer for the selected gauge', () => {
        global.tdSelectedGauge = 'GAUGE-7';
        window.TradingDesk = { hide: jest.fn() };
        window.GaugeHazardCurve = { show: jest.fn() };

        window.tdMarketNewTrade();

        expect(window.TradingDesk.hide).toHaveBeenCalled();
        expect(window.GaugeHazardCurve.show).toHaveBeenCalledWith('GAUGE-7');
    });

    test('it falls back to the legacy opener', () => {
        global.tdSelectedGauge = 'GAUGE-8';
        window.viewHazardCurve = jest.fn();
        window.tdMarketNewTrade();
        expect(window.viewHazardCurve).toHaveBeenCalledWith('GAUGE-8');
    });

    test('no pricer at all is reported rather than silent', () => {
        // A dead "New Trade" button that does nothing is worse than one that
        // says why.
        global.tdSelectedGauge = 'GAUGE-9';
        window.tdMarketNewTrade();
        expect(window.showError).toHaveBeenCalledWith('PRS pricer not available');
    });
});
