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

            function toggleGaugeVisibility(idx, visible) {
                if (!spSimChart) return;
                spSimChart.setDatasetVisibility(idx, visible);
                spSimChart.update();
                updateGaugeBtnLabel();
            }

            function toggleAllGauges(show) {
                if (!spSimChart) return;
                var dd = document.getElementById('sp-vis-gauge-dropdown');
                var cbs = dd ? dd.querySelectorAll('input[type="checkbox"]') : [];
                var nDatasets = spSimChart.data.datasets.length;
                for (var i = 0; i < nDatasets - 1; i++) {
                    spSimChart.setDatasetVisibility(i, show);
                }
                cbs.forEach(function(cb) { cb.checked = show; });
                spSimChart.update();
                updateGaugeBtnLabel();
            }

            function updateGaugeBtnLabel() {
                var dd = document.getElementById('sp-vis-gauge-dropdown');
                var btn = document.getElementById('sp-vis-gauge-btn');
                if (!dd || !btn) return;
                var cbs = dd.querySelectorAll('input[type="checkbox"]');
                var total = cbs.length;
                var checked = 0;
                cbs.forEach(function(cb) { if (cb.checked) checked++; });
                if (checked === total) btn.textContent = total + ' Gauges';
                else if (checked === 0) btn.textContent = 'No Gauges';
                else btn.textContent = checked + ' of ' + total + ' Gauges';
            }

            // Close gauge dropdown on outside click
            document.addEventListener('click', function(e) {
                var dd = document.getElementById('sp-vis-gauge-dropdown');
                var btn = document.getElementById('sp-vis-gauge-btn');
                if (!dd || !btn) return;
                if (!btn.contains(e.target) && !dd.contains(e.target)) {
                    dd.style.display = 'none';
                }
            });
