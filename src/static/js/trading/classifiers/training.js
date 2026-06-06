
            function _clStartSingleTraining(gaugeId) {
                var cfg = window.__BACKEND_CONFIG || {};
                var baseUrl = cfg.url || '';

                // Update button to spinner
                var btns = document.querySelectorAll('button[data-train-gauge="' + gaugeId + '"]');
                for (var i = 0; i < btns.length; i++) {
                    btns[i].disabled = true;
                    btns[i].textContent = 'Training\u2026';
                    btns[i].style.background = '#90a4ae';
                }

                window.__mkmAdminFetch(baseUrl + '/api/v1/trading/stress/train/' + gaugeId, {
                    method: 'POST',
                    mode: 'cors'
                })
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    if (data.status === 'ready') {
                        // Already trained
                        loadClassifiersData();
                        return;
                    }
                    // Poll for completion
                    var pollId = setInterval(function() {
                        fetch(baseUrl + '/api/v1/trading/stress/classifier-status/' + gaugeId, {mode: 'cors'})
                            .then(function(r) { return r.json(); })
                            .then(function(st) {
                                if (st.status === 'ready') {
                                    clearInterval(pollId);
                                    clSelectedGaugeId = gaugeId;
                                    loadClassifiersData();
                                } else if (st.status === 'failed') {
                                    clearInterval(pollId);
                                    console.error('[Classifiers] Training failed:', st.error);
                                    loadClassifiersData();
                                }
                            })
                            .catch(function() { clearInterval(pollId); });
                    }, 5000);
                })
                .catch(function(err) {
                    console.error('[Classifiers] Train POST error:', err);
                    loadClassifiersData();
                });
            }

            // Batch training: Train All button handler (bound in setup)
            (function() {
                // Defer binding until DOM is ready
                var _clBindTrainAll = function() {
                    var btn = document.getElementById('cl-train-all-btn');
                    if (btn && !btn._clBound) {
                        btn._clBound = true;
                        btn.addEventListener('click', function() {
                            _clStartBatchTraining();
                        });
                    }
                    var clearBtn = document.getElementById('cl-clear-all-btn');
                    if (clearBtn && !clearBtn._clBound) {
                        clearBtn._clBound = true;
                        clearBtn.addEventListener('click', function() {
                            _clClearAll();
                        });
                    }
                };

                // Try binding after tab switch creates the DOM
                var origLoad = window.loadClassifiersData || function() {};
                var patchedLoad = function() {
                    origLoad();
                    setTimeout(_clBindTrainAll, 100);
                };
                // We override via a post-load hook instead of replacing loadClassifiersData
                // Just call the binder after each data load
                var _origRenderTable = _clRenderSummaryTable;
                _clRenderSummaryTable = function(gauges) {
                    _origRenderTable(gauges);
                    _clBindTrainAll();
                };
            })();

            function _clStartBatchTraining() {
                var cfg = window.__BACKEND_CONFIG || {};
                var baseUrl = cfg.url || '';
                var btn = document.getElementById('cl-train-all-btn');
                if (btn) {
                    btn.disabled = true;
                    btn.textContent = 'Training\u2026';
                    btn.style.background = '#90a4ae';
                }

                // Show progress bar
                var wrap = document.getElementById('cl-progress-wrap');
                if (wrap) wrap.style.display = 'block';
                _clUpdateProgress(0, 0, null, null);

                // Inform user this will take a while
                if (window.showSuccess) {
                    window.showSuccess(
                        'Training started. This will take approximately 10\u201320 minutes. ' +
                        'Feel free to navigate elsewhere \u2014 you will be notified when complete.'
                    );
                }

                window.__mkmAdminFetch(baseUrl + '/api/v1/trading/classifiers/train-all', {
                    method: 'POST',
                    mode: 'cors'
                })
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    if (data.status === 'complete') {
                        // All already trained
                        _clHideProgress();
                        loadClassifiersData();
                        return;
                    }
                    // Start polling
                    clBatchPollTimer = setInterval(function() {
                        _clPollBatchStatus(baseUrl);
                    }, 5000);
                })
                .catch(function(err) {
                    console.error('[Classifiers] Train-all POST error:', err);
                    _clHideProgress();
                    loadClassifiersData();
                });
            }

            function _clPollBatchStatus(baseUrl) {
                fetch(baseUrl + '/api/v1/trading/classifiers/train-all/status', {mode: 'cors'})
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        _clUpdateProgress(data.completed, data.total, data.current_gauge_id, data.eta_seconds);
                        _clUpdateProgressResults(data.results || [], data.avg_auc, data.num_trained, data.num_failed, data.num_skipped);
                        if (data.status === 'complete') {
                            if (clBatchPollTimer) {
                                clearInterval(clBatchPollTimer);
                                clBatchPollTimer = null;
                            }
                            // Notify the user (works even if they navigated away)
                            if (window.showSuccess) {
                                window.showSuccess(
                                    'Classifier training complete! ' +
                                    data.completed + '/' + data.total + ' gauges trained.' +
                                    (data.avg_auc ? ' Avg AUC: ' + data.avg_auc.toFixed(4) : '')
                                );
                            }
                            setTimeout(function() {
                                _clHideProgress();
                                loadClassifiersData();
                            }, 1000);
                        }
                    })
                    .catch(function(err) {
                        console.error('[Classifiers] Poll error:', err);
                    });
            }

            function _clUpdateProgress(completed, total, currentGauge, etaSeconds) {
                var bar = document.getElementById('cl-progress-bar');
                var txt = document.getElementById('cl-progress-text');
                if (!bar || !txt) return;

                var pct = total > 0 ? (completed / total * 100) : 0;
                bar.style.width = pct + '%';

                var msg = '[' + completed + '/' + total + ']';
                if (currentGauge) msg += ' Training ' + currentGauge + '\u2026';
                if (etaSeconds != null && etaSeconds > 0) {
                    if (etaSeconds < 60) msg += '  ETA ' + Math.round(etaSeconds) + 's';
                    else if (etaSeconds < 3600) msg += '  ETA ' + (etaSeconds / 60).toFixed(1) + 'm';
                    else msg += '  ETA ' + (etaSeconds / 3600).toFixed(1) + 'h';
                }
                if (completed === total && total > 0) msg = 'Complete! ' + total + ' classifiers trained.';
                txt.textContent = msg;
            }

            function _clUpdateProgressResults(results, avgAuc, numTrained, numFailed, numSkipped) {
                var el = document.getElementById('cl-progress-results');
                if (!el) return;
                if (results.length === 0) { el.style.display = 'none'; return; }
                el.style.display = 'block';

                // Summary line
                var summ = '<div style="margin-bottom:4px;font-weight:600;font-family:sans-serif;">';
                if (avgAuc != null) summ += 'Avg AUC: ' + avgAuc.toFixed(4) + '  \u00b7  ';
                summ += (numTrained || 0) + ' trained';
                if (numFailed) summ += ', <span style="color:#c62828;">' + numFailed + ' failed</span>';
                if (numSkipped) summ += ', ' + numSkipped + ' skipped';
                summ += '</div>';

                // Per-gauge rows (most recent first)
                var rows = '';
                for (var i = results.length - 1; i >= 0; i--) {
                    var r = results[i];
                    var icon = r.status === 'trained' ? '\u2713' : r.status === 'failed' ? '\u2717' : '\u2298';
                    var color = r.status === 'trained' ? '#2e7d32' : r.status === 'failed' ? '#c62828' : '#f57f17';
                    var timeStr = r.elapsed_seconds != null ? r.elapsed_seconds.toFixed(1) + 's' : '\u2014';
                    var aucStr = r.auc_roc != null ? 'AUC ' + r.auc_roc.toFixed(3) : (r.error ? r.error.substring(0, 30) : '\u2014');
                    rows += '<div style="color:' + color + ';">' +
                        icon + ' ' + r.gauge_id + '  ' + timeStr + '  ' + aucStr + '</div>';
                }
                el.innerHTML = summ + rows;
                // Auto-scroll to top (latest result)
                el.scrollTop = 0;
            }

            function _clHideProgress() {
                var wrap = document.getElementById('cl-progress-wrap');
                if (wrap) wrap.style.display = 'none';
                var results = document.getElementById('cl-progress-results');
                if (results) results.style.display = 'none';
                var btn = document.getElementById('cl-train-all-btn');
                if (btn) {
                    btn.disabled = false;
                    btn.textContent = 'Train All Untrained';
                    btn.style.background = '#1976d2';
                }
            }

            function _clClearAll() {
                if (!confirm('Delete all trained classifiers? You will need to retrain them.')) return;
                var cfg = window.__BACKEND_CONFIG || {};
                var baseUrl = cfg.url || '';
                var btn = document.getElementById('cl-clear-all-btn');
                if (btn) {
                    btn.disabled = true;
                    btn.textContent = 'Clearing\u2026';
                    btn.style.background = '#90a4ae';
                }

                window.__mkmAdminFetch(baseUrl + '/api/v1/trading/classifiers/clear-all', {
                    method: 'POST',
                    mode: 'cors'
                })
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    if (btn) {
                        btn.disabled = false;
                        btn.textContent = 'Clear All';
                        btn.style.background = '#e53935';
                    }
                    clSelectedGaugeId = null;
                    var detailPane = document.getElementById('cl-detail-pane');
                    if (detailPane) {
                        detailPane.innerHTML =
                            '<div style="text-align:center;color:#999;font-size:12px;padding-top:40px;">' +
                            'Select a gauge to view classifier details</div>';
                    }
                    loadClassifiersData();
                })
                .catch(function(err) {
                    console.error('[Classifiers] Clear error:', err);
                    if (btn) {
                        btn.disabled = false;
                        btn.textContent = 'Clear All';
                        btn.style.background = '#e53935';
                    }
                });
            }
