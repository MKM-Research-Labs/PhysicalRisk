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

// Escape closes the trading desk. The desk was the one panel with no key
// handler, so the e2e check that Escape closes it could only fail — and had
// been asserting nothing until it was made to mean what its name says.

const LIFECYCLE = '../../src/static/js/trading/tradingdesk/panel_lifecycle';

const CLEANUPS = [
    'tdCleanupMap', 'tdCleanupMarketCharts', 'tdCleanupEodCharts',
    'tdCleanupCurveCharts', 'tdCleanupStressCharts',
];

let onKeydown;

function loadLifecycle(panel) {
    // The fragment is spliced into the desk's IIFE, where these are locals.
    global.tdPanel = panel;
    global.addMapControl = jest.fn();
    CLEANUPS.forEach((name) => { global[name] = jest.fn(); });
    jest.spyOn(console, 'log').mockImplementation(() => {});
    // Capture the listener so it can be removed: each load registers another
    // on the shared document, and they would otherwise stack across tests.
    const add = jest.spyOn(document, 'addEventListener');
    jest.isolateModules(() => { require(LIFECYCLE); });
    onKeydown = add.mock.calls.find(([type]) => type === 'keydown')[1];
    add.mockRestore();
}

function press(key) {
    document.dispatchEvent(new KeyboardEvent('keydown', {key}));
}

function makePanel(display) {
    const panel = document.createElement('div');
    panel.id = 'trading-desk-panel';
    panel.style.display = display;
    return panel;
}

describe('Escape on the trading desk', () => {
    afterEach(() => {
        document.removeEventListener('keydown', onKeydown);
        jest.restoreAllMocks();
    });

    test('closes the desk when it is open', () => {
        const panel = makePanel('flex');
        loadLifecycle(panel);

        press('Escape');

        expect(panel.style.display).toBe('none');
        CLEANUPS.forEach((name) => expect(global[name]).toHaveBeenCalledTimes(1));
    });

    test('does nothing when the desk is already closed', () => {
        // hidePanel destroys every chart and the map; it must not run again
        // for an Escape meant for some other panel.
        const panel = makePanel('none');
        loadLifecycle(panel);

        press('Escape');

        CLEANUPS.forEach((name) => expect(global[name]).not.toHaveBeenCalled());
    });

    test('does nothing before the desk has ever been created', () => {
        loadLifecycle(null);

        expect(() => press('Escape')).not.toThrow();
        CLEANUPS.forEach((name) => expect(global[name]).not.toHaveBeenCalled());
    });

    test('leaves the desk open for any other key', () => {
        const panel = makePanel('flex');
        loadLifecycle(panel);

        press('Enter');

        expect(panel.style.display).toBe('flex');
    });
});
