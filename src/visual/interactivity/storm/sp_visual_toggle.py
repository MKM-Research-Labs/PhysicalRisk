# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""sp_visual — gauge visibility toggle functions and outside-click listener."""


def get_toggle_js() -> str:
    """Return JS for toggleGaugeVisibility, toggleAllGauges, updateGaugeBtnLabel."""
    return """
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
"""
