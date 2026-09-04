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

// startup.js — the display-name helpers and the WP5 auth wrappers.
//
// __mkmAdminFetch is the single path every port-mutating request takes: PRS
// commit, trade close-out, market state, yield and hazard curves, EOD submit,
// classifier training. Its retry-after-401 behaviour had no test at all, so a
// change that dropped the session cookie, lost the retry, or swallowed a
// cancelled sign-in would have gone unnoticed by anything except a human
// finding themselves silently logged out mid-trade.
//
// The file assigns to window at top level and calls _startupEntry() on load,
// which fires the preloader's fetches — so fetch is mocked before require().

const FRAGMENT = '../../src/static/js/startup';

function loadStartup() {
    global.fetch = jest.fn(() => Promise.resolve({
        ok: true, status: 200, json: () => Promise.resolve({}),
    }));
    // Report the document as still loading so _startupEntry only registers a
    // DOMContentLoaded listener instead of running the preloader. The
    // preloader calls _createStartupPopup, which lives in a sibling fragment
    // the Python loader concatenates and is therefore absent here — and it is
    // not what these tests are about. This keeps the fixture to the helpers
    // under test rather than stubbing a chain of unrelated globals.
    Object.defineProperty(document, 'readyState', {
        configurable: true, get: () => 'loading',
    });
    jest.isolateModules(() => { require(FRAGMENT); });
}

describe('display name helpers', () => {
    beforeEach(loadStartup);

    test('an explicit address wins over the lookup', () => {
        window._propertyNames = { 'PROP-1': 'Lookup Road' };
        expect(window.propertyDisplayName('PROP-1', '1 Given Street'))
            .toBe('1 Given Street (PROP-1)');
    });

    test('the lookup is used when no address is passed', () => {
        window._propertyNames = { 'PROP-1': '2 Lookup Road' };
        expect(window.propertyDisplayName('PROP-1'))
            .toBe('2 Lookup Road (PROP-1)');
    });

    test('an unknown property degrades to the bare id', () => {
        window._propertyNames = {};
        expect(window.propertyDisplayName('PROP-9')).toBe('PROP-9');
    });

    test('a missing lookup table does not throw', () => {
        window._propertyNames = undefined;
        expect(window.propertyDisplayName('PROP-9')).toBe('PROP-9');
    });

    test('gauge labels follow the same rules', () => {
        window._gaugeNames = { 'GAUGE-1': 'Kingston' };
        expect(window.gaugeDisplayName('GAUGE-1')).toBe('Kingston (GAUGE-1)');
        expect(window.gaugeDisplayName('GAUGE-1', 'Teddington'))
            .toBe('Teddington (GAUGE-1)');
        window._gaugeNames = {};
        expect(window.gaugeDisplayName('GAUGE-2')).toBe('GAUGE-2');
    });
});

describe('__mkmLogin', () => {
    beforeEach(loadStartup);

    test('a cancelled username resolves false without calling the API', async () => {
        window.prompt = jest.fn(() => null);
        await expect(window.__mkmLogin()).resolves.toBe(false);
        expect(global.fetch).not.toHaveBeenCalledWith(
            '/auth/login', expect.anything());
    });

    test('a cancelled password resolves false without calling the API', async () => {
        // Distinct from the above: the username was accepted, so a naive
        // implementation could post an empty password.
        window.prompt = jest.fn()
            .mockReturnValueOnce('trader')
            .mockReturnValueOnce(null);
        await expect(window.__mkmLogin()).resolves.toBe(false);
        expect(global.fetch).not.toHaveBeenCalledWith(
            '/auth/login', expect.anything());
    });

    test('an empty password is still submitted', async () => {
        // '' is a typed answer, not a dismissal — only null cancels. The
        // server decides whether it is valid.
        window.prompt = jest.fn()
            .mockReturnValueOnce('trader')
            .mockReturnValueOnce('');
        await window.__mkmLogin();
        const [url, opts] = global.fetch.mock.calls.at(-1);
        expect(url).toBe('/auth/login');
        expect(JSON.parse(opts.body)).toEqual({username: 'trader', password: ''});
    });

    test('credentials are posted with the session cookie', async () => {
        window.prompt = jest.fn()
            .mockReturnValueOnce('trader')
            .mockReturnValueOnce('secret');
        await window.__mkmLogin();
        const [url, opts] = global.fetch.mock.calls.at(-1);
        expect(url).toBe('/auth/login');
        expect(opts.method).toBe('POST');
        expect(opts.credentials).toBe('same-origin');
        expect(opts.headers['Content-Type']).toBe('application/json');
        expect(JSON.parse(opts.body))
            .toEqual({username: 'trader', password: 'secret'});
    });

    test('the result mirrors the response status', async () => {
        window.prompt = jest.fn(() => 'x');
        global.fetch.mockResolvedValue({ok: true});
        await expect(window.__mkmLogin()).resolves.toBe(true);
        global.fetch.mockResolvedValue({ok: false});
        await expect(window.__mkmLogin()).resolves.toBe(false);
    });
});

