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

function renderVersionHistoryTab(m) {
    var versions = m.version_history || [];
    if (versions.length === 0) return '<div style="padding:var(--space-wide);text-align:center;color:var(--muted);">No version history recorded</div>';

    var html = '<div style="padding:var(--space-6);">';

    // Current version banner
    html += '<div style="padding:var(--space-5) var(--space-7);background:var(--accent-soft);border-radius:var(--radius-md);border-left:3px solid var(--accent);margin-bottom:var(--space-8);">';
    html += '<span style="font-size:var(--size-xxs);color:var(--muted);text-transform:uppercase;">Current Version</span>';
    html += '<span style="font-size:var(--size-lg);font-weight:700;color:var(--accent);margin-left:var(--space-5);">v' + m.version + '</span>';
    html += '<span style="font-size:var(--size-xs);color:var(--text-3);margin-left:var(--space-5);">' + m.lifecycle_stage + '</span>';
    html += '</div>';

    // Timeline
    html += '<div style="position:relative;padding-left:var(--space-10);">';

    // Vertical line
    html += '<div style="position:absolute;left:8px;top:8px;bottom:8px;width:2px;background:var(--line);"></div>';

    versions.slice().reverse().forEach(function(v, i) {
        var isCurrent = v.version === m.version;
        var dotColor = isCurrent ? 'var(--accent)' : 'var(--grey)';
        var dotSize = isCurrent ? '12px' : '8px';

        html += '<div style="position:relative;padding:var(--space-5) 0 var(--space-8) var(--space-8);">';

        // Timeline dot
        html += '<div style="position:absolute;left:-' + (isCurrent ? '18px' : '16px') + ';top:14px;width:' + dotSize + ';height:' + dotSize + ';border-radius:50%;background:' + dotColor + ';border:2px solid white;box-shadow:0 0 0 1px ' + dotColor + ';"></div>';

        // Version card
        html += '<div style="padding:var(--space-6) var(--space-8);border:1px solid ' + (isCurrent ? 'var(--accent-border)' : 'var(--line)') + ';border-radius:var(--radius-md);background:' + (isCurrent ? 'var(--rv-wash-4)' : 'white') + ';">';

        // Header row
        html += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:var(--space-3);">';
        html += '<div>';
        html += '<span style="font-size:var(--size-14);font-weight:700;color:' + (isCurrent ? 'var(--accent)' : 'var(--text)') + ';">v' + v.version + '</span>';
        if (isCurrent) html += ' ' + badge('Current', 'var(--accent)');
        html += '</div>';
        html += '<span style="font-size:var(--size-xs);color:var(--muted);">' + v.date + '</span>';
        html += '</div>';

        // Description
        html += '<div style="font-size:var(--size-sm);color:var(--text-2);margin-bottom:var(--space-3);">' + v.description + '</div>';

        // Footer
        html += '<div style="display:flex;gap:var(--space-8);font-size:var(--size-xxs);color:var(--muted);">';
        html += '<span>Author: <b>' + v.author + '</b></span>';
        if (v.document) {
            html += '<span>Ref: <span style="color:var(--accent);">' + v.document + '</span></span>';
        }
        html += '</div>';

        html += '</div></div>';
    });

    html += '</div></div>';
    return html;
}
