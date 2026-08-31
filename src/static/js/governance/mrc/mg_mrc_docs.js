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

function renderMrcDocuments(m) {
    var mc = document.getElementById('mrc-meeting-content');
    var docs = m.documents || [];

    var html = '<div>';

    // Upload form
    html += '<div style="margin-bottom:var(--space-8);padding:var(--space-6);border:1px dashed var(--divider);border-radius:var(--radius-md);background:var(--raised);">';
    html += '<div style="font-size:var(--size-xs);font-weight:600;color:var(--text);margin-bottom:var(--space-4);">Upload Supporting Document</div>';
    html += '<form id="mrc-upload-form" style="display:flex;gap:var(--space-4);align-items:flex-end;flex-wrap:wrap;">';
    html += '<div><label style="font-size:var(--size-xxs);color:var(--text-3);display:block;margin-bottom:var(--space-1);">File</label>';
    html += '<input type="file" id="mrc-upload-file" style="font-size:var(--size-xxs);"></div>';
    html += '<div style="flex:1;min-width:150px;"><label style="font-size:var(--size-xxs);color:var(--text-3);display:block;margin-bottom:var(--space-1);">Description</label>';
    html += '<input type="text" id="mrc-upload-desc" placeholder="Brief description" style="width:100%;font-size:var(--size-xs);padding:var(--space-2) var(--space-4);border:1px solid var(--line-strong);border-radius:var(--radius-sm);"></div>';
    html += '<button type="button" onclick="window.MG.uploadMeetingDoc(\'' + m.id + '\')" style="padding:var(--space-3) var(--space-7);font-size:var(--size-xs);border:1px solid var(--accent);border-radius:var(--radius-4);cursor:pointer;background:var(--accent);color:var(--inverse);font-weight:500;white-space:nowrap;">Upload</button>';
    html += '</form>';
    html += '<div id="mrc-upload-status" style="margin-top:var(--space-2);font-size:var(--size-xxs);"></div>';
    html += '</div>';

    // Document list
    if (docs.length === 0) {
        html += '<div style="color:var(--muted);font-size:var(--size-sm);">No documents uploaded yet.</div>';
    } else {
        html += '<table style="width:100%;border-collapse:collapse;font-size:var(--size-xs);">';
        html += '<thead><tr style="background:var(--raised);">';
        ['Filename', 'Description', 'Uploaded By', 'Date', ''].forEach(function(h) {
            html += '<th style="padding:var(--space-4) var(--space-5);text-align:left;border-bottom:2px solid var(--line-strong);font-size:var(--size-xxs);color:var(--text-2);">' + h + '</th>';
        });
        html += '</tr></thead><tbody>';

        docs.forEach(function(d) {
            var dlUrl = getBaseUrl() + '/api/v1/governance/mrc/meetings/' + m.id + '/documents/' + encodeURIComponent(d.filename);
            html += '<tr>';
            html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);font-weight:500;">' + d.filename + '</td>';
            html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);">' + (d.description || '\u2014') + '</td>';
            html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);">' + (d.uploaded_by || '\u2014') + '</td>';
            html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);white-space:nowrap;">' + (d.uploaded_at ? d.uploaded_at.substring(0, 10) : '\u2014') + '</td>';
            html += '<td style="padding:var(--space-3) var(--space-5);border-bottom:1px solid var(--code);"><a href="' + dlUrl + '" target="_blank" style="color:var(--accent);text-decoration:none;font-size:var(--size-xxs);">Download</a></td>';
            html += '</tr>';
        });

        html += '</tbody></table>';
    }
    html += '</div>';
    mc.innerHTML = html;
}

function uploadMeetingDoc(meetingId) {
    var fileInput = document.getElementById('mrc-upload-file');
    var descInput = document.getElementById('mrc-upload-desc');
    var statusEl = document.getElementById('mrc-upload-status');

    if (!fileInput.files || fileInput.files.length === 0) {
        statusEl.innerHTML = '<span style="color:var(--red);">Please select a file.</span>';
        return;
    }

    var formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('description', descInput.value);
    formData.append('user', 'David K Kelly');

    statusEl.innerHTML = '<span style="color:var(--accent);">Uploading...</span>';

    fetch(getBaseUrl() + '/api/v1/governance/mrc/meetings/' + meetingId + '/documents', {
        method: 'POST',
        body: formData,
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.status === 'success') {
            statusEl.innerHTML = '<span style="color:var(--green);">Uploaded successfully.</span>';
            showMrcMeeting(meetingId);
        } else {
            statusEl.innerHTML = '<span style="color:var(--red);">' + (data.message || 'Upload failed') + '</span>';
        }
    })
    .catch(function(err) {
        statusEl.innerHTML = '<span style="color:var(--red);">Error: ' + err.message + '</span>';
    });
}

