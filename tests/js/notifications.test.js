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

const { createNotificationSystem } = require('../../src/static/js/notifications');

describe('NotificationSystem', () => {
    let notif;

    beforeEach(() => {
        document.body.innerHTML = '';
        jest.useFakeTimers();
        notif = createNotificationSystem({
            position: 'top-right',
            timeout: 5000,
            maxVisible: 5
        });
    });

    afterEach(() => {
        jest.useRealTimers();
    });

    test('show() creates DOM element with correct structure', () => {
        const id = notif.show('Test message', 'info');
        const el = document.getElementById('notif-' + id);
        expect(el).not.toBeNull();
        expect(el.querySelector('span')).not.toBeNull();
        expect(el.querySelector('div > div')).not.toBeNull();
        expect(el.innerHTML).toContain('Test message');
    });

    test('show() uses correct template for info type', () => {
        const id = notif.show('Info msg', 'info');
        const el = document.getElementById('notif-' + id);
        expect(el.className).toContain('notif');
        expect(el.style.borderLeftColor).toBe('#2196F3');
    });

    test('show() uses correct template for success type', () => {
        const id = notif.show('Success msg', 'success');
        const el = document.getElementById('notif-' + id);
        expect(el.style.borderLeftColor).toBe('#4CAF50');
    });

    test('show() uses correct template for warning type', () => {
        const id = notif.show('Warn msg', 'warning');
        const el = document.getElementById('notif-' + id);
        expect(el.style.borderLeftColor).toBe('#FF9800');
    });

    test('show() uses correct template for error type', () => {
        const id = notif.show('Error msg', 'error');
        const el = document.getElementById('notif-' + id);
        expect(el.style.borderLeftColor).toBe('#f44336');
    });

    test('show() uses correct template for loading type', () => {
        const id = notif.show('Loading msg', 'loading');
        const el = document.getElementById('notif-' + id);
        expect(el.style.borderLeftColor).toBe('#9E9E9E');
    });

    test('show() defaults to info for unknown type', () => {
        const id = notif.show('Unknown', 'nonexistent');
        const el = document.getElementById('notif-' + id);
        expect(el.style.borderLeftColor).toBe('#2196F3');
    });

    test('respects maxVisible — oldest dismissed when exceeded', () => {
        const sys = createNotificationSystem({ maxVisible: 2, timeout: 0 });
        const id1 = sys.show('First', 'info', { persistent: true });
        const id2 = sys.show('Second', 'info', { persistent: true });
        const id3 = sys.show('Third', 'info', { persistent: true });

        // id1 should have been dismissed
        jest.advanceTimersByTime(400);
        const queue = sys.getQueue();
        expect(queue).not.toContain(id1);
        expect(queue).toContain(id2);
        expect(queue).toContain(id3);
    });

    test('dismiss() removes element from DOM', () => {
        const id = notif.show('To dismiss', 'info', { persistent: true });
        expect(document.getElementById('notif-' + id)).not.toBeNull();

        notif.dismiss(id);
        jest.advanceTimersByTime(400);
        expect(document.getElementById('notif-' + id)).toBeNull();
    });

    test('dismiss() removes id from queue', () => {
        const id = notif.show('Queued', 'info', { persistent: true });
        expect(notif.getQueue()).toContain(id);
        notif.dismiss(id);
        expect(notif.getQueue()).not.toContain(id);
    });

    test('update() changes message text', () => {
        const id = notif.show('Original', 'info', { persistent: true });
        notif.update(id, 'Updated message');
        const textEl = document.getElementById('notif-' + id).querySelector('div > div');
        expect(textEl.innerHTML).toContain('Updated message');
    });

    test('update() changes type styling', () => {
        const id = notif.show('Msg', 'info', { persistent: true });
        notif.update(id, 'Now error', 'error');
        const el = document.getElementById('notif-' + id);
        expect(el.style.borderLeftColor).toBe('#f44336');
    });

    test('clearAll() removes all notifications', () => {
        notif.show('One', 'info', { persistent: true });
        notif.show('Two', 'info', { persistent: true });
        notif.show('Three', 'info', { persistent: true });
        expect(notif.getQueue().length).toBe(3);

        notif.clearAll();
        jest.advanceTimersByTime(400);
        expect(notif.getQueue().length).toBe(0);
    });

    test('auto-dismiss after timeout', () => {
        const id = notif.show('Auto dismiss', 'info');
        expect(notif.getQueue()).toContain(id);

        jest.advanceTimersByTime(5100);
        expect(notif.getQueue()).not.toContain(id);
    });

    test('persistent option prevents auto-dismiss', () => {
        const id = notif.show('Persistent', 'info', { persistent: true });
        jest.advanceTimersByTime(10000);
        expect(notif.getQueue()).toContain(id);
    });

    test('container positioned correctly for top-right', () => {
        notif.show('Test', 'info');
        const container = document.getElementById('notif-container');
        expect(container.className).toBe('top-right');
    });

    test('container positioned correctly for bottom-left', () => {
        const sys = createNotificationSystem({ position: 'bottom-left' });
        sys.show('Test', 'info');
        const container = document.getElementById('notif-container');
        expect(container.className).toBe('bottom-left');
    });
});

describe('NotificationSystem browser auto-init', () => {
    test('convenience functions delegate with correct type', () => {
        document.body.innerHTML = '';

        // Set up config for browser auto-init
        global.__NOTIF_CONFIG = {
            position: 'top-right',
            timeout: 5000,
            maxVisible: 5
        };

        // Re-require to trigger auto-init
        jest.resetModules();
        require('../../src/static/js/notifications');

        expect(typeof global.showSuccess).toBe('function');
        expect(typeof global.showError).toBe('function');
        expect(typeof global.showWarning).toBe('function');
        expect(typeof global.showInfo).toBe('function');
        expect(typeof global.showLoading).toBe('function');
        expect(typeof global.showNotification).toBe('function');
        expect(typeof global.dismissNotification).toBe('function');

        // Clean up
        delete global.__NOTIF_CONFIG;
    });
});
