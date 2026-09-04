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

// tdSubmitEod writes the official end-of-day record; tdDownloadEodPdf
// retrieves it. Neither was tested. The submit path in particular is the
// point at which a day's P&L becomes the book's history, so a silent failure
// there is not recoverable by looking at the screen.

const FRAGMENT = '../../src/static/js/trading/eod/actions';

const flush = async () => { for (let i = 0; i < 12; i++) await Promise.resolve(); };

function load() {
    global.getBaseUrl = () => 'http://localhost:5013';
    global.loadEodData = jest.fn();
    global.tdEodChart = null;
    jest.isolateModules(() => { require(FRAGMENT); });
}

const ok = (body) => ({ json: () => Promise.resolve(body) });

describe('tdSubmitEod', () => {
    let adminFetch;

    beforeEach(() => {
        document.body.innerHTML =
            '<input id="td-eod-date" value="2026-09-04">' +
            '<span id="td-eod-status"></span>';
        adminFetch = jest.fn(() => Promise.resolve(ok({
            status: 'success', message: 'EOD stored', eod_id: 'EOD-001' })));
        window.__mkmAdminFetch = adminFetch;
        window.showSuccess = jest.fn();
        window.showError = jest.fn();
        load();
    });

    afterEach(() => { delete window.PropertyPDFPanel; });

    test('the date from the picker is what gets submitted', async () => {
        window.tdSubmitEod();
        await flush();

        const [url, opts] = adminFetch.mock.calls[0];
        expect(url).toBe('http://localhost:5013/api/v1/trading/eod');
        expect(opts.method).toBe('POST');
        expect(JSON.parse(opts.body)).toEqual({date: '2026-09-04'});
    });

    test('a missing date input submits an empty date rather than throwing', async () => {
        // The server decides whether a blank date is acceptable; the UI must
        // not fall over before it gets there.
        document.body.innerHTML = '';
        load();
        window.tdSubmitEod();
        await flush();
        expect(JSON.parse(adminFetch.mock.calls[0][1].body)).toEqual({date: ''});
    });

    test('progress is shown while the request is in flight', () => {
        window.tdSubmitEod();
        expect(document.getElementById('td-eod-status').textContent)
            .toBe('Submitting…');
    });

    test('a stored snapshot reports its id and reloads the history', async () => {
        window.tdSubmitEod();
        await flush();

        expect(window.showSuccess).toHaveBeenCalledWith('EOD stored');
        expect(document.getElementById('td-eod-status').textContent)
            .toBe('EOD submitted: EOD-001');
        expect(global.loadEodData).toHaveBeenCalled();
    });

    test('a refused submit says why and does not reload', async () => {
        // Reloading on failure would replace the visible error with a stale
        // history and make it look as though the snapshot had been taken.
        adminFetch.mockResolvedValue(ok({
            status: 'error', message: 'book not flat' }));
        window.tdSubmitEod();
        await flush();

        expect(window.showError).toHaveBeenCalledWith('book not flat');
        expect(document.getElementById('td-eod-status').textContent)
            .toBe('Failed: book not flat');
        expect(global.loadEodData).not.toHaveBeenCalled();
    });

    test('a refusal with no message still reports something', async () => {
        adminFetch.mockResolvedValue(ok({status: 'error'}));
        window.tdSubmitEod();
        await flush();
        expect(window.showError).toHaveBeenCalledWith('EOD submit failed');
        expect(document.getElementById('td-eod-status').textContent)
            .toContain('Unknown error');
    });

    test('a network failure is reported in the status line too', async () => {
        adminFetch.mockRejectedValue(new Error('offline'));
        window.tdSubmitEod();
        await flush();

        expect(window.showError).toHaveBeenCalledWith(
            expect.stringContaining('offline'));
        expect(document.getElementById('td-eod-status').textContent)
            .toBe('Error: offline');
    });

    test('the returned PDF is shown inline when a panel exists', async () => {
        window.PropertyPDFPanel = { show: jest.fn() };
        adminFetch.mockResolvedValue(ok({
            status: 'success', message: 'ok', eod_id: 'EOD-002',
            pdf_base64: 'JVBERi0=' }));

        window.tdSubmitEod();
        await flush();

        expect(window.PropertyPDFPanel.show)
            .toHaveBeenCalledWith('EOD-2026-09-04', 'JVBERi0=');
    });

    test('no PDF panel is not an error', async () => {
        adminFetch.mockResolvedValue(ok({
            status: 'success', message: 'ok', eod_id: 'EOD-003',
            pdf_base64: 'JVBERi0=' }));
        window.tdSubmitEod();
        await flush();
        expect(window.showError).not.toHaveBeenCalled();
    });
});

describe('tdDownloadEodPdf', () => {
    beforeEach(() => {
        window.showError = jest.fn();
        jest.spyOn(console, 'error').mockImplementation(() => {});
        load();
    });
    afterEach(() => jest.restoreAllMocks());

    test('it requests the pdf for the given date', () => {
        global.fetch = jest.fn(() => new Promise(() => {}));
        window.tdDownloadEodPdf('2026-09-04');
        expect(global.fetch).toHaveBeenCalledWith(
            'http://localhost:5013/api/v1/trading/eod/2026-09-04/pdf',
            {mode: 'cors'});
    });

    test('a missing snapshot names the date it could not find', async () => {
        global.fetch = jest.fn(() => Promise.resolve({ok: false, status: 404}));
        window.tdDownloadEodPdf('2026-01-01');
        await flush();
        expect(window.showError).toHaveBeenCalledWith(
            expect.stringContaining('2026-01-01'));
    });
});
