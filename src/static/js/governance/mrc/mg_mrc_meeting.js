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

var mrcMeetingTab = 'agenda';

function showMrcMeeting(meetingId) {
    var sc = document.getElementById('mrc-sub-content');
    sc.innerHTML = '<div style="padding:var(--space-inset);text-align:center;color:var(--muted);">Loading meeting...</div>';

    console.log('[MRC] Loading meeting:', meetingId);
    fetch(getBaseUrl() + '/api/v1/governance/mrc/meetings/' + meetingId, {mode: 'cors'})
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.status !== 'success') {
                sc.innerHTML = '<div style="padding:var(--space-inset);text-align:center;color:var(--red);">Meeting not found</div>';
                return;
            }
            console.log('[MRC] Meeting loaded:', data.meeting.title, '(' + data.meeting.status + ')');
            window._mrcMeeting = data.meeting;
            mrcMeetingTab = 'agenda';
            renderMrcMeetingDetail(data.meeting);
        })
        .catch(function(err) {
            console.error('[MRC] Meeting load error:', err);
            sc.innerHTML = '<div style="padding:var(--space-inset);text-align:center;color:var(--red);">Error: ' + err.message + '</div>';
        });
}

function renderMrcMeetingDetail(m) {
    var sc = document.getElementById('mrc-sub-content');

    var html = '<div style="padding:0;">';

    // Header
    html += '<div style="padding:var(--space-6) var(--space-8);border-bottom:1px solid var(--line-soft);">';
    html += '<div style="display:flex;align-items:center;gap:var(--space-6);margin-bottom:var(--space-4);">';
    html += '<button onclick="window.MG.switchMrcTab(\'meetings\')" style="padding:var(--space-2) var(--space-5);font-size:var(--size-xs);border:1px solid var(--accent);border-radius:var(--radius-4);cursor:pointer;background:var(--accent-soft);color:var(--accent);font-weight:500;">&larr; Back</button>';
    html += '<div style="font-size:var(--size-14);font-weight:700;color:var(--text);">' + m.title + '</div>';
    var statusColor = m.status === 'Completed' ? 'var(--green)' : m.status === 'Scheduled' ? 'var(--accent)' : 'var(--amber)';
    html += badge(m.status, statusColor);
    html += '<div style="flex:1;"></div>';
    html += '<button onclick="window.MG.downloadMeetingPdf(\'' + m.id + '\')" style="padding:var(--space-3) var(--space-6);font-size:var(--size-xs);border:1px solid var(--accent);border-radius:var(--radius-4);cursor:pointer;background:var(--accent-soft);color:var(--accent);font-weight:500;">&#x2913; Meeting Pack PDF</button>';
    html += '</div>';

    // Meeting info row
    html += '<div style="display:flex;gap:var(--space-wide);font-size:var(--size-xs);color:var(--text-3);flex-wrap:wrap;">';
    html += '<span>Date: <b>' + m.date + '</b></span>';
    html += '<span>Time: <b>' + (m.time || '\u2014') + '</b></span>';
    html += '<span>Location: <b>' + (m.location || '\u2014') + '</b></span>';
    html += '<span>Chair: <b>' + m.chair + '</b></span>';
    html += '</div>';
    html += '</div>';

    // Meeting sub-tabs
    html += '<div style="display:flex;border-bottom:1px solid var(--line-soft);background:var(--raised);">';
    var pCount = (m.participants || []).length;
    var minCount = Array.isArray(m.minutes) ? m.minutes.length : 0;
    var mTabs = [
        {id: 'agenda', label: 'Agenda (' + (m.agenda || []).length + ')'},
        {id: 'minutes', label: 'Minutes (' + minCount + ')'},
        {id: 'participants', label: 'Participants (' + pCount + ')'},
        {id: 'models', label: 'Models (' + (m.models_in_scope || []).length + ')'},
        {id: 'decisions', label: 'Decisions (' + (m.decisions || []).length + ')'},
        {id: 'actions', label: 'Actions (' + (m.actions || []).length + ')'},
        {id: 'mdocs', label: 'Documents (' + (m.documents || []).length + ')'},
    ];
    mTabs.forEach(function(t) {
        html += '<button id="mrc-mtab-' + t.id + '" onclick="window.MG.switchMeetingTab(\'' + t.id + '\')" style="padding:var(--space-4) var(--space-7);font-size:var(--size-xs);border:none;cursor:pointer;border-bottom:2px solid ' + (t.id === mrcMeetingTab ? 'var(--accent)' : 'transparent') + ';background:transparent;color:' + (t.id === mrcMeetingTab ? 'var(--accent)' : 'var(--text-3)') + ';font-weight:' + (t.id === mrcMeetingTab ? '600' : '400') + ';">' + t.label + '</button>';
    });
    html += '</div>';

    html += '<div id="mrc-meeting-content" style="padding:var(--space-8);overflow-y:auto;"></div>';
    html += '</div>';

    sc.innerHTML = html;
    renderMeetingTabContent(mrcMeetingTab, m);
}

function switchMeetingTab(tabId) {
    mrcMeetingTab = tabId;
    ['agenda', 'minutes', 'participants', 'models', 'decisions', 'actions', 'mdocs'].forEach(function(t) {
        var btn = document.getElementById('mrc-mtab-' + t);
        if (btn) {
            btn.style.borderBottomColor = t === tabId ? 'var(--accent)' : 'transparent';
            btn.style.color = t === tabId ? 'var(--accent)' : 'var(--text-3)';
            btn.style.fontWeight = t === tabId ? '600' : '400';
        }
    });
    renderMeetingTabContent(tabId, window._mrcMeeting);
}

function renderMeetingTabContent(tabId, m) {
    var mc = document.getElementById('mrc-meeting-content');
    if (tabId === 'agenda') mc.innerHTML = renderMrcAgenda(m);
    else if (tabId === 'minutes') mc.innerHTML = renderMrcMinutes(m);
    else if (tabId === 'participants') mc.innerHTML = renderMrcParticipants(m);
    else if (tabId === 'models') mc.innerHTML = renderMrcModelsInScope(m);
    else if (tabId === 'decisions') mc.innerHTML = renderMrcDecisions(m);
    else if (tabId === 'actions') mc.innerHTML = renderMrcActions(m);
    else if (tabId === 'mdocs') renderMrcDocuments(m);
}

function downloadMeetingPdf(meetingId) {
    window.open(getBaseUrl() + '/api/v1/governance/mrc/meetings/' + meetingId + '/pdf', '_blank');
}

// ================================================================
// CRUD helper — POST JSON, refresh meeting on success
// ================================================================
function mrcCrudPost(url, body, meetingId) {
    fetch(getBaseUrl() + url, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(body),
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.status === 'success') {
            window._mrcMeeting = data.meeting;
            renderMrcMeetingDetail(data.meeting);
            // Restore the current tab
            switchMeetingTab(mrcMeetingTab);
        } else {
            alert(data.message || 'Operation failed');
        }
    })
    .catch(function(err) { alert('Error: ' + err.message); });
}

// ================================================================
// Sub-module code
// ================================================================
