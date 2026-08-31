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

function renderDocsTab(m) {
    if (!m || !m.model_id) {
        return '<div style="padding:var(--space-inset);text-align:center;color:var(--muted);font-size:var(--size-sm);">' +
            'No model selected.</div>';
    }
    var docUrl = '/api/v1/governance/models/' + m.model_id + '/documentation/pdf';
    var testUrl = '/api/v1/governance/models/' + m.model_id + '/test-results/pdf';
    var analysisUrl = '/api/v1/governance/models/' + m.model_id + '/analysis/pdf';

    var html = '<div style="display:flex;flex-direction:column;height:100%;">';

    // Sub-tab bar
    html += '<div id="mg-docs-subtabs" style="display:flex;gap:0;border-bottom:2px solid var(--line);margin-bottom:var(--space-6);">';
    var sections = [
        {id: 'core-docs', label: 'Core Documentation'},
        {id: 'test-results', label: 'Test Results'},
        {id: 'analysis', label: 'Analysis'},
    ];
    sections.forEach(function(s, i) {
        var active = i === 0;
        html += '<button id="mg-docs-btn-' + s.id + '" onclick="window.MG.switchDocsSection(\'' + s.id + '\')" ';
        html += 'style="padding:var(--space-4) var(--space-8);font-size:var(--size-xs);font-weight:' + (active ? '600' : '400') + ';';
        html += 'border:none;cursor:pointer;background:transparent;';
        html += 'color:' + (active ? 'var(--accent)' : 'var(--text-3)') + ';';
        html += 'border-bottom:2px solid ' + (active ? 'var(--accent)' : 'transparent') + ';';
        html += 'margin-bottom:-2px;">' + s.label + '</button>';
    });
    html += '</div>';

    // Section containers
    // -- Core Documentation
    html += '<div id="mg-docs-sec-core-docs" style="flex:1;display:flex;flex-direction:column;">';
    html += _docsPdfSection(docUrl, 'mg-doc-pdf-container', 'Model documentation for ' + m.model_id + ' &mdash; ' + m.name);
    html += '</div>';

    // -- Test Results (hidden initially)
    html += '<div id="mg-docs-sec-test-results" style="flex:1;display:none;flex-direction:column;">';
    html += _docsPdfSection(testUrl, 'mg-test-pdf-container', 'Automated test results for model ' + m.model_id);
    html += '</div>';

    // -- Analysis (hidden initially)
    html += '<div id="mg-docs-sec-analysis" style="flex:1;display:none;flex-direction:column;">';
    html += _docsPdfSection(analysisUrl, 'mg-analysis-pdf-container', 'Model analysis for ' + m.model_id + ' &mdash; sensitivity, stress testing');
    html += '</div>';

    html += '</div>';

    // Check PDF availability for each section
    var checks = [
        {url: docUrl, containerId: 'mg-doc-pdf-container', label: 'No Documentation Available', hint: 'Model documentation PDF has not been generated for ' + m.model_id + '.'},
        {url: testUrl, containerId: 'mg-test-pdf-container', label: 'No Test Results Available', hint: 'Run: <code style="background:var(--sunken);padding:var(--space-1) var(--space-3);border-radius:var(--radius-sm);">python phys.py check tests --pdf</code>'},
        {url: analysisUrl, containerId: 'mg-analysis-pdf-container', label: 'No Analysis Available', hint: 'Run: <code style="background:var(--sunken);padding:var(--space-1) var(--space-3);border-radius:var(--radius-sm);">python -m docs.models.sensitivities.generate_all_analysis</code>'},
    ];
    checks.forEach(function(c) {
        fetch(c.url, {method: 'HEAD'}).then(function(resp) {
            if (!resp.ok) {
                var el = document.getElementById(c.containerId);
                if (el) {
                    el.innerHTML = '<div style="padding:var(--space-inset);text-align:center;">' +
                        '<div style="font-size:var(--size-32);margin-bottom:var(--space-6);">&#x26A0;</div>' +
                        '<div style="font-size:var(--size-md);font-weight:600;color:var(--text);margin-bottom:var(--space-4);">' + c.label + '</div>' +
                        '<div style="font-size:var(--size-xs);color:var(--muted);">' + c.hint + '</div></div>';
                }
            }
        });
    });

    return html;
}

function _docsPdfSection(pdfUrl, containerId, description) {
    var html = '';
    html += '<div style="display:flex;align-items:center;justify-content:space-between;padding:var(--space-4) 0;margin-bottom:var(--space-4);">';
    html += '<div style="font-size:var(--size-sm);color:var(--text-3);">' + description + '</div>';
    html += '<a href="' + pdfUrl + '" target="_blank" style="display:inline-flex;align-items:center;gap:var(--space-3);padding:var(--space-3) var(--space-7);background:var(--accent);color:var(--inverse);border-radius:var(--radius-4);text-decoration:none;font-size:var(--size-xs);font-weight:500;">&#x2913; Download PDF</a>';
    html += '</div>';
    html += '<div id="' + containerId + '" style="flex:1;min-height:500px;border:1px solid var(--line);border-radius:var(--radius-md);overflow:hidden;">';
    html += '<object data="' + pdfUrl + '" type="application/pdf" width="100%" height="500" style="border:none;">';
    html += '<div style="padding:var(--space-inset);text-align:center;">';
    html += '<div style="font-size:var(--size-32);margin-bottom:var(--space-6);">&#x1F4C4;</div>';
    html += '<div style="font-size:var(--size-md);font-weight:600;color:var(--text);margin-bottom:var(--space-4);">PDF Document</div>';
    html += '<div style="font-size:var(--size-xs);color:var(--muted);margin-bottom:var(--space-8);">Your browser cannot display the PDF inline.</div>';
    html += '<a href="' + pdfUrl + '" target="_blank" style="display:inline-block;padding:var(--space-4) var(--space-wide);background:var(--accent);color:var(--inverse);border-radius:var(--radius-4);text-decoration:none;font-size:var(--size-sm);">Open PDF</a>';
    html += '</div></object></div>';
    return html;
}

function switchDocsSection(sectionId) {
    var sectionIds = ['core-docs', 'test-results', 'analysis'];
    sectionIds.forEach(function(s) {
        var sec = document.getElementById('mg-docs-sec-' + s);
        var btn = document.getElementById('mg-docs-btn-' + s);
        if (sec) sec.style.display = s === sectionId ? 'flex' : 'none';
        if (btn) {
            btn.style.borderBottomColor = s === sectionId ? 'var(--accent)' : 'transparent';
            btn.style.color = s === sectionId ? 'var(--accent)' : 'var(--text-3)';
            btn.style.fontWeight = s === sectionId ? '600' : '400';
        }
    });
}
