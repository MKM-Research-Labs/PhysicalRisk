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

            // ==============================================================
            // Tab switching
            // ==============================================================
            function switchTab(tab) {
                tdActiveTab = tab;

                var views = ['client', 'blotter', 'market', 'risk', 'map', 'eod', 'curves', 'stress', 'portstress', 'classifiers'];
                views.forEach(function(v) {
                    var el = document.getElementById('td-' + v + '-view');
                    var btn = document.getElementById('td-tab-' + v);
                    if (el) el.style.display = 'none';
                    if (btn) {
                        btn.style.background = '#f5f5f5';
                        btn.style.color = '#555';
                    }
                });

                var activeEl = document.getElementById('td-' + tab + '-view');
                var activeBtn = document.getElementById('td-tab-' + tab);
                if (activeEl) activeEl.style.display = 'flex';
                if (activeBtn) {
                    activeBtn.style.background = '#1976d2';
                    activeBtn.style.color = 'white';
                }

                // Load data for each tab
                if (tab === 'client') loadClientData();
                else if (tab === 'blotter') loadBlotterData();
                else if (tab === 'market') {
                    // Pass blotter gauge filter for continuity
                    var gaugeHint = tdBlotterFilters.gauge_id || null;
                    loadMarketData(gaugeHint);
                }
                else if (tab === 'risk') loadRiskData();
                else if (tab === 'map') loadMapData();
                else if (tab === 'eod') loadEodData();
                else if (tab === 'curves') tdLoadCurveGauges();
                else if (tab === 'stress') {
                    // Gauge hint: blotter filter > market selection > first blotter trade
                    // Blotter filter is the most recent explicit user selection and must win.
                    var stressHint = (tdBlotterFilters && tdBlotterFilters.gauge_id ? tdBlotterFilters.gauge_id : null) ||
                        tdSelectedGauge ||
                        (tdBlotterData && tdBlotterData.length > 0 ? tdBlotterData[0].gauge_id : null);
                    loadStressData(stressHint);
                }
                else if (tab === 'portstress') loadPortStressData();
                else if (tab === 'classifiers') loadClassifiersData();
            }
