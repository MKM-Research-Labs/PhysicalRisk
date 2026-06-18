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

            // ----------------------------------------------------------------
            // Classifier training UI (on-demand)
            // ----------------------------------------------------------------
            var _stressTrainingPollTimer = null;

            function _showClassifierNotTrained(container, gaugeId) {
                var statusEl = document.getElementById('hazard-status');
                if (statusEl) statusEl.textContent = 'Classifier not trained for this gauge';
                container.innerHTML =
                    '<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;gap:16px;">' +
                        '<div style="font-size:36px;color:#e0e0e0;">&#9888;</div>' +
                        '<div style="font-size:13px;font-weight:600;color:#333;">Classifier Not Available</div>' +
                        '<div style="font-size:11px;color:#666;max-width:400px;text-align:center;">' +
                            'No trained flood classifier found for this gauge. ' +
                            'Training takes approximately 3-5 minutes and runs in the background.' +
                        '</div>' +
                        '<button id="stress-train-btn" style="padding:8px 24px;font-size:12px;font-weight:600;' +
                            'background:#1565c0;color:#fff;border:none;border-radius:4px;cursor:pointer;">Train Now</button>' +
                        '<div id="stress-train-status" style="font-size:10px;color:#999;"></div>' +
                    '</div>';
                var btn = document.getElementById('stress-train-btn');
                if (btn) btn.addEventListener('click', function() { _startClassifierTraining(gaugeId); });
            }

            function _showClassifierTraining(container, gaugeId, elapsed) {
                var statusEl = document.getElementById('hazard-status');
                if (statusEl) statusEl.textContent = 'Training classifier... (' + elapsed + 's)';
                container.innerHTML =
                    '<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;gap:16px;">' +
                        '<div class="stress-spinner" style="width:40px;height:40px;border:4px solid #e0e0e0;' +
                            'border-top:4px solid #1565c0;border-radius:50%;animation:stressSpin 1s linear infinite;"></div>' +
                        '<div style="font-size:13px;font-weight:600;color:#333;">Training Classifier</div>' +
                        '<div id="stress-train-elapsed" style="font-size:11px;color:#666;">' +
                            'Training in progress... (' + elapsed + 's elapsed)' +
                        '</div>' +
                        '<div style="font-size:10px;color:#999;">You can switch tabs and come back — training continues in the background.</div>' +
                    '</div>' +
                    '<style>@keyframes stressSpin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }</style>';
                _pollClassifierStatus(gaugeId);
            }

            function _showClassifierFailed(container, gaugeId, error) {
                var statusEl = document.getElementById('hazard-status');
                if (statusEl) statusEl.textContent = 'Classifier training failed';
                container.innerHTML =
                    '<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;gap:16px;">' +
                        '<div style="font-size:36px;color:#c00;">&#10060;</div>' +
                        '<div style="font-size:13px;font-weight:600;color:#c00;">Training Failed</div>' +
                        '<div style="font-size:11px;color:#666;max-width:400px;text-align:center;">' + error + '</div>' +
                        '<button id="stress-retry-btn" style="padding:8px 24px;font-size:12px;font-weight:600;' +
                            'background:#1565c0;color:#fff;border:none;border-radius:4px;cursor:pointer;">Retry</button>' +
                    '</div>';
                var btn = document.getElementById('stress-retry-btn');
                if (btn) btn.addEventListener('click', function() { _startClassifierTraining(gaugeId); });
            }

            function _startClassifierTraining(gaugeId) {
                var cfg = window.__BACKEND_CONFIG || {};
                var baseUrl = cfg.url || '';
                var statusDiv = document.getElementById('stress-train-status');
                if (statusDiv) statusDiv.textContent = 'Starting training...';

                var btn = document.getElementById('stress-train-btn');
                if (btn) { btn.disabled = true; btn.style.opacity = '0.6'; }

                window.__mkmAdminFetch(baseUrl + '/api/v1/trading/stress/train/' + gaugeId, {
                    method: 'POST',
                    mode: 'cors'
                })
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    if (data.status === 'ready') {
                        _renderStressUI(gaugeId);
                    } else if (data.status === 'training') {
                        var container = document.getElementById('hazard-chart-container');
                        if (container) _showClassifierTraining(container, gaugeId, 0);
                    } else {
                        if (statusDiv) statusDiv.textContent = 'Error: ' + (data.message || 'Failed');
                        if (btn) { btn.disabled = false; btn.style.opacity = '1'; }
                    }
                })
                .catch(function(err) {
                    console.error('[Stress] Train request error:', err);
                    if (statusDiv) statusDiv.textContent = 'Network error';
                    if (btn) { btn.disabled = false; btn.style.opacity = '1'; }
                });
            }

            function _pollClassifierStatus(gaugeId) {
                if (_stressTrainingPollTimer) clearInterval(_stressTrainingPollTimer);
                var cfg = window.__BACKEND_CONFIG || {};
                var baseUrl = cfg.url || '';

                _stressTrainingPollTimer = setInterval(function() {
                    fetch(baseUrl + '/api/v1/trading/stress/classifier-status/' + gaugeId, {mode: 'cors'})
                        .then(function(r) { return r.json(); })
                        .then(function(data) {
                            if (data.status === 'ready') {
                                clearInterval(_stressTrainingPollTimer);
                                _stressTrainingPollTimer = null;
                                _renderStressUI(gaugeId);
                            } else if (data.status === 'training') {
                                var el = document.getElementById('stress-train-elapsed');
                                if (el) el.textContent = 'Training in progress... (' + (data.elapsed_seconds || 0) + 's elapsed)';
                            } else if (data.status === 'failed') {
                                clearInterval(_stressTrainingPollTimer);
                                _stressTrainingPollTimer = null;
                                var container = document.getElementById('hazard-chart-container');
                                if (container) _showClassifierFailed(container, gaugeId, data.error || 'Unknown error');
                            }
                        })
                        .catch(function() {});
                }, 10000);
            }