// ── New meeting form ──
function showNewMeetingForm() {
    var sc = document.getElementById('mrc-sub-content');

    var html = '<div style="padding:var(--space-8);">';
    html += '<div style="display:flex;align-items:center;gap:var(--space-6);margin-bottom:var(--space-8);">';
    html += '<button onclick="window.MG.switchMrcTab(\'meetings\')" style="padding:var(--space-2) var(--space-5);font-size:var(--size-xs);border:1px solid var(--accent);border-radius:var(--radius-4);cursor:pointer;background:var(--accent-soft);color:var(--accent);font-weight:500;">&larr; Back</button>';
    html += '<div style="font-size:var(--size-14);font-weight:700;color:var(--text);">Create New MRC Meeting</div>';
    html += '</div>';

    var fields = [
        {id: 'title', label: 'Meeting Title', type: 'text', value: 'MRC Meeting'},
        {id: 'date', label: 'Date', type: 'date', value: new Date().toISOString().substring(0, 10)},
        {id: 'time', label: 'Time', type: 'time', value: '10:00'},
        {id: 'location', label: 'Location', type: 'text', value: 'Virtual (Teams)'},
    ];

    html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:var(--space-6);margin-bottom:var(--space-8);">';
    fields.forEach(function(f) {
        html += '<div><label style="font-size:var(--size-xxs);color:var(--text-3);display:block;margin-bottom:var(--space-1);">' + f.label + '</label>';
        html += '<input type="' + f.type + '" id="mrc-new-' + f.id + '" value="' + f.value + '" style="width:100%;font-size:var(--size-xs);padding:var(--space-3) var(--space-4);border:1px solid var(--line-strong);border-radius:var(--radius-4);box-sizing:border-box;"></div>';
    });
    html += '</div>';

    // Models in scope (checkboxes)
    html += '<div style="margin-bottom:var(--space-8);">';
    html += '<label style="font-size:var(--size-xxs);color:var(--text-3);display:block;margin-bottom:var(--space-3);">Models in Scope</label>';
    html += '<div style="display:flex;flex-wrap:wrap;gap:var(--space-3);">';
    if (mgData && mgData.models) {
        mgData.models.forEach(function(mod) {
            html += '<label style="display:flex;align-items:center;gap:var(--space-2);font-size:var(--size-xs);padding:var(--space-2) var(--space-4);border:1px solid var(--line-strong);border-radius:var(--radius-4);cursor:pointer;background:var(--raised);">';
            html += '<input type="checkbox" class="mrc-model-cb" value="' + mod.model_id + '" checked> ' + mod.model_id + ' ' + mod.short_name;
            html += '</label>';
        });
    }
    html += '</div></div>';

    // Supporting documents
    html += '<div style="margin-bottom:var(--space-8);">';
    html += '<label style="font-size:var(--size-xxs);color:var(--text-3);display:block;margin-bottom:var(--space-3);">Supporting Documents</label>';
    html += '<div id="mrc-new-docs-list" style="margin-bottom:var(--space-4);"></div>';
    html += '<div style="display:flex;gap:var(--space-4);align-items:flex-end;flex-wrap:wrap;padding:var(--space-5);border:1px dashed var(--divider);border-radius:var(--radius-md);background:var(--raised);">';
    html += '<div><label style="font-size:var(--size-xxs);color:var(--text-3);display:block;margin-bottom:var(--space-1);">File</label>';
    html += '<input type="file" id="mrc-new-doc-file" style="font-size:var(--size-xxs);"></div>';
    html += '<div style="flex:1;min-width:150px;"><label style="font-size:var(--size-xxs);color:var(--text-3);display:block;margin-bottom:var(--space-1);">Description</label>';
    html += '<input type="text" id="mrc-new-doc-desc" placeholder="Brief description" style="width:100%;font-size:var(--size-xs);padding:var(--space-2) var(--space-4);border:1px solid var(--line-strong);border-radius:var(--radius-sm);box-sizing:border-box;"></div>';
    html += '<button type="button" onclick="window.MG.addNewMeetingDoc()" style="padding:var(--space-3) var(--space-6);font-size:var(--size-xs);border:1px solid var(--accent);border-radius:var(--radius-4);cursor:pointer;background:var(--panel);color:var(--accent);font-weight:500;white-space:nowrap;">+ Add File</button>';
    html += '</div>';
    html += '</div>';

    html += '<div id="mrc-create-status" style="margin-bottom:var(--space-4);font-size:var(--size-xxs);"></div>';
    html += '<button onclick="window.MG.createMeeting()" style="padding:var(--space-4) var(--space-wide);font-size:var(--size-sm);border:none;border-radius:var(--radius-4);cursor:pointer;background:var(--accent);color:var(--inverse);font-weight:600;">Create Meeting</button>';

    html += '</div>';
    sc.innerHTML = html;
    window._mrcPendingDocs = [];
}

