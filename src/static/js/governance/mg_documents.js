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

function renderDocuments() {
    var content = document.getElementById('mg-content');
    content.innerHTML = '<div style="padding:var(--space-inset);text-align:center;color:var(--muted);">Loading documents...</div>';

    var baseUrl = getBaseUrl();

    // Use page-load preloaded cache if available
    if (window._tdPreGovDocs) {
        var cached = window._tdPreGovDocs;
        window._tdPreGovDocs = null;
        _applyDocuments(cached);
        return;
    }

    fetch(baseUrl + '/api/v1/governance/documents', {mode: 'cors'})
        .then(function(r) { return r.json(); })
        .then(function(data) { _applyDocuments(data); })
        .catch(function(err) {
            content.innerHTML = '<div style="padding:var(--space-inset);text-align:center;color:var(--red);">Error loading documents: ' + err + '</div>';
        });
}

function _applyDocuments(data) {
    var content = document.getElementById('mg-content');
    if (!content) return;
    // The upload form must render regardless of whether the list fetch succeeded
    // — users still need the ability to add documents. Any list-load error is
    // surfaced inline below the form rather than replacing the whole panel.
    var loadError = data.status !== 'success';
    var docs = (data.documents || []);

            var html = '<div style="padding:var(--space-8);">';

            // Upload section
            html += '<div style="margin-bottom:var(--space-wide);padding:var(--space-8);border:2px dashed var(--divider);border-radius:var(--radius-lg);background:var(--raised);">';
            html += '<div style="font-weight:600;font-size:var(--size-md);color:var(--text);margin-bottom:var(--space-4);">Upload Document</div>';
            html += '<div style="display:flex;gap:var(--space-4);align-items:center;flex-wrap:wrap;">';
            html += '<input type="file" id="mg-doc-file" style="font-size:var(--size-xs);">';
            html += '<input type="text" id="mg-doc-desc" placeholder="Description (optional)" style="flex:1;padding:var(--space-3) var(--space-4);font-size:var(--size-xs);border:1px solid var(--divider);border-radius:var(--radius-4);min-width:150px;">';
            html += '<button onclick="window.MG.uploadDocument()" style="padding:var(--space-3) var(--space-8);font-size:var(--size-xs);background:var(--accent);color:var(--inverse);border:none;border-radius:var(--radius-4);cursor:pointer;font-weight:600;">Upload</button>';
            html += '</div></div>';

            // Inline error (if the list fetch failed) — shown below the upload form
            if (loadError) {
                html += '<div style="padding:var(--space-5) var(--space-6);margin-bottom:var(--space-6);border:1px solid var(--danger-line-mid);background:var(--danger-bg-soft);color:var(--red-dark);font-size:var(--size-xs);border-radius:var(--radius-4);">' +
                        'Could not load existing document list. Upload still works.' +
                        '</div>';
            }

            // Documents table
            html += '<div style="font-weight:600;font-size:var(--size-md);color:var(--text);margin-bottom:var(--space-4);">Uploaded Documents (' + docs.length + ')</div>';
            if (docs.length > 0) {
                html += '<table style="width:100%;border-collapse:collapse;font-size:var(--size-xs);">';
                html += '<thead><tr style="background:var(--blue-grey-bg);">';
                html += '<th style="padding:var(--space-4) var(--space-5);text-align:left;font-weight:600;">Name</th>';
                html += '<th style="padding:var(--space-4) var(--space-5);text-align:left;font-weight:600;">Description</th>';
                html += '<th style="padding:var(--space-4) var(--space-5);text-align:left;font-weight:600;">Date Added</th>';
                html += '<th style="padding:var(--space-4) var(--space-5);text-align:right;font-weight:600;">Size</th>';
                html += '<th style="padding:var(--space-4) var(--space-5);text-align:center;font-weight:600;">Actions</th>';
                html += '</tr></thead><tbody>';

                for (var i = 0; i < docs.length; i++) {
                    var d = docs[i];
                    var bg = i % 2 === 0 ? 'var(--panel)' : 'var(--wash)';
                    var sizeKb = d.size ? (d.size / 1024).toFixed(1) + ' KB' : '';
                    var dateStr = d.uploaded_at ? d.uploaded_at.substring(0, 10) : '';

                    html += '<tr style="background:' + bg + ';border-bottom:1px solid var(--line-soft);">';
                    html += '<td style="padding:var(--space-3) var(--space-5);">' + (d.filename || '') + '</td>';
                    html += '<td style="padding:var(--space-3) var(--space-5);color:var(--text-3);">' + (d.description || '') + '</td>';
                    html += '<td style="padding:var(--space-3) var(--space-5);">' + dateStr + '</td>';
                    html += '<td style="padding:var(--space-3) var(--space-5);text-align:right;">' + sizeKb + '</td>';
                    html += '<td style="padding:var(--space-3) var(--space-5);text-align:center;">' +
                        '<a href="#" onclick="event.preventDefault();window.MG.downloadDocument(\'' + d.id + '\')" style="color:var(--accent);margin-right:var(--space-4);">Download</a>' +
                        '<a href="#" onclick="event.preventDefault();window.MG.deleteDocument(\'' + d.id + '\')" style="color:var(--red-dark);">Delete</a>' +
                        '</td></tr>';
                }
                html += '</tbody></table>';
            } else {
                html += '<div style="padding:var(--space-8);color:var(--muted);font-size:var(--size-xs);text-align:center;">No documents uploaded yet.</div>';
            }

            html += '</div>';
            content.innerHTML = html;

    document.getElementById('mg-stats-bar').innerHTML =
        '<span>Documents: <b>' + docs.length + '</b></span>';
}

window.MG = window.MG || {};

window.MG.uploadDocument = function() {
    var fileInput = document.getElementById('mg-doc-file');
    var descInput = document.getElementById('mg-doc-desc');
    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        if (window.showError) window.showError('Please select a file');
        return;
    }

    var formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('description', descInput ? descInput.value : '');

    var baseUrl = getBaseUrl();
    fetch(baseUrl + '/api/v1/governance/documents/upload', {
        method: 'POST',
        body: formData,
        mode: 'cors'
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.status === 'success') {
            if (window.showSuccess) window.showSuccess('Document uploaded: ' + data.document.filename);
            renderDocuments();
        } else {
            if (window.showError) window.showError(data.message || 'Upload failed');
        }
    })
    .catch(function(err) {
        if (window.showError) window.showError('Upload failed: ' + err.message);
    });
};

window.MG.downloadDocument = function(docId) {
    var baseUrl = getBaseUrl();
    window.open(baseUrl + '/api/v1/governance/documents/' + docId + '/download', '_blank');
};

window.MG.deleteDocument = function(docId) {
    if (!confirm('Delete this document?')) return;
    var baseUrl = getBaseUrl();
    fetch(baseUrl + '/api/v1/governance/documents/' + docId + '/delete', {
        method: 'POST',
        mode: 'cors'
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.status === 'success') {
            if (window.showSuccess) window.showSuccess('Document deleted');
            renderDocuments();
        }
    })
    .catch(function(err) {
        if (window.showError) window.showError('Delete failed: ' + err.message);
    });
};
