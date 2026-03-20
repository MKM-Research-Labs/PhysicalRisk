"""
Classifiers — setup sub-module.

State variables, DOM construction, data loading.
Sub-modules imported and concatenated here.
"""

from . import summary_table, detail, training


def get_js() -> str:
    """Return JavaScript fragment for the full Classifiers tab (Tab 9)."""
    return (
        _get_setup_js()
        + summary_table.get_js()
        + detail.get_js()
        + training.get_js()
    )


def _get_setup_js() -> str:
    """Return JavaScript for state, DOM, and data loading."""
    return """
            // ==============================================================
            // Tab 9: Classifiers — GBM flood classifier management
            // ==============================================================
            var clSummary = null;
            var clSelectedGaugeId = null;
            var clFeatureChart = null;
            var clBatchPollTimer = null;

            function createClassifiersView() {
                var view = document.createElement('div');
                view.id = 'td-classifiers-view';
                view.style.cssText = 'flex:1;display:none;flex-direction:column;overflow:hidden;';

                // Top bar: Train All button + summary stats
                var topBar = document.createElement('div');
                topBar.id = 'cl-top-bar';
                topBar.style.cssText = 'padding:8px 16px;border-bottom:1px solid #eee;display:flex;align-items:center;gap:12px;background:#f5f7fa;flex-shrink:0;';
                topBar.innerHTML =
                    '<button id="cl-train-all-btn" style="padding:5px 14px;font-size:11px;font-weight:600;' +
                    'background:#1976d2;color:white;border:none;border-radius:3px;cursor:pointer;">' +
                    'Train All Untrained</button>' +
                    '<span id="cl-summary-stats" style="flex:1;font-size:11px;color:#666;text-align:right;"></span>';
                view.appendChild(topBar);

                // Progress bar (hidden by default)
                var progressWrap = document.createElement('div');
                progressWrap.id = 'cl-progress-wrap';
                progressWrap.style.cssText = 'display:none;padding:6px 16px;border-bottom:1px solid #eee;background:#fafbfc;flex-shrink:0;';
                progressWrap.innerHTML =
                    '<div style="display:flex;align-items:center;gap:10px;">' +
                    '<div style="flex:1;height:18px;background:#e0e0e0;border-radius:9px;overflow:hidden;position:relative;">' +
                    '<div id="cl-progress-bar" style="height:100%;width:0%;background:linear-gradient(90deg,#1976d2,#42a5f5);' +
                    'border-radius:9px;transition:width 0.5s ease;"></div>' +
                    '</div>' +
                    '<span id="cl-progress-text" style="font-size:10px;color:#555;min-width:200px;"></span>' +
                    '</div>';
                view.appendChild(progressWrap);

                // Main body: table (left) + detail (right)
                var body = document.createElement('div');
                body.style.cssText = 'flex:1;display:flex;overflow:hidden;';

                var tablePane = document.createElement('div');
                tablePane.id = 'cl-table-pane';
                tablePane.style.cssText = 'width:55%;overflow-y:auto;border-right:1px solid #eee;';

                var detailPane = document.createElement('div');
                detailPane.id = 'cl-detail-pane';
                detailPane.style.cssText = 'width:45%;overflow-y:auto;padding:16px;';
                detailPane.innerHTML =
                    '<div style="text-align:center;color:#999;font-size:12px;padding-top:40px;">' +
                    'Select a gauge to view classifier details</div>';

                body.appendChild(tablePane);
                body.appendChild(detailPane);
                view.appendChild(body);

                return view;
            }

            function loadClassifiersData() {
                var cfg = window.__BACKEND_CONFIG || {};
                var baseUrl = cfg.url || '';

                fetch(baseUrl + '/api/v1/trading/classifiers/summary', {mode: 'cors'})
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        if (data.status === 'success') {
                            clSummary = data;
                            _clUpdateStatsBar(data);
                            _clRenderSummaryTable(data.gauges || []);
                            // Reselect previously selected gauge
                            if (clSelectedGaugeId) {
                                var g = (data.gauges || []).find(function(x) {
                                    return x.gauge_id === clSelectedGaugeId;
                                });
                                if (g) _clRenderDetail(g);
                            }
                        }
                    })
                    .catch(function(err) {
                        console.error('[Classifiers] Summary fetch error:', err);
                    });
            }

            function _clUpdateStatsBar(data) {
                var el = document.getElementById('cl-summary-stats');
                if (!el) return;
                var trained = data.num_trained || 0;
                var total = data.num_total || 0;
                var auc = data.avg_auc_roc;
                var txt = trained + '/' + total + ' trained';
                if (auc) txt += '  \\u00b7  avg AUC ' + auc.toFixed(4);
                el.textContent = txt;
            }

            function clCleanupCharts() {
                if (clFeatureChart) {
                    clFeatureChart.destroy();
                    clFeatureChart = null;
                }
                if (clBatchPollTimer) {
                    clearInterval(clBatchPollTimer);
                    clBatchPollTimer = null;
                }
            }
"""
