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

// Tests for src/static/js/theme.js — read access to the design tokens (rule R7).
//
// The behaviour worth pinning is what happens for a token the theme does NOT define.
// Theme.value returns null there rather than a fallback colour, because a caller that
// silently substitutes one paints an unthemed element in a plausible colour — which
// is precisely the failure the token check exists to catch, made invisible.

require('../../src/static/js/theme');

describe('Theme', () => {
    beforeEach(() => {
        document.documentElement.style.setProperty('--accent', '#1976d2');
        document.documentElement.style.setProperty('--space-7', '8px');
        window.Theme.reset();
    });

    afterEach(() => {
        document.documentElement.style.removeProperty('--accent');
        document.documentElement.style.removeProperty('--space-7');
        window.Theme.reset();
    });

    test('value() resolves a defined token to its literal value', () => {
        expect(window.Theme.value('accent')).toBe('#1976d2');
        expect(window.Theme.value('space-7')).toBe('8px');
    });

    test('value() returns null for an undefined token', () => {
        expect(window.Theme.value('no-such-token')).toBeNull();
    });

    test('value() never invents a fallback colour', () => {
        // A returned '#000' or '' here would put an unthemed element on screen in a
        // colour that looks deliberate. Null forces the caller to deal with it.
        const missing = window.Theme.value('accent-typo');
        expect(missing).not.toBe('');
        expect(missing).toBeNull();
    });

    test('has() distinguishes defined from undefined tokens', () => {
        expect(window.Theme.has('accent')).toBe(true);
        expect(window.Theme.has('no-such-token')).toBe(false);
    });

    test('ref() builds the CSS spelling of a token', () => {
        expect(window.Theme.ref('accent')).toBe('var(--accent)');
    });

    test('ref() does not require the token to exist', () => {
        // ref() is for building a style attribute, where the browser resolves the
        // reference; it deliberately does not consult the cascade.
        expect(window.Theme.ref('not-yet-defined')).toBe('var(--not-yet-defined)');
    });

    test('ref() returns null for an empty token name', () => {
        expect(window.Theme.ref('')).toBeNull();
    });

    test('value() memoises, so a redraw does not re-read the cascade', () => {
        const spy = jest.spyOn(window, 'getComputedStyle');
        window.Theme.value('accent');
        window.Theme.value('accent');
        window.Theme.value('accent');
        expect(spy).toHaveBeenCalledTimes(1);
        spy.mockRestore();
    });

    test('value() memoises a miss as well as a hit', () => {
        const spy = jest.spyOn(window, 'getComputedStyle');
        window.Theme.value('absent');
        window.Theme.value('absent');
        expect(spy).toHaveBeenCalledTimes(1);
        spy.mockRestore();
    });

    test('reset() drops the memo so a swapped block is picked up', () => {
        expect(window.Theme.value('accent')).toBe('#1976d2');
        document.documentElement.style.setProperty('--accent', '#c62828');
        expect(window.Theme.value('accent')).toBe('#1976d2');  // still memoised
        window.Theme.reset();
        expect(window.Theme.value('accent')).toBe('#c62828');
    });

    test('a second load does not replace a live Theme object', () => {
        // The block is injected once per document, but the console inlines many
        // scripts into one global scope; re-entry must not clear the memo.
        const first = window.Theme;
        jest.resetModules();
        require('../../src/static/js/theme');
        expect(window.Theme).toBe(first);
    });
});