describe('__mkmAdminFetch', () => {
    beforeEach(loadStartup);

    test('a body gets a JSON content type and the session cookie', async () => {
        global.fetch.mockResolvedValue({status: 200});
        await window.__mkmAdminFetch('/api/x', {method: 'POST', body: '{}'});
        const [, opts] = global.fetch.mock.calls.at(-1);
        expect(opts.headers['Content-Type']).toBe('application/json');
        expect(opts.credentials).toBe('same-origin');
    });

    test('an explicit content type is not overwritten', async () => {
        global.fetch.mockResolvedValue({status: 200});
        await window.__mkmAdminFetch('/api/x', {
            method: 'POST', body: 'a=1',
            headers: {'content-type': 'application/x-www-form-urlencoded'},
        });
        const [, opts] = global.fetch.mock.calls.at(-1);
        expect(opts.headers['content-type'])
            .toBe('application/x-www-form-urlencoded');
        expect(opts.headers['Content-Type']).toBeUndefined();
    });

    test('a bodiless request gets no content type', async () => {
        global.fetch.mockResolvedValue({status: 200});
        await window.__mkmAdminFetch('/api/x');
        const [, opts] = global.fetch.mock.calls.at(-1);
        expect(opts.headers['Content-Type']).toBeUndefined();
        expect(opts.credentials).toBe('same-origin');
    });

    test('a successful response is returned untouched', async () => {
        const resp = {status: 200, marker: 'original'};
        global.fetch.mockResolvedValue(resp);
        await expect(window.__mkmAdminFetch('/api/x')).resolves.toBe(resp);
    });

    test('a non-401 error is passed through, not retried', async () => {
        // Retrying a 500 would double-submit a trade.
        const resp = {status: 500};
        global.fetch.mockResolvedValue(resp);
        window.prompt = jest.fn();
        await expect(window.__mkmAdminFetch('/api/x')).resolves.toBe(resp);
        expect(window.prompt).not.toHaveBeenCalled();
    });

    test('a 401 prompts a sign-in and retries once', async () => {
        const after = {status: 200, marker: 'after-login'};
        global.fetch
            .mockResolvedValueOnce({status: 401})   // first attempt
            .mockResolvedValueOnce({ok: true})      // /auth/login
            .mockResolvedValueOnce(after);          // retry
        window.prompt = jest.fn()
            .mockReturnValueOnce('trader')
            .mockReturnValueOnce('secret');

        await expect(window.__mkmAdminFetch('/api/x', {method: 'POST'}))
            .resolves.toBe(after);
    });

    test('a dismissed sign-in rejects with cancelled', async () => {
        // Callers distinguish this from a failure: the trader chose to stop,
        // so it must not surface as a commit error.
        global.fetch.mockResolvedValueOnce({status: 401});
        window.prompt = jest.fn(() => null);

        await expect(window.__mkmAdminFetch('/api/x'))
            .rejects.toThrow('cancelled');
    });

    test('a failed sign-in rejects rather than retrying blind', async () => {
        global.fetch
            .mockResolvedValueOnce({status: 401})
            .mockResolvedValueOnce({ok: false});   // bad credentials
        window.prompt = jest.fn(() => 'x');

        await expect(window.__mkmAdminFetch('/api/x'))
            .rejects.toThrow('cancelled');
    });

    test('the retry carries the original method and body', async () => {
        global.fetch
            .mockResolvedValueOnce({status: 401})
            .mockResolvedValueOnce({ok: true})
            .mockResolvedValueOnce({status: 200});
        window.prompt = jest.fn(() => 'x');

        await window.__mkmAdminFetch('/api/commit',
                                     {method: 'POST', body: '{"n":1}'});
        const [url, opts] = global.fetch.mock.calls.at(-1);
        expect(url).toBe('/api/commit');
        expect(opts.method).toBe('POST');
        expect(opts.body).toBe('{"n":1}');
    });
});