function addNewMeetingDoc() {
    var fileInput = document.getElementById('mrc-new-doc-file');
    var descInput = document.getElementById('mrc-new-doc-desc');
    if (!fileInput.files || fileInput.files.length === 0) return;

    var file = fileInput.files[0];
    window._mrcPendingDocs = window._mrcPendingDocs || [];
    window._mrcPendingDocs.push({file: file, description: descInput.value});

    // Update the visual list
    var listEl = document.getElementById('mrc-new-docs-list');
    var html = '';
    window._mrcPendingDocs.forEach(function(d, i) {
        html += '<div style="display:flex;align-items:center;gap:var(--space-4);padding:var(--space-2) var(--space-4);margin-bottom:var(--space-2);border:1px solid var(--line);border-radius:var(--radius-4);background:var(--panel);font-size:var(--size-xs);">';
        html += '<span style="flex:1;font-weight:500;">' + d.file.name + '</span>';
        if (d.description) html += '<span style="color:var(--muted);">' + d.description + '</span>';
        html += '<span style="color:var(--muted);font-size:var(--size-xxs);">(' + (d.file.size / 1024).toFixed(0) + ' KB)</span>';
        html += '<button onclick="window.MG.removeNewMeetingDoc(' + i + ')" style="border:none;background:none;color:var(--red);cursor:pointer;font-size:var(--size-14);padding:0 var(--space-2);" title="Remove">&times;</button>';
        html += '</div>';
    });
    listEl.innerHTML = html;

    // Reset inputs
    fileInput.value = '';
    descInput.value = '';
}

function removeNewMeetingDoc(index) {
    window._mrcPendingDocs.splice(index, 1);
    var listEl = document.getElementById('mrc-new-docs-list');
    var html = '';
    window._mrcPendingDocs.forEach(function(d, i) {
        html += '<div style="display:flex;align-items:center;gap:var(--space-4);padding:var(--space-2) var(--space-4);margin-bottom:var(--space-2);border:1px solid var(--line);border-radius:var(--radius-4);background:var(--panel);font-size:var(--size-xs);">';
        html += '<span style="flex:1;font-weight:500;">' + d.file.name + '</span>';
        if (d.description) html += '<span style="color:var(--muted);">' + d.description + '</span>';
        html += '<span style="color:var(--muted);font-size:var(--size-xxs);">(' + (d.file.size / 1024).toFixed(0) + ' KB)</span>';
        html += '<button onclick="window.MG.removeNewMeetingDoc(' + i + ')" style="border:none;background:none;color:var(--red);cursor:pointer;font-size:var(--size-14);padding:0 var(--space-2);" title="Remove">&times;</button>';
        html += '</div>';
    });
    listEl.innerHTML = html;
}

function uploadPendingDocs(meetingId) {
    var docs = window._mrcPendingDocs || [];
    if (docs.length === 0) {
        showMrcMeeting(meetingId);
        return;
    }
    var statusEl = document.getElementById('mrc-create-status');
    var uploaded = 0;
    var total = docs.length;
    statusEl.innerHTML = '<span style="color:var(--accent);">Uploading documents (' + uploaded + '/' + total + ')...</span>';

    function uploadNext() {
        if (uploaded >= total) {
            window._mrcPendingDocs = [];
            showMrcMeeting(meetingId);
            return;
        }
        var d = docs[uploaded];
        var formData = new FormData();
        formData.append('file', d.file);
        formData.append('description', d.description || '');
        formData.append('user', 'David K Kelly');

        fetch(getBaseUrl() + '/api/v1/governance/mrc/meetings/' + meetingId + '/documents', {
            method: 'POST',
            body: formData,
        })
        .then(function(r) { return r.json(); })
        .then(function() {
            uploaded++;
            if (statusEl) statusEl.innerHTML = '<span style="color:var(--accent);">Uploading documents (' + uploaded + '/' + total + ')...</span>';
            uploadNext();
        })
        .catch(function() {
            uploaded++;
            uploadNext();
        });
    }
    uploadNext();
}

function createMeeting() {
    var title = document.getElementById('mrc-new-title').value;
    var date = document.getElementById('mrc-new-date').value;
    var time = document.getElementById('mrc-new-time').value;
    var location = document.getElementById('mrc-new-location').value;
    var statusEl = document.getElementById('mrc-create-status');

    var modelCbs = document.querySelectorAll('.mrc-model-cb:checked');
    var models = [];
    modelCbs.forEach(function(cb) { models.push(cb.value); });

    if (!title || !date) {
        statusEl.innerHTML = '<span style="color:var(--red);">Title and date are required.</span>';
        return;
    }

    var hasDocs = window._mrcPendingDocs && window._mrcPendingDocs.length > 0;
    statusEl.innerHTML = '<span style="color:var(--accent);">Creating meeting...</span>';

    fetch(getBaseUrl() + '/api/v1/governance/mrc/meetings', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            title: title,
            date: date,
            time: time,
            location: location,
            status: 'Scheduled',
            models_in_scope: models,
        }),
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.status === 'success') {
            if (hasDocs) {
                uploadPendingDocs(data.meeting.id);
            } else {
                showMrcMeeting(data.meeting.id);
            }
        } else {
            statusEl.innerHTML = '<span style="color:var(--red);">' + (data.message || 'Failed') + '</span>';
        }
    })
    .catch(function(err) {
        statusEl.innerHTML = '<span style="color:var(--red);">Error: ' + err.message + '</span>';
    });
}

