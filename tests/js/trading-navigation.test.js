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

// The cross-panel navigation entry points: FS01 grid clicks and the aggregate
// map's popup links. Each one carries a filter or a gauge id from one screen
// to another, and getting that wrong shows the trader a different instrument
// from the one they clicked — which is worse than showing nothing.

const GRID = '../../src/static/js/trading/fs01/grid';
const MAP_VIEW = '../../src/static/js/trading/aggregate/map_view';

function loadGrid() {
    global.switchTab = jest.fn();
    global.Theme = { value: (k) => `var(--${k})` };
    global.fmtGBP = (n) => String(n);
    jest.spyOn(console, 'log').mockImplementation(() => {});
    jest.isolateModules(() => { require(GRID); });
}

function loadMapView() {
    global.Theme = { value: (k) => `var(--${k})` };
    global.fmtGBP = (n) => String(n);
    global.tdTradeMap = null;
    global.L = { circleMarker: jest.fn(), map: jest.fn() };
    jest.isolateModules(() => { require(MAP_VIEW); });
}

describe('FS01 grid clicks', () => {
    beforeEach(() => {
        jest.useFakeTimers();
        window.tdApplyFilter = jest.fn();
        loadGrid();
    });
    afterEach(() => { jest.useRealTimers(); jest.restoreAllMocks(); });

    test('a gauge click opens the blotter filtered to that gauge', () => {
        window.tdRiskGaugeClick('GAUGE-1', 'Kingston');
        expect(global.switchTab).toHaveBeenCalledWith('blotter');

        // The filter is applied after the tab renders, not before — applying
        // it first would be overwritten by the blotter's own load.
        expect(window.tdApplyFilter).not.toHaveBeenCalled();
        jest.advanceTimersByTime(150);
        expect(window.tdApplyFilter).toHaveBeenCalledWith(
            {gauge_id: 'GAUGE-1', gauge_name: 'Kingston'});
    });

    test('a gauge with no name filters on the id alone', () => {
        window.tdRiskGaugeClick('GAUGE-1');
        jest.advanceTimersByTime(150);
        expect(window.tdApplyFilter).toHaveBeenCalledWith({gauge_id: 'GAUGE-1'});
    });

    test('a cell click carries the tenor bucket as well', () => {
        window.tdRiskCellClick('GAUGE-2', '5Y', 'Teddington');
        jest.advanceTimersByTime(150);
        expect(window.tdApplyFilter).toHaveBeenCalledWith(
            {gauge_id: 'GAUGE-2', gauge_name: 'Teddington', tenor: '5Y'});
    });

    test('a cell click without a bucket omits the tenor', () => {
        // An empty bucket must not become tenor:'' — that would filter the
        // blotter down to nothing rather than showing every tenor.
        window.tdRiskCellClick('GAUGE-2', '', 'Teddington');
        jest.advanceTimersByTime(150);
        const filters = window.tdApplyFilter.mock.calls[0][0];
        expect(filters).not.toHaveProperty('tenor');
    });

    test('a missing tdApplyFilter is survivable', () => {
        delete window.tdApplyFilter;
        window.tdRiskCellClick('GAUGE-3', '3Y');
        expect(() => jest.advanceTimersByTime(150)).not.toThrow();
    });
});

describe('aggregate map popup links', () => {
    beforeEach(loadMapView);
    afterEach(() => {
        delete window.TradingDesk;
        delete window.GaugeHazardCurve;
        delete window.viewHazardCurve;
    });

    test('viewing a hazard curve hides the desk and opens the panel', () => {
        window.TradingDesk = { hide: jest.fn() };
        window.GaugeHazardCurve = { show: jest.fn() };

        window.tdViewHazardCurve('GAUGE-1');

        expect(window.TradingDesk.hide).toHaveBeenCalled();
        expect(window.GaugeHazardCurve.show).toHaveBeenCalledWith('GAUGE-1');
    });

    test('it falls back to the legacy opener', () => {
        window.viewHazardCurve = jest.fn();
        window.tdViewHazardCurve('GAUGE-2');
        expect(window.viewHazardCurve).toHaveBeenCalledWith('GAUGE-2');
    });

    test('no panel at all does not throw', () => {
        expect(() => window.tdViewHazardCurve('GAUGE-3')).not.toThrow();
    });

    test('a new trade opens the same pricing panel', () => {
        window.TradingDesk = { hide: jest.fn() };
        window.GaugeHazardCurve = { show: jest.fn() };

        window.tdNewTrade('GAUGE-4');

        expect(window.TradingDesk.hide).toHaveBeenCalled();
        expect(window.GaugeHazardCurve.show).toHaveBeenCalledWith('GAUGE-4');
    });

    test('new trade falls back to the legacy opener too', () => {
        window.viewHazardCurve = jest.fn();
        window.tdNewTrade('GAUGE-5');
        expect(window.viewHazardCurve).toHaveBeenCalledWith('GAUGE-5');
    });
});
