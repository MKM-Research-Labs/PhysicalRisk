
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

                if (statusEl) statusEl.textContent = 'Submitting\u2026';

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
