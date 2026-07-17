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

function _licenseText() {
    return [
        'Copyright © 2022-2026 MKM Research Labs. All rights reserved.',
        'This software is licensed by MKM Research Labs for non-commercial ' +
        'research and educational use only. Any commercial use — including ' +
        'use in or for products or services offered for sale, internal business ' +
        'operations intended for commercial advantage, or research and ' +
        'development conducted for a commercial entity — is expressly ' +
        'prohibited unless separately authorised in writing by MKM Research Labs.',
        'Use, reproduction, distribution, or modification of this code is ' +
        'subject to the terms and conditions of the licence agreement provided ' +
        'with this software.',
        'THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS ' +
        'OR IMPLIED. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE ' +
        'LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY ARISING FROM, OUT OF ' +
        'OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE ' +
        'SOFTWARE.'
    ];
}

function _showLicenseGate(onAccept, onCancel) {
    if (document.getElementById('license-gate-overlay')) return;

    var overlay = document.createElement('div');
    overlay.id = 'license-gate-overlay';
    overlay.style.cssText =
        'position:fixed;inset:0;background:rgba(15,23,42,0.55);z-index:10000;' +
        'display:flex;align-items:center;justify-content:center;' +
        'font-family:Arial,Helvetica,sans-serif;';

    var modal = document.createElement('div');
    modal.style.cssText =
        'background:#fff;max-width:560px;width:90%;border-radius:10px;' +
        'box-shadow:0 12px 48px rgba(0,0,0,0.32);padding:26px 30px;';

    var title = document.createElement('div');
    title.style.cssText =
        'font-size:17px;font-weight:bold;color:#1565c0;margin-bottom:6px;';
    title.textContent = 'MKM Research Labs — Physical Risk Platform';
    modal.appendChild(title);

    var sub = document.createElement('div');
    sub.style.cssText = 'font-size:12px;color:#888;margin-bottom:14px;';
    sub.textContent = 'Please review and accept the licence terms to continue.';
    modal.appendChild(sub);

    var box = document.createElement('div');
    box.style.cssText =
        'font-size:12px;line-height:1.55;color:#444;max-height:280px;' +
        'overflow:auto;border:1px solid #eee;border-radius:6px;' +
        'padding:14px 16px;background:#fafafa;';
    _licenseText().forEach(function (p, idx) {
        var el = document.createElement('p');
        el.style.cssText = 'margin:' + (idx ? '10px 0 0' : '0') + ';';
        el.textContent = p;
        box.appendChild(el);
    });
    modal.appendChild(box);

    var note = document.createElement('div');
    note.style.cssText = 'margin-top:16px;font-size:12px;color:#666;';
    note.innerHTML =
        'Selecting <b>Accept</b> agrees to these terms and begins loading the ' +
        'platform data.';
    modal.appendChild(note);

    var actions = document.createElement('div');
    actions.style.cssText =
        'margin-top:20px;display:flex;justify-content:flex-end;gap:10px;';

    var cancel = document.createElement('button');
    cancel.textContent = 'Cancel';
    cancel.style.cssText =
        'padding:8px 18px;border:1px solid #ccc;background:#fff;color:#555;' +
        'border-radius:6px;font-size:13px;cursor:pointer;';

    var accept = document.createElement('button');
    accept.textContent = 'Accept';
    accept.style.cssText =
        'padding:8px 20px;border:none;background:#1976d2;color:#fff;' +
        'border-radius:6px;font-size:13px;font-weight:bold;cursor:pointer;';

    actions.appendChild(cancel);
    actions.appendChild(accept);
    modal.appendChild(actions);

    overlay.appendChild(modal);
    document.body.appendChild(overlay);

    accept.addEventListener('click', function () {
        overlay.remove();
        if (typeof onAccept === 'function') onAccept();
    });
    cancel.addEventListener('click', function () {
        overlay.remove();
        if (typeof onCancel === 'function') onCancel();
    });
}

function _onLicenseDeclined() {
    if (document.getElementById('license-declined-note')) return;
    var note = document.createElement('div');
    note.id = 'license-declined-note';
    note.style.cssText =
        'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);' +
        'background:#fff;border:1px solid #ddd;border-radius:10px;' +
        'padding:22px 28px;font-family:Arial,Helvetica,sans-serif;' +
        'font-size:13px;color:#555;max-width:380px;text-align:center;' +
        'box-shadow:0 8px 32px rgba(0,0,0,0.2);z-index:9999;';
    note.innerHTML =
        '<div style="font-weight:bold;color:#c62828;margin-bottom:8px;">' +
        'Licence not accepted</div>' +
        'Data loading was cancelled. Reload the page to review the licence ' +
        'again and start the platform.';
    document.body.appendChild(note);
}
