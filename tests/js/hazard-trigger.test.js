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

// _hcTriggerChanged — the trigger filter on the gauge hazard-curve tab.
//
// It sets a module-local filter and re-renders. The filter decides which
// trigger's term structure the trader is looking at, so a change that failed
// to re-render would leave the previous trigger's curve on screen under the
// new label — the worst kind of wrong, because it looks right.

const FRAGMENT = '../../src/static/js/gauge/gaugehc/ghc_hazard';

const TERM_STRUCTURES = {
    alert:   [{year: 1, survival_prob: 0.97, cumulative_default_prob: 0.03}],
    warning: [{year: 1, survival_prob: 0.99, cumulative_default_prob: 0.01}],
    severe:  [{year: 1, survival_prob: 0.995, cumulative_default_prob: 0.005}],
};

function load(hazard = {term_structures: TERM_STRUCTURES}) {
    document.body.innerHTML =
        '<canvas id="hazard-chart"></canvas>' +
        '<div id="hazard-stats-bar"></div>';
    global.hazardData = hazard;
    global.currentChart = null;
    global.Theme = { value: (k) => `var(--${k})`, ramp: () => ({}) };
    global.Chart = jest.fn(function () { this.destroy = jest.fn(); });
    // jsdom canvases have no 2d context; the renderer only passes it to Chart.
    HTMLCanvasElement.prototype.getContext = jest.fn(() => ({}));
    jest.isolateModules(() => { require(FRAGMENT); });
}

describe('_hcTriggerChanged', () => {
    afterEach(() => jest.restoreAllMocks());

    test('changing the trigger re-renders the chart', () => {
        load();
        global.Chart.mockClear();
        window._hcTriggerChanged('severe');
        expect(global.Chart).toHaveBeenCalled();
    });

    test('each trigger and the all-triggers view render', () => {
        load();
        for (const t of ['alert', 'warning', 'severe', 'all']) {
            global.Chart.mockClear();
            window._hcTriggerChanged(t);
            expect(global.Chart).toHaveBeenCalled();
        }
    });

    test('an absent term structure reports it instead of drawing', () => {
        // A missing alert series is the signal that the gauge has no curve;
        // drawing an empty chart would present that as a zero-risk gauge.
        load({term_structures: {}});
        window._hcTriggerChanged('alert');
        expect(document.getElementById('hazard-stats-bar').textContent)
            .toContain('No term structure data');
    });

    test('hazard data with no term_structures key is survivable', () => {
        load({});
        expect(() => window._hcTriggerChanged('all')).not.toThrow();
    });
});
