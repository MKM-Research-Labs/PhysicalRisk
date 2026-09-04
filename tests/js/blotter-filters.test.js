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

// Blotter filtering and sort order. What a trader sees as "the book" is the
// filtered view, so a filter that silently drops or keeps the wrong trades
// misrepresents the position — which is why this ranks with the money paths
// rather than with presentation.
//
// tdBlotterFilters is assigned without `var` in the fragment, so it lands on
// the global object; the tests read it there to observe filter state.

const FILTERS = '../../src/static/js/trading/blotter/filters';
const TABLE = '../../src/static/js/trading/blotter/table';

const TRADES = [
    { swap_id: 'S1', gauge_id: 'G-A', counterparty: 'Barclays',
      trigger: 'severe', tenor: 5, trade_status: 'Open' },
    { swap_id: 'S2', gauge_id: 'G-B', counterparty: 'HSBC',
      trigger: 'warning', tenor: 3, trade_status: 'Closed' },
    { swap_id: 'S3', gauge_id: 'G-A', counterparty: 'HSBC',
      trigger: 'severe', tenor: 3 },
];

function load(module, blotter = TRADES) {
    global.tdBlotterData = blotter;
    global.tdBlotterFilters = {};
    global.renderBlotterPnlBar = jest.fn();
    global.renderFilterBar = jest.fn();
    global.renderBlotterTable = jest.fn();
    global.fmtGBP = (n) => '£' + Number(n).toLocaleString('en-GB');
    global.Theme = { value: (k) => `var(--${k})` };
    jest.isolateModules(() => { require(module); });
}

function filterBar() {
    document.body.innerHTML = `
        <select id="td-filter-gauge"><option value=""></option>
          <option value="G-A">G-A</option></select>
        <select id="td-filter-ctpy"><option value=""></option>
          <option value="HSBC">HSBC</option></select>
        <select id="td-filter-trigger"><option value=""></option>
          <option value="severe">severe</option></select>
        <select id="td-filter-tenor"><option value=""></option>
          <option value="3Y">3Y</option></select>
        <select id="td-filter-status"><option value=""></option>
          <option value="Live">Live</option></select>`;
}

describe('blotter filters', () => {
    beforeEach(() => { document.body.innerHTML = ''; });

    test('a chosen filter is recorded and the views re-render', () => {
        filterBar();
        load(FILTERS);
        document.getElementById('td-filter-gauge').value = 'G-A';
        document.getElementById('td-filter-ctpy').value = 'HSBC';

        window.tdFilterChanged();

        expect(global.tdBlotterFilters)
            .toEqual({ gauge_id: 'G-A', counterparty: 'HSBC' });
        expect(global.renderBlotterTable).toHaveBeenCalled();
        expect(global.renderBlotterPnlBar).toHaveBeenCalled();
    });

    test('an empty selection is not recorded as a filter', () => {
        // A blank select means "no filter", not "match the empty string" —
        // recording it would filter the book down to nothing.
        filterBar();
        load(FILTERS);
        window.tdFilterChanged();
        expect(global.tdBlotterFilters).toEqual({});
    });

    test('missing controls do not throw', () => {
        document.body.innerHTML = '';
        load(FILTERS);
        window.tdFilterChanged();
        expect(global.tdBlotterFilters).toEqual({});
    });

    test('clearing removes every filter', () => {
        filterBar();
        load(FILTERS);
        global.tdBlotterFilters = { gauge_id: 'G-A', trigger: 'severe' };
        window.tdClearFilters();
        expect(global.tdBlotterFilters).toEqual({});
        expect(global.renderBlotterTable).toHaveBeenCalled();
    });

    test('removing one filter leaves the others standing', () => {
        load(FILTERS);
        global.tdBlotterFilters = { gauge_id: 'G-A', trigger: 'severe' };
        window.tdRemoveFilter('gauge_id');
        expect(global.tdBlotterFilters).toEqual({ trigger: 'severe' });
    });

    test('a programmatic filter applies immediately when data is loaded', () => {
        load(FILTERS);
        window.tdApplyFilter({ counterparty: 'HSBC' });
        expect(global.tdBlotterFilters).toEqual({ counterparty: 'HSBC' });
        expect(global.renderBlotterTable).toHaveBeenCalled();
    });

    test('a filter arriving before the data is stashed, not lost', () => {
        // FS01 cell clicks can land before the blotter loads; dropping the
        // filter would show the trader an unfiltered book they did not ask for.
        load(FILTERS, null);
        window.tdApplyFilter({ gauge_id: 'G-A' });
        expect(window._tdPendingFilter).toEqual({ gauge_id: 'G-A' });
        expect(global.renderBlotterTable).not.toHaveBeenCalled();
    });

    test('applying nothing resets to an empty filter set', () => {
        load(FILTERS);
        global.tdBlotterFilters = { gauge_id: 'G-A' };
        window.tdApplyFilter();
        expect(global.tdBlotterFilters).toEqual({});
    });

    test('new PRS opens the filtered gauge', () => {
        load(FILTERS);
        global.tdBlotterFilters = { gauge_id: 'G-A' };
        window.TradingDesk = { hide: jest.fn() };
        window.GaugeHazardCurve = { show: jest.fn() };

        window.tdNewPRS();

        expect(window.TradingDesk.hide).toHaveBeenCalled();
        expect(window.GaugeHazardCurve.show).toHaveBeenCalledWith('G-A');
        delete window.TradingDesk;
        delete window.GaugeHazardCurve;
    });

    test('new PRS does nothing without a gauge filter', () => {
        load(FILTERS);
        window.GaugeHazardCurve = { show: jest.fn() };
        window.tdNewPRS();
        expect(window.GaugeHazardCurve.show).not.toHaveBeenCalled();
        delete window.GaugeHazardCurve;
    });

    test('new PRS falls back to the legacy opener', () => {
        load(FILTERS);
        global.tdBlotterFilters = { gauge_id: 'G-A' };
        window.viewHazardCurve = jest.fn();
        window.tdNewPRS();
        expect(window.viewHazardCurve).toHaveBeenCalledWith('G-A');
        delete window.viewHazardCurve;
    });
});

describe('blotter sort order', () => {
    test('toggling flips between newest and oldest', () => {
        // Only the order flag is asserted. table.js declares its own
        // renderBlotterTable, so that call resolves to the file-local
        // function and never reaches a global stub — asserting on the stub
        // would be checking a mock nothing calls.
        load(TABLE);
        delete window._tdSortOrder;

        window.tdToggleSort();
        expect(window._tdSortOrder).toBe('oldest');
        window.tdToggleSort();
        expect(window._tdSortOrder).toBe('newest');
    });

    test('an unset order starts from newest', () => {
        load(TABLE);
        delete window._tdSortOrder;
        window.tdToggleSort();
        expect(window._tdSortOrder).toBe('oldest');
    });
});
