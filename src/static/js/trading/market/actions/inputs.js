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

            window.tdCurveInputChanged = function(input) {
                var tenor = input.getAttribute('data-tenor');
                var mode = input.getAttribute('data-mode');
                var val = parseFloat(input.value);

                if (mode === 'yield') {
                    var rate = val / 100;
                    tdYieldCurve[tenor] = rate;
                    tdYieldDirty = true;
                    console.log('[Market] Yield input changed: ' + tenor + 'Y = ' + val.toFixed(2) + '% (dirty=' + tdYieldDirty + ')');
                } else {
                    var rate = val / 10000;
                    var trigger = input.getAttribute('data-trigger');
                    var gaugeId = input.getAttribute('data-gauge');
                    if (!tdHazardTS[gaugeId]) tdHazardTS[gaugeId] = {};
                    if (!tdHazardTS[gaugeId][trigger]) tdHazardTS[gaugeId][trigger] = {};
                    tdHazardTS[gaugeId][trigger][tenor] = rate;
                    var dirtyKey = gaugeId + ':' + trigger;
                    tdHazardDirtyKeys[dirtyKey] = true;
                    console.log('[Market] Hazard input changed: ' + gaugeId + ' ' + trigger + ' ' + tenor + 'Y = ' + val.toFixed(1) + 'bps (dirty=' + dirtyKey + ')');
                }

                // Update chart data in-place (no full re-render — preserves input focus)
                if (tdMarketChart && tdMarketChart.data && tdMarketChart.data.datasets[0]) {
                    var tenors = mode === 'yield' ? ['1','2','3','4','5','6'] : ['1','2','3','4','5'];
                    var idx = tenors.indexOf(tenor);
                    if (idx >= 0) {
                        tdMarketChart.data.datasets[0].data[idx] = val;
                        tdMarketChart.update('none');
                    }
                }

                // Update dirty indicator on commit button
                var commitBtn = document.getElementById('td-commit-btn');
                if (commitBtn) {
                    commitBtn.style.background = '#e65100';
                    commitBtn.textContent = 'Commit*';
                }

                // Update info bar dirty label
                var info = document.getElementById('td-market-info');
                if (info && info.innerHTML.indexOf('UNCOMMITTED') < 0) {
                    info.innerHTML += ' | <span style="color:#e65100;font-weight:600;">UNCOMMITTED</span>';
                }
            };
