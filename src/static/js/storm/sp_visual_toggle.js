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

            // ================================================================
            // Gauge visibility toggles
            // ================================================================
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
