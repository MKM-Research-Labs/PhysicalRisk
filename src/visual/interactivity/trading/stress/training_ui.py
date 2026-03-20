# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Trading desk Stress Test — on-demand classifier training UI.

Handles classifier status check, "Train Now" button, training progress
spinner with polling, and error/retry flow for the trading desk stress tab.
"""


def get_js() -> str:
    """Return JS fragment for on-demand classifier training UI (trading desk)."""
    return """
            // ----------------------------------------------------------------
            // Trading desk classifier training UI (on-demand)
            // ----------------------------------------------------------------
            var _tdStressTrainingPollTimer = null;

            function _tdShowNotTrained(gaugeId) {
                var stormSel = document.getElementById('td-stress-storm');
                if (stormSel) stormSel.innerHTML = '<option value="">Classifier not trained</option>';
                var tableWrap = document.getElementById('td-stress-table-wrap');
                if (tableWrap) {
                    tableWrap.innerHTML =
                        '<div style="text-align:center;padding:40px 20px;">' +
                            '<div style="font-size:24px;color:#e0e0e0;margin-bottom:12px;">&#9888;</div>' +
                            '<div style="font-size:12px;font-weight:600;color:#333;margin-bottom:8px;">Classifier Not Available</div>' +
                            '<div style="font-size:11px;color:#666;margin-bottom:16px;">' +
                                'No trained flood classifier for this gauge.<br>Training takes approx. 3-5 minutes.' +
                            '</div>' +
                            '<button id="td-stress-train-btn" style="padding:6px 20px;font-size:11px;font-weight:600;' +
                                'background:#1565c0;color:#fff;border:none;border-radius:3px;cursor:pointer;">Train Now</button>' +
                            '<div id="td-stress-train-msg" style="font-size:10px;color:#999;margin-top:8px;"></div>' +
                        '</div>';
                    var btn = document.getElementById('td-stress-train-btn');
                    if (btn) btn.addEventListener('click', function() { _tdStartTraining(gaugeId); });
                }
            }

            function _tdShowTrainingInProgress(gaugeId, elapsed) {
                var stormSel = document.getElementById('td-stress-storm');
                if (stormSel) stormSel.innerHTML = '<option value="">Training classifier...</option>';
                var tableWrap = document.getElementById('td-stress-table-wrap');
                if (tableWrap) {
                    tableWrap.innerHTML =
                        '<div style="text-align:center;padding:40px 20px;">' +
                            '<div style="width:32px;height:32px;border:3px solid #e0e0e0;border-top:3px solid #1565c0;' +
                                'border-radius:50%;animation:tdStressSpin 1s linear infinite;margin:0 auto 12px;"></div>' +
                            '<div style="font-size:12px;font-weight:600;color:#333;">Training Classifier</div>' +
                            '<div id="td-stress-train-elapsed" style="font-size:11px;color:#666;margin-top:6px;">' +
                                'Training in progress... (' + elapsed + 's elapsed)' +
                            '</div>' +
                            '<div style="font-size:10px;color:#999;margin-top:8px;">You can switch tabs — training continues in the background.</div>' +
                        '</div>' +
                        '<style>@keyframes tdStressSpin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }</style>';
                }
                _tdPollClassifierStatus(gaugeId);
            }

            function _tdShowTrainingFailed(gaugeId, error) {
                var stormSel = document.getElementById('td-stress-storm');
                if (stormSel) stormSel.innerHTML = '<option value="">Training failed</option>';
                var tableWrap = document.getElementById('td-stress-table-wrap');
                if (tableWrap) {
                    tableWrap.innerHTML =
                        '<div style="text-align:center;padding:40px 20px;">' +
                            '<div style="font-size:24px;color:#c00;margin-bottom:12px;">&#10060;</div>' +
                            '<div style="font-size:12px;font-weight:600;color:#c00;margin-bottom:8px;">Training Failed</div>' +
                            '<div style="font-size:11px;color:#666;margin-bottom:16px;">' + error + '</div>' +
                            '<button id="td-stress-retry-btn" style="padding:6px 20px;font-size:11px;font-weight:600;' +
                                'background:#1565c0;color:#fff;border:none;border-radius:3px;cursor:pointer;">Retry</button>' +
                        '</div>';
                    var btn = document.getElementById('td-stress-retry-btn');
                    if (btn) btn.addEventListener('click', function() { _tdStartTraining(gaugeId); });
                }
            }

            function _tdStartTraining(gaugeId) {
                var cfg = window.__BACKEND_CONFIG || {};
                var baseUrl = cfg.url || '';
                var msgEl = document.getElementById('td-stress-train-msg');
                if (msgEl) msgEl.textContent = 'Starting training...';
                var btn = document.getElementById('td-stress-train-btn');
                if (btn) { btn.disabled = true; btn.style.opacity = '0.6'; }

                fetch(baseUrl + '/api/v1/trading/stress/train/' + gaugeId, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    mode: 'cors'
                })
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    if (data.status === 'ready') {
                        _tdLoadStorms(gaugeId);
                    } else if (data.status === 'training') {
                        _tdShowTrainingInProgress(gaugeId, 0);
                    } else {
                        if (msgEl) msgEl.textContent = 'Error: ' + (data.message || 'Failed');
                        if (btn) { btn.disabled = false; btn.style.opacity = '1'; }
                    }
                })
                .catch(function(err) {
                    console.error('[Stress] Train error:', err);
                    if (msgEl) msgEl.textContent = 'Network error';
                    if (btn) { btn.disabled = false; btn.style.opacity = '1'; }
                });
            }

            function _tdPollClassifierStatus(gaugeId) {
                if (_tdStressTrainingPollTimer) clearInterval(_tdStressTrainingPollTimer);
                var cfg = window.__BACKEND_CONFIG || {};
                var baseUrl = cfg.url || '';

                _tdStressTrainingPollTimer = setInterval(function() {
                    fetch(baseUrl + '/api/v1/trading/stress/classifier-status/' + gaugeId, {mode: 'cors'})
                        .then(function(r) { return r.json(); })
                        .then(function(data) {
                            if (data.status === 'ready') {
                                clearInterval(_tdStressTrainingPollTimer);
                                _tdStressTrainingPollTimer = null;
                                _tdLoadStorms(gaugeId);
                            } else if (data.status === 'training') {
                                var el = document.getElementById('td-stress-train-elapsed');
                                if (el) el.textContent = 'Training in progress... (' + (data.elapsed_seconds || 0) + 's elapsed)';
                            } else if (data.status === 'failed') {
                                clearInterval(_tdStressTrainingPollTimer);
                                _tdStressTrainingPollTimer = null;
                                _tdShowTrainingFailed(gaugeId, data.error || 'Unknown error');
                            }
                        })
                        .catch(function() {});
                }, 10000);
            }
"""
