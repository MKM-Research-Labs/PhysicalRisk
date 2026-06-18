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

            // ---- Chart tab switching ----
            function _tdSwitchStressChart(idx) {
                tdStressChartTab = idx;
                for (var i = 0; i < 3; i++) {
                    var tab = document.getElementById('td-stress-ctab-' + i);
                    if (tab) {
                        tab.style.borderBottomColor = (i === idx) ? '#1565c0' : 'transparent';
                        tab.style.color = (i === idx) ? '#1565c0' : '#999';
                    }
                }
                _tdDrawStressChart();
            }

            function _tdDrawStressChart() {
                if (!tdStressResult) return;
                var chartWrap = document.getElementById('td-stress-chart-wrap');
                if (tdStressChartTab === 2) {
                    // Surface tab: show table, hide canvas
                    if (tdStressChart) { tdStressChart.destroy(); tdStressChart = null; }
                    if (chartWrap) chartWrap.innerHTML = '<div id="td-stress-surface-wrap" style="width:100%;height:100%;overflow:auto;"></div>';
                    _tdRenderSurfaceTable(tdStressResult);
                } else {
                    // Chart tabs: restore canvas if needed
                    if (chartWrap && !document.getElementById('td-stress-chart-canvas')) {
                        chartWrap.innerHTML = '<canvas id="td-stress-chart-canvas" style="width:100%;height:100%;"></canvas>';
                    }
                    if (tdStressChartTab === 0) {
                        _tdRenderProbabilityChart(tdStressResult);
                    } else {
                        _tdRenderStressPnlChart(tdStressResult);
                    }
                }
            }
