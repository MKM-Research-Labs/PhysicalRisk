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
EOD (End of Day) — actions sub-module.

EOD PDF download, EOD submit handler, and chart cleanup.
"""


def get_js() -> str:
    """Return JavaScript fragment for EOD actions."""
    return """
            window.tdDownloadEodPdf = function(eodDate) {
                var url = getBaseUrl() + '/api/v1/trading/eod/' + eodDate + '/pdf';
                fetch(url, {mode: 'cors'})
                    .then(function(r) {
                        if (!r.ok) throw new Error('HTTP ' + r.status);
                        return r.blob();
                    })
                    .then(function(blob) {
                        // Try inline display first, fallback to new tab
                        var reader = new FileReader();
                        reader.onload = function() {
                            var base64 = reader.result.split(',')[1];
                            if (window.PropertyPDFPanel && typeof window.PropertyPDFPanel.show === 'function') {
                                window.PropertyPDFPanel.show('EOD-' + eodDate, base64);
                            } else {
                                window.open(URL.createObjectURL(blob), '_blank');
                            }
                        };
                        reader.readAsDataURL(blob);
                    })
                    .catch(function(err) {
                        console.error('[EOD] PDF download error:', err);
                        if (window.showError) window.showError('EOD PDF not available for ' + eodDate);
                    });
            };

            window.tdSubmitEod = function() {
                var dateInput = document.getElementById('td-eod-date');
                var eodDate = dateInput ? dateInput.value : '';
                var statusEl = document.getElementById('td-eod-status');

                if (statusEl) statusEl.textContent = 'Submitting\\u2026';

                var url = getBaseUrl() + '/api/v1/trading/eod';
                window.__mkmAdminFetch(url, {
                    method: 'POST',
                    body: JSON.stringify({date: eodDate}),
                    mode: 'cors'
                })
                .then(function(r) { return r.json(); })
                .then(function(result) {
                    if (result.status === 'success') {
                        if (window.showSuccess) window.showSuccess(result.message);
                        if (statusEl) statusEl.textContent = 'EOD submitted: ' + result.eod_id;

                        // Show PDF if available
                        if (result.pdf_base64 && window.PropertyPDFPanel) {
                            window.PropertyPDFPanel.show('EOD-' + eodDate, result.pdf_base64);
                        }

                        // Reload EOD data
                        loadEodData();
                    } else {
                        if (window.showError) window.showError(result.message || 'EOD submit failed');
                        if (statusEl) statusEl.textContent = 'Failed: ' + (result.message || 'Unknown error');
                    }
                })
                .catch(function(err) {
                    if (window.showError) window.showError('EOD submit failed: ' + err.message);
                    if (statusEl) statusEl.textContent = 'Error: ' + err.message;
                });
            };

            function tdCleanupEodCharts() {
                if (tdEodChart) {
                    tdEodChart.destroy();
                    tdEodChart = null;
                }
            }
"""
