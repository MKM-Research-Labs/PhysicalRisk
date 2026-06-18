// Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
//
// This software is licensed by MKM Research Labs for non-commercial 
// research and educational use only. Any commercial use, including 
// but not limited to use in or for products or services offered for sale, 
// internal business operations intended for commercial advantage, or
// research and development conducted for a commercial entity, is expressly
// prohibited unless separately authorized in writing by MKM Research Labs.
//
// Use, reproduction, distribution, or modification of this code is subject to the
// terms and conditions of the license agreement provided with this software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

            var activeTab = 0;

            // Basis Explorer state
            var basisActiveSubTab = 0;
            var basisSelectedStorm = null;
            var basisSubTabNames = ['Gauge', 'SHE', 'SHD', 'Asset'];

            function ensureCanvas() {
                var container = document.getElementById('phc-chart-container');
                container.style.display = '';
                container.style.flexDirection = '';
                if (!document.getElementById('phc-chart') || document.getElementById('phc-chart').tagName !== 'CANVAS') {
                    container.innerHTML = '';
                    var canvas = document.createElement('canvas');
                    canvas.id = 'phc-chart';
                    container.appendChild(canvas);
                }
            }

            function switchTab(idx) {
                activeTab = idx;
                var tabs = document.querySelectorAll('.phc-tab');
                tabs.forEach(function(t, i) {
                    t.style.color = i === idx ? '#1976D2' : '#888';
                    t.style.borderBottomColor = i === idx ? '#1976D2' : 'transparent';
                });

                var controls = document.getElementById('phc-controls');
                controls.style.display = idx === 2 ? 'block' : 'none';

                // Remove basis sub-tab bar if switching away
                var existingSubBar = document.getElementById('phc-basis-subtab-bar');
                if (idx !== 3 && existingSubBar) {
                    existingSubBar.remove();
                }

                if (!phcData) return;

                if (idx !== 0 && idx !== 2 && idx !== 3) ensureCanvas();

                if (idx === 0) renderHazardCurve();
                else if (idx === 1) renderTermStructure();
                else if (idx === 2) renderPRSPricing();
                else if (idx === 3) renderBasisExplorer();
            }

            // ==============================================================
            // Basis Explorer — nested sub-tab management
            // ==============================================================
            function renderBasisExplorer() {
                // Create sub-tab bar if not present
                var subBar = document.getElementById('phc-basis-subtab-bar');
                if (!subBar) {
                    subBar = document.createElement('div');
                    subBar.id = 'phc-basis-subtab-bar';
                    subBar.style.cssText =
                        'display:flex;gap:0;border-bottom:1px solid #e0e0e0;padding:0 16px;' +
                        'background:#f0f4f8;';

                    basisSubTabNames.forEach(function(name, i) {
                        var btn = document.createElement('button');
                        btn.className = 'phc-basis-subtab';
                        btn.dataset.subtab = i;
                        btn.textContent = name;
                        btn.style.cssText =
                            'padding:6px 14px;border:none;background:none;cursor:pointer;' +
                            'font-size:11px;font-weight:600;color:#888;border-bottom:2px solid transparent;' +
                            'margin-bottom:-1px;transition:all 0.2s;';
                        btn.onclick = function() {
                            basisActiveSubTab = i;
                            renderBasisSubTab(i);
                        };
                        subBar.appendChild(btn);
                    });

                    // Insert after controls area
                    var controls = document.getElementById('phc-controls');
                    controls.parentNode.insertBefore(subBar, controls.nextSibling);
                }

                renderBasisSubTab(basisActiveSubTab);
            }

            function renderBasisSubTab(idx) {
                basisActiveSubTab = idx;

                // Update sub-tab styling
                var subTabs = document.querySelectorAll('.phc-basis-subtab');
                subTabs.forEach(function(t, i) {
                    t.style.color = i === idx ? '#1565C0' : '#888';
                    t.style.borderBottomColor = i === idx ? '#1565C0' : 'transparent';
                });

                // Destroy any existing charts before rendering
                if (basisGaugeChart) { basisGaugeChart.destroy(); basisGaugeChart = null; }
                if (basisSHEChart) { basisSHEChart.destroy(); basisSHEChart = null; }
                if (basisSHDChart) { basisSHDChart.destroy(); basisSHDChart = null; }
                if (basisPropertyChart) { basisPropertyChart.destroy(); basisPropertyChart = null; }
                if (_basisWaterfallChart) { _basisWaterfallChart.destroy(); _basisWaterfallChart = null; }
                if (typeof _perilOutcomesChart !== 'undefined' && _perilOutcomesChart) { _perilOutcomesChart.destroy(); _perilOutcomesChart = null; }
                if (currentChart) { currentChart.destroy(); currentChart = null; }

                // Set container to flex-column for basis layouts
                var container = document.getElementById('phc-chart-container');
                container.style.display = 'flex';
                container.style.flexDirection = 'column';

                if (idx === 0) renderBasisGauge();
                else if (idx === 1) renderBasisSHE();
                else if (idx === 2) renderBasisSHD();
                else if (idx === 3) renderBasisProperty();
            }
