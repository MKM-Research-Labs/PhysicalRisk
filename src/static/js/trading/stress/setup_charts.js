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

            function _tdSwitchStressChart(idx) {
                tdStressChartTab = idx;
                for (var i = 0; i < 3; i++) {
                    var tab = document.getElementById('td-stress-ctab-' + i);
                    if (tab) {
                        tab.style.borderBottomColor = (i === idx) ? 'var(--accent-mid)' : 'transparent';
                        tab.style.color = (i === idx) ? 'var(--accent-mid)' : 'var(--muted-2)';
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
