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

            function toggleMgExpand() {
                if (!mgPanel) return;
                mgExpanded = !mgExpanded;
                var expandBtn = document.getElementById('mg-expand-btn');
                if (mgExpanded) {
                    mgPanel.style.width = 'calc(100vw - 40px)';
                    mgPanel.style.height = 'calc(100vh - 40px)';
                    if (expandBtn) expandBtn.innerHTML = '&#x2750;';
                    if (expandBtn) expandBtn.title = 'Restore';
                } else {
                    mgPanel.style.width = MG_W;
                    mgPanel.style.height = MG_H;
                    if (expandBtn) expandBtn.innerHTML = '&#x26F6;';
                    if (expandBtn) expandBtn.title = 'Expand';
                }
            }

            // ================================================================
            // Panel creation
            // ================================================================
            function createPanel() {
                if (mgPanel) return mgPanel;

                mgPanel = document.createElement('div');
                mgPanel.id = 'mg-panel';
                mgPanel.style.cssText = 'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);width:' + MG_W + ';height:' + MG_H + ';background:var(--panel);border-radius:var(--radius-lg);box-shadow:var(--shadow-modal);z-index:2000;display:none;flex-direction:column;font-family:Arial,Helvetica,sans-serif;overflow:hidden;transition:width 0.2s,height 0.2s;';

                // Header
                var header = document.createElement('div');
                header.style.cssText = 'display:flex;align-items:center;justify-content:space-between;padding:var(--space-5) var(--space-8);border-bottom:1px solid var(--line-soft);flex-shrink:0;';

                var leftHeader = document.createElement('div');
                leftHeader.style.cssText = 'display:flex;align-items:center;gap:var(--space-6);';

                var title = document.createElement('span');
                title.id = 'mg-title';
                title.textContent = 'Regulatory Compliance';
                title.style.cssText = 'font-size:var(--size-14);font-weight:700;color:var(--text);';

                // Tab buttons
                var toggleWrap = document.createElement('div');
                toggleWrap.style.cssText = 'display:flex;border:1px solid var(--line-strong);border-radius:var(--radius-4);overflow:hidden;';

                var tabs = [
                    {id: 'inventory', label: 'Inventory'},
                    {id: 'chain', label: 'Model Chain'},
                    {id: 'bcbs239', label: 'BCBS 239'},
                    {id: 'raci', label: 'RACI'},
                    {id: 'mrc', label: 'MRC'},
                    {id: 'audit', label: 'Audit Trail'},
                    {id: 'documents', label: 'Documents'},
                    {id: 'bibliography', label: 'Bibliography'},
                    {id: 'audit-reports', label: 'Audit Reports'},
                    {id: 'lineage', label: 'Data Lineage'},
                    {id: 'field-lineage', label: 'Field Lineage'},
                ];
                tabs.forEach(function(t) {
                    var btn = document.createElement('button');
                    btn.id = 'mg-tab-' + t.id;
                    btn.textContent = t.label;
                    btn.style.cssText = 'padding:var(--space-2) var(--space-6);font-size:var(--size-xs);border:none;cursor:pointer;' +
                        (t.id === 'inventory' ? 'background:var(--accent);color:var(--inverse);' : 'background:var(--panel);color:var(--text);');
                    btn.onclick = (function(tabId) { return function() { switchMgTab(tabId); }; })(t.id);
                    toggleWrap.appendChild(btn);
                });

                leftHeader.appendChild(title);
                leftHeader.appendChild(toggleWrap);

                // Back button (hidden by default)
                var backBtn = document.createElement('button');
                backBtn.id = 'mg-back-btn';
                backBtn.textContent = '\u2190 Back to Models';
                backBtn.style.cssText = 'display:none;padding:var(--space-3) var(--space-7);font-size:var(--size-sm);font-weight:500;border:1px solid var(--accent);border-radius:var(--radius-4);cursor:pointer;background:var(--accent-soft);color:var(--accent);margin-left:var(--space-6);';
                backBtn.onclick = function() { showInventory(); };
                leftHeader.appendChild(backBtn);

                var rightHeader = document.createElement('div');
                rightHeader.style.cssText = 'display:flex;align-items:center;gap:var(--space-1);';

                var expandBtn = document.createElement('button');
                expandBtn.id = 'mg-expand-btn';
                expandBtn.innerHTML = '&#x26F6;';
                expandBtn.title = 'Expand';
                expandBtn.style.cssText = 'border:none;background:none;font-size:var(--size-18);cursor:pointer;color:var(--text-3);padding:0 var(--space-3);line-height:1;';
                expandBtn.onclick = toggleMgExpand;

                var closeBtn = document.createElement('button');
                closeBtn.innerHTML = '&times;';
                closeBtn.style.cssText = 'border:none;background:none;font-size:var(--size-24);cursor:pointer;color:var(--text-3);padding:0 var(--space-4);line-height:1;';
                closeBtn.onclick = hideMgPanel;

                rightHeader.appendChild(expandBtn);
                rightHeader.appendChild(closeBtn);

                header.appendChild(leftHeader);
                header.appendChild(rightHeader);

                // Illustrative-data banner. In PhysicalRisk (the open-source
                // platform) this governance panel is a DEMO of the model-risk
                // capability; MKM's live internal governance process lives in
                // the separate MKM-ModelRisk system. Make that explicit so
                // external reviewers don't read the inventory/MRC/RACI content
                // as real governance records.
                var demoBanner = document.createElement('div');
                demoBanner.id = 'mg-demo-banner';
                demoBanner.textContent =
                    'Demo — illustrative sample data, not live governance records';
                demoBanner.style.cssText = 'padding:var(--space-3) var(--space-8);font-size:var(--size-xs);' +
                    'font-weight:600;color:var(--warn-ink-deep);background:var(--warn-bg);' +
                    'border-bottom:1px solid var(--warn-line-soft);flex-shrink:0;text-align:center;';

                // Content area
                var content = document.createElement('div');
                content.id = 'mg-content';
                content.style.cssText = 'flex:1;overflow-y:auto;padding:0;';

                // Stats bar
                var statsBar = document.createElement('div');
                statsBar.id = 'mg-stats-bar';
                statsBar.style.cssText = 'padding:var(--space-4) var(--space-8);border-top:1px solid var(--line-soft);display:flex;gap:var(--space-wide);font-size:var(--size-xs);color:var(--text-3);background:var(--control);border-radius:0 0 var(--radius-lg) var(--radius-lg);';

                mgPanel.appendChild(header);
                mgPanel.appendChild(demoBanner);
                mgPanel.appendChild(content);
                mgPanel.appendChild(statsBar);
                document.body.appendChild(mgPanel);
                return mgPanel;
            }
