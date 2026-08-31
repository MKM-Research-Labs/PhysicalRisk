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

            function createPanel() {
                if (spPanel) return spPanel;

                spPanel = document.createElement('div');
                spPanel.id = 'storm-portfolio-panel';
                spPanel.style.cssText =
                    'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);' +
                    'width:' + PANEL_W + ';height:' + PANEL_H + ';' +
                    'background:var(--panel);border:1px solid var(--divider);border-radius:var(--radius-lg);' +
                    'box-shadow:var(--shadow-toast);z-index:2000;' +
                    'display:none;flex-direction:column;font-family:Arial,sans-serif;';

                // Header with tabs
                var header = document.createElement('div');
                header.style.cssText =
                    'display:flex;justify-content:space-between;align-items:center;' +
                    'padding:var(--space-5) var(--space-8);border-bottom:1px solid var(--line-soft);background:var(--wash);' +
                    'border-radius:var(--radius-lg) var(--radius-lg) 0 0;';

                var leftHeader = document.createElement('div');
                leftHeader.style.cssText = 'display:flex;align-items:center;gap:var(--space-8);';
                var title = document.createElement('span');
                title.id = 'sp-panel-title';
                title.style.cssText = 'font-weight:bold;font-size:var(--size-14);color:var(--text);';
                title.textContent = 'Portfolio Storm Impact';

                var toggleWrap = document.createElement('div');
                toggleWrap.style.cssText = 'display:flex;border:1px solid var(--line-strong);border-radius:var(--radius-4);overflow:hidden;';
                var tabBtn = document.createElement('button');
                tabBtn.id = 'sp-tab-table';
                tabBtn.textContent = 'Table';
                tabBtn.style.cssText = 'padding:var(--space-2) var(--space-6);font-size:var(--size-xs);border:none;cursor:pointer;background:var(--accent);color:var(--inverse);';
                tabBtn.onclick = function() { switchTab('table'); };
                var simBtn = document.createElement('button');
                simBtn.id = 'sp-tab-sim';
                simBtn.textContent = 'Sim';
                simBtn.style.cssText = 'padding:var(--space-2) var(--space-6);font-size:var(--size-xs);border:none;cursor:pointer;background:var(--panel);color:var(--text);';
                simBtn.onclick = function() { switchTab('sim'); };
                var visBtn = document.createElement('button');
                visBtn.id = 'sp-tab-vis';
                visBtn.textContent = 'Visual';
                visBtn.style.cssText = 'padding:var(--space-2) var(--space-6);font-size:var(--size-xs);border:none;cursor:pointer;background:var(--panel);color:var(--text);';
                visBtn.onclick = function() { switchTab('vis'); };
                var varBtn = document.createElement('button');
                varBtn.id = 'sp-tab-var';
                varBtn.textContent = 'VaR';
                varBtn.style.cssText = 'padding:var(--space-2) var(--space-6);font-size:var(--size-xs);border:none;cursor:pointer;background:var(--panel);color:var(--text);';
                varBtn.onclick = function() { switchTab('var'); };
                var ctrlBtn = document.createElement('button');
                ctrlBtn.id = 'sp-tab-control';
                ctrlBtn.textContent = 'Control';
                ctrlBtn.style.cssText = 'padding:var(--space-2) var(--space-6);font-size:var(--size-xs);border:none;cursor:pointer;background:var(--panel);color:var(--text);';
                ctrlBtn.onclick = function() { switchTab('control'); };
                toggleWrap.appendChild(tabBtn);
                toggleWrap.appendChild(simBtn);
                toggleWrap.appendChild(visBtn);
                toggleWrap.appendChild(varBtn);
                toggleWrap.appendChild(ctrlBtn);

                leftHeader.appendChild(title);
                leftHeader.appendChild(toggleWrap);

                var closeBtn = document.createElement('button');
                closeBtn.innerHTML = '&times;';
                closeBtn.style.cssText =
                    'border:none;background:none;font-size:var(--size-24);cursor:pointer;color:var(--text-3);padding:0 var(--space-4);line-height:1;';
                closeBtn.onclick = hidePanel;
                header.appendChild(leftHeader);
                header.appendChild(closeBtn);

                // Shared storm selector — two rows so the storm dropdown
                // gets the full panel width and the secondary controls
                // (sort / typhoon-only / percentile) sit on a row below.
                var selectorWrap = document.createElement('div');
                selectorWrap.id = 'sp-selector-wrap';
                selectorWrap.style.cssText = 'padding:var(--space-4) var(--space-8);border-bottom:1px solid var(--line-soft);background:var(--raised);display:flex;flex-direction:column;gap:var(--space-3);';

                // Top row: storm picker only
                var selectorRow = document.createElement('div');
                selectorRow.id = 'sp-selector-row';
                selectorRow.style.cssText = 'display:flex;align-items:center;gap:var(--space-6);';
                var selLabel = document.createElement('span');
                selLabel.textContent = 'Storm:';
                selLabel.style.cssText = 'font-size:var(--size-sm);font-weight:600;color:var(--text-2);';
                var stormSelect = document.createElement('select');
                stormSelect.id = 'sp-storm-select';
                stormSelect.style.cssText = 'flex:1;padding:var(--space-2) var(--space-4);font-size:var(--size-sm);border:1px solid var(--line-strong);border-radius:var(--radius-4);';
                stormSelect.onchange = function() { onStormChanged(this.value); };
                selectorRow.appendChild(selLabel);
                selectorRow.appendChild(stormSelect);

                // Bottom row: sort + typhoon filter + percentile control
                var controlsRow = document.createElement('div');
                controlsRow.id = 'sp-controls-row';
                controlsRow.style.cssText = 'display:flex;align-items:center;gap:var(--space-8);flex-wrap:wrap;';
                var sortLabel = document.createElement('span');
                sortLabel.textContent = 'Sort:';
                sortLabel.style.cssText = 'font-size:var(--size-sm);font-weight:600;color:var(--text-2);';
                var sortSelect = document.createElement('select');
                sortSelect.id = 'sp-sort-select';
                sortSelect.style.cssText = 'padding:var(--space-2) var(--space-4);font-size:var(--size-sm);border:1px solid var(--line-strong);border-radius:var(--radius-4);';
                sortSelect.innerHTML =
                    '<option value="damage" selected>Damage cost</option>' +
                    '<option value="flooded">Properties flooded</option>' +
                    '<option value="severity">Gauge severity</option>';
                sortSelect.onchange = function() { loadStormList(this.value); };
                var pctWrap = document.createElement('span');
                pctWrap.style.cssText = 'display:flex;align-items:center;gap:var(--space-3);';
                pctWrap.innerHTML = '__SP_PCT_HTML__';

                // Typhoon-only filter — narrows the storm dropdown to storms
                // that were paired with a typhoon event by the severity-bucket
                // linkage. Click-handler lives in sp_table.py's loadStormList.
                var typhoonWrap = document.createElement('label');
                typhoonWrap.style.cssText = 'display:flex;align-items:center;gap:var(--space-3);font-size:var(--size-sm);color:var(--text);cursor:pointer;user-select:none;';
                typhoonWrap.title = 'Show only the storms that carried a typhoon';
                var typhoonChk = document.createElement('input');
                typhoonChk.type = 'checkbox';
                typhoonChk.id = 'sp-typhoon-only';
                typhoonChk.style.cssText = 'margin:0;cursor:pointer;';
                typhoonChk.onchange = function() { _applyTyphoonFilter(); };
                var typhoonLabel = document.createElement('span');
                typhoonLabel.innerHTML = '⚡ <b>Typhoon only</b>';
                var typhoonCount = document.createElement('span');
                typhoonCount.id = 'sp-typhoon-count';
                typhoonCount.style.cssText = 'color:var(--muted);font-size:var(--size-xs);margin-left:var(--space-1);';
                typhoonWrap.appendChild(typhoonChk);
                typhoonWrap.appendChild(typhoonLabel);
                typhoonWrap.appendChild(typhoonCount);

                controlsRow.appendChild(sortLabel);
                controlsRow.appendChild(sortSelect);
                controlsRow.appendChild(typhoonWrap);
                controlsRow.appendChild(pctWrap);

                selectorWrap.appendChild(selectorRow);
                selectorWrap.appendChild(controlsRow);

                // Tab views from sub-modules
                var tableView = createTableView();
                var simView = createSimView();
                var visView = createVisView();
                var varView = createVarView();
                var controlView = createControlView();

                // Stats bar (shared)
                var statsBar = document.createElement('div');
                statsBar.id = 'sp-stats-bar';
                statsBar.style.cssText = 'padding:var(--space-4) var(--space-8);border-top:1px solid var(--line-soft);display:flex;gap:var(--space-wide);font-size:var(--size-xs);color:var(--text-3);background:var(--control);border-radius:0 0 var(--radius-lg) var(--radius-lg);';

                spPanel.appendChild(header);
                spPanel.appendChild(selectorWrap);
                spPanel.appendChild(tableView);
                spPanel.appendChild(simView);
                spPanel.appendChild(visView);
                spPanel.appendChild(varView);
                spPanel.appendChild(controlView);
                spPanel.appendChild(statsBar);
                document.body.appendChild(spPanel);
                return spPanel;
            }

            // ==============================================================
            // Tab switching
            // ==============================================================
            function switchTab(tab) {
                spActiveTab = tab;
                var tableEl = document.getElementById('sp-table-view');
                var simEl = document.getElementById('sp-sim-view');
                var visEl = document.getElementById('sp-vis-view');
                var varEl = document.getElementById('sp-var-view');
                var controlEl = document.getElementById('sp-control-view');
                var btnTable = document.getElementById('sp-tab-table');
                var btnSim = document.getElementById('sp-tab-sim');
                var btnVis = document.getElementById('sp-tab-vis');
                var btnVar = document.getElementById('sp-tab-var');
                var btnCtrl = document.getElementById('sp-tab-control');

                tableEl.style.display = 'none';
                simEl.style.display = 'none';
                visEl.style.display = 'none';
                varEl.style.display = 'none';
                if (controlEl) controlEl.style.display = 'none';

                [btnTable, btnSim, btnVis, btnVar, btnCtrl].forEach(function(b) {
                    if (b) { b.style.background = Theme.value('panel'); b.style.color = Theme.value('text'); }
                });

                if (tab !== 'sim' && spSimPlaying) {
                    spStopAnim();
                }

                if (tab === 'table') {
                    tableEl.style.display = 'flex';
                    btnTable.style.background = Theme.value('accent');
                    btnTable.style.color = Theme.value('panel');
                } else if (tab === 'sim') {
                    simEl.style.display = 'flex';
                    btnSim.style.background = Theme.value('accent');
                    btnSim.style.color = Theme.value('panel');
                    var ss = document.getElementById('sp-storm-select');
                    var sid = ss ? ss.value : '';
                    if (sid) {
                        setTimeout(function() {
                            initSimMap();
                            loadSimMapData(sid);
                        }, 50);
                    }
                } else if (tab === 'vis') {
                    visEl.style.display = 'flex';
                    btnVis.style.background = Theme.value('accent');
                    btnVis.style.color = Theme.value('panel');
                    var ss2 = document.getElementById('sp-storm-select');
                    var sid2 = ss2 ? ss2.value : '';
                    if (sid2 && (!spSimData || spSimData.storm_id !== sid2)) {
                        loadSimData(sid2);
                    }
                } else if (tab === 'var') {
                    varEl.style.display = 'flex';
                    btnVar.style.background = Theme.value('accent');
                    btnVar.style.color = Theme.value('panel');
                    if (!spVarData) loadVarData();
                } else if (tab === 'control') {
                    if (controlEl) controlEl.style.display = 'flex';
                    btnCtrl.style.background = Theme.value('accent');
                    btnCtrl.style.color = Theme.value('panel');
                    loadControlData();
                }
            }

            // ==============================================================
            // Storm change handler (shared across all tabs)
            // ==============================================================
            function onStormChanged(stormId) {
                if (!stormId) return;
                spSimData = null;
                spSimMapData = null;
                loadPortfolioImpact(stormId);
                if (spActiveTab === 'sim') {
                    spStopAnim();
                    setTimeout(function() {
                        initSimMap();
                        loadSimMapData(stormId);
                    }, 50);
                } else if (spActiveTab === 'vis') {
                    loadSimData(stormId);
                }
            }

            // ==============================================================
            // Show / hide
            // ==============================================================
            function showPanel() {
                console.log('[StormPortfolio] Opening panel');
                createPanel();
                spPanel.style.display = 'flex';
                spActiveTab = 'table';
                switchTab('table');
                loadStormList();
            }

            function hidePanel() {
                if (spPanel) spPanel.style.display = 'none';
                console.log('[StormPortfolio] Panel closed');
                spStopAnim();
                if (spSimMap) {
                    spSimMap.remove();
                    spSimMap = null;
                }
                spSimMapData = null;
                if (spVarChart) {
                    spVarChart.destroy();
                    spVarChart = null;
                }
                if (spSimChart) {
                    spSimChart.destroy();
                    spSimChart = null;
                }
                spVarData = null;
                spSimData = null;
            }

            // Global entry point
            window.showStormPortfolio = showPanel;
