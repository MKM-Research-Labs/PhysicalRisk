// Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
//
// This software is licensed by MKM Research Labs for non-commercial 
// research and educational use only. Any commercial use, including 
// but not limited to use in or for products or services offered for sale, 
// internal business operations intended for commercial advantage, or
// research and development conducted for a commercial entity, is expressly
// prohibited unless separately authorized in writing by MKM Research Labs.
//
// Use, reproduction, distribution, or modification of this code is subject to the
// terms and conditions of the license agreement provided with this software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

const { createContextMenuHandler } = require('../../src/static/js/context-menus');

describe('ContextMenuHandler', () => {
    let menuHandler;
    const propertyItems = [
        { id: 'gen_report', label: 'Generate PDF Report', action: 'generateReport' },
        { id: 'view_details', label: 'View Details', action: 'viewPropertyDetails' }
    ];
    const gaugeItems = [
        { id: 'gen_gauge', label: 'Generate Gauge Report', action: 'generateGaugeReport' },
        { id: 'view_hazard', label: 'View Hazard Curve', action: 'viewHazardCurve' }
    ];

    beforeEach(() => {
        document.body.innerHTML = '';
        jest.clearAllMocks();
        menuHandler = createContextMenuHandler({
            property: propertyItems,
            gauge: gaugeItems
        });
    });

    test('createMenu() creates DOM element with correct item count', () => {
        const menu = menuHandler.createMenu('test-menu', propertyItems);
        expect(menu).not.toBeNull();
        expect(menu.id).toBe('test-menu');
        // Each item is a div child
        expect(menu.children.length).toBe(propertyItems.length);
    });

    test('menu items have correct labels from config', () => {
        const menu = menuHandler.createMenu('prop-menu', propertyItems);
        const items = Array.from(menu.children);
        expect(items[0].innerHTML).toBe('Generate PDF Report');
        expect(items[1].innerHTML).toBe('View Details');
    });

    test('createMenu() for gauge has 2 items', () => {
        const menu = menuHandler.createMenu('gauge-menu', gaugeItems);
        expect(menu.children.length).toBe(2);
    });

    test('showMenu() positions at event coordinates', () => {
        const mockEvent = {
            preventDefault: jest.fn(),
            stopPropagation: jest.fn(),
            pageX: 150,
            pageY: 250
        };

        menuHandler.showMenu(mockEvent, 'PROP-123', 'property');

        const menu = document.getElementById('property-context-menu');
        expect(menu).not.toBeNull();
        expect(menu.style.left).toBe('150px');
        expect(menu.style.top).toBe('250px');
        expect(menu.style.display).toBe('block');
    });

    test('showMenu() sets currentId and currentType', () => {
        const mockEvent = {
            preventDefault: jest.fn(),
            stopPropagation: jest.fn(),
            pageX: 0,
            pageY: 0
        };

        menuHandler.showMenu(mockEvent, 'GAUGE-456', 'gauge');
        expect(menuHandler.getCurrentId()).toBe('GAUGE-456');
        expect(menuHandler.getCurrentType()).toBe('gauge');
    });

    test('item click calls window[action](currentId)', () => {
        global.generateReport = jest.fn();

        const mockEvent = {
            preventDefault: jest.fn(),
            stopPropagation: jest.fn(),
            pageX: 0,
            pageY: 0
        };

        menuHandler.showMenu(mockEvent, 'PROP-789', 'property');
        const menu = document.getElementById('property-context-menu');
        const firstItem = menu.children[0];
        firstItem.click();

        expect(global.generateReport).toHaveBeenCalledWith('PROP-789');
        delete global.generateReport;
    });

    test('item click hides menu', () => {
        global.generateReport = jest.fn();

        const mockEvent = {
            preventDefault: jest.fn(),
            stopPropagation: jest.fn(),
            pageX: 0,
            pageY: 0
        };

        menuHandler.showMenu(mockEvent, 'PROP-789', 'property');
        const menu = document.getElementById('property-context-menu');
        menu.children[0].click();

        expect(menu.style.display).toBe('none');
        delete global.generateReport;
    });

    test('document click hides all menus', () => {
        const mockEvent = {
            preventDefault: jest.fn(),
            stopPropagation: jest.fn(),
            pageX: 0,
            pageY: 0
        };

        menuHandler.showMenu(mockEvent, 'PROP-1', 'property');
        const menu = document.getElementById('property-context-menu');
        expect(menu.style.display).toBe('block');

        document.dispatchEvent(new Event('click'));
        expect(menu.style.display).toBe('none');
    });

    test('extractId() matches PROP-xxxxxxxx pattern', () => {
        const id = menuHandler.extractId('Some text PROP-abcd1234 more text', /(PROP-[a-f0-9]+)/);
        expect(id).toBe('PROP-abcd1234');
    });

    test('extractId() matches GAUGE-xxxxxxxx pattern', () => {
        const id = menuHandler.extractId('GAUGE-deadbeef info', /(GAUGE-[a-f0-9]+)/);
        expect(id).toBe('GAUGE-deadbeef');
    });

    test('extractId() matches Property: PROP-xxx|... format', () => {
        const id = menuHandler.extractId('Property: PROP-abc123 | London', /Property:\s*([^|<]+)/);
        expect(id).toBe('PROP-abc123');
    });

    test('extractId() returns null for no match', () => {
        const id = menuHandler.extractId('no ids here', /(PROP-[a-f0-9]+)/);
        expect(id).toBeNull();
    });

    test('extractId() returns null for null content', () => {
        const id = menuHandler.extractId(null, /(PROP-[a-f0-9]+)/);
        expect(id).toBeNull();
    });

    // -----------------------------------------------------------------------
    // extractShortName — regression for property ID false-match bug
    // -----------------------------------------------------------------------

    test('extractShortName() returns full property ID from tooltip', () => {
        // Tooltip format: "Property: PROP-xxxxxxxx | Floods: N (label)"
        const name = menuHandler.extractShortName('Property: PROP-ab12cd34 | Floods: 0 (Low)');
        expect(name).toBe('PROP-ab12cd34');
    });

    test('extractShortName() returns property ID even when hex ID ends in two letters before pipe', () => {
        // Regression: "ae" before " | " was being matched by the gauge regex
        const name = menuHandler.extractShortName('Property: PROP-1234bcae | Floods: 2 (Medium)');
        expect(name).toBe('PROP-1234bcae');
    });

    test('extractShortName() returns property ID when mortgaged flag present', () => {
        const name = menuHandler.extractShortName('Property: PROP-deadbeef | Floods: 5 (High) | Mortgaged');
        expect(name).toBe('PROP-deadbeef');
    });

    test('extractShortName() extracts gauge area name from gauge tooltip', () => {
        // Gauge tooltip typically has area name before GAUGE-xxx
        const name = menuHandler.extractShortName('Chelsea Bridge | GAUGE-abc12345 | Level: 2.1m');
        expect(name).toBe('Chelsea Bridge');
    });

    test('extractShortName() strips Thames prefix from gauge name', () => {
        const name = menuHandler.extractShortName('Thames Chelsea | GAUGE-abc12345 | Level: 2.1m');
        expect(name).toBe('Chelsea');
    });

    test('extractShortName() returns null for empty content', () => {
        expect(menuHandler.extractShortName(null)).toBeNull();
        expect(menuHandler.extractShortName('')).toBeNull();
    });

    test('extractShortName() strips HTML before matching', () => {
        const html = '<b>Property:</b> <span>PROP-aabbccdd</span> | Floods: 0 (Low)';
        const name = menuHandler.extractShortName(html);
        expect(name).toBe('PROP-aabbccdd');
    });

    // -----------------------------------------------------------------------
    // Gauge Blotter disabled state when gauge has no open trades
    // -----------------------------------------------------------------------

    const gaugeBlotterItems = [
        { id: 'gauge_blotter', label: 'Gauge Blotter', action: 'showGaugeBlotter' },
        { id: 'view_hazard', label: 'View Hazard Curve', action: 'viewHazardCurve' }
    ];

    test('gauge_blotter item is enabled when gaugesWithTrades not yet loaded (null)', () => {
        // Before fetch completes, gaugesWithTrades is null — all items enabled
        // No displayName passed so no header div; children[0] is the first menu item
        const handler = createContextMenuHandler({ gauge: gaugeBlotterItems });
        const mockEvent = { preventDefault: jest.fn(), stopPropagation: jest.fn(), pageX: 0, pageY: 0 };
        handler.showMenu(mockEvent, 'GAUGE-aabbccdd', 'gauge');
        const menu = document.getElementById('gauge-context-menu');
        const blotterItem = menu.children[0]; // no header — item 0 is gauge_blotter
        expect(blotterItem.className).not.toContain('ctx-menu-item-disabled');
        expect(blotterItem.onclick).not.toBeNull();
    });

    test('gauge_blotter item is enabled when gauge IS in active set', () => {
        const handler = createContextMenuHandler({ gauge: gaugeBlotterItems });
        handler.setActiveGauges(['GAUGE-aabbccdd', 'GAUGE-11223344']);
        const mockEvent = { preventDefault: jest.fn(), stopPropagation: jest.fn(), pageX: 0, pageY: 0 };
        handler.showMenu(mockEvent, 'GAUGE-aabbccdd', 'gauge');
        const menu = document.getElementById('gauge-context-menu');
        const blotterItem = menu.children[0];
        expect(blotterItem.className).not.toContain('ctx-menu-item-disabled');
        expect(blotterItem.onclick).not.toBeNull();
    });

    test('gauge_blotter item is disabled when gauge NOT in active set', () => {
        const handler = createContextMenuHandler({ gauge: gaugeBlotterItems });
        handler.setActiveGauges(['GAUGE-11223344']); // different gauge has trades
        const mockEvent = { preventDefault: jest.fn(), stopPropagation: jest.fn(), pageX: 0, pageY: 0 };
        handler.showMenu(mockEvent, 'GAUGE-aabbccdd', 'gauge');
        const menu = document.getElementById('gauge-context-menu');
        const blotterItem = menu.children[0];
        expect(blotterItem.className).toContain('ctx-menu-item-disabled');
        expect(blotterItem.onclick).toBeNull();
    });

    test('gauge_blotter disabled item does not call action on click', () => {
        global.showGaugeBlotter = jest.fn();
        const handler = createContextMenuHandler({ gauge: gaugeBlotterItems });
        handler.setActiveGauges([]); // no gauges have trades
        const mockEvent = { preventDefault: jest.fn(), stopPropagation: jest.fn(), pageX: 0, pageY: 0 };
        handler.showMenu(mockEvent, 'GAUGE-aabbccdd', 'gauge');
        const menu = document.getElementById('gauge-context-menu');
        const blotterItem = menu.children[0];
        blotterItem.click(); // should do nothing (no onclick)
        expect(global.showGaugeBlotter).not.toHaveBeenCalled();
        delete global.showGaugeBlotter;
    });

    test('non-blotter gauge item is never disabled even when gauge not in active set', () => {
        const handler = createContextMenuHandler({ gauge: gaugeBlotterItems });
        handler.setActiveGauges([]); // no trades anywhere
        const mockEvent = { preventDefault: jest.fn(), stopPropagation: jest.fn(), pageX: 0, pageY: 0 };
        handler.showMenu(mockEvent, 'GAUGE-aabbccdd', 'gauge');
        const menu = document.getElementById('gauge-context-menu');
        const hazardItem = menu.children[1]; // second item (view_hazard, id != 'gauge_blotter')
        expect(hazardItem.className).not.toContain('ctx-menu-item-disabled');
    });

    test('setActiveGauges() updates disabled state for subsequent showMenu calls', () => {
        const handler = createContextMenuHandler({ gauge: gaugeBlotterItems });
        const mockEvent = { preventDefault: jest.fn(), stopPropagation: jest.fn(), pageX: 0, pageY: 0 };

        // First: no trades — should be disabled
        handler.setActiveGauges([]);
        handler.showMenu(mockEvent, 'GAUGE-aabbccdd', 'gauge');
        let menu = document.getElementById('gauge-context-menu');
        expect(menu.children[0].className).toContain('ctx-menu-item-disabled');

        // Now add the gauge — should be enabled
        handler.setActiveGauges(['GAUGE-aabbccdd']);
        handler.showMenu(mockEvent, 'GAUGE-aabbccdd', 'gauge');
        menu = document.getElementById('gauge-context-menu');
        expect(menu.children[0].className).not.toContain('ctx-menu-item-disabled');
    });
});
