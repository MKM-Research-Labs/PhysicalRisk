# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""sp_visual — data loading and stats rendering."""


def get_data_js() -> str:
    """Return JS for storm label lookup, loadSimData, and renderSimStats."""
    return """
            // ================================================================
            // Simulation data loading
            // ================================================================
            function _getStormLabel(stormId) {
                var sel = document.getElementById('sp-storm-select');
                if (sel) {
                    for (var i = 0; i < sel.options.length; i++) {
                        if (sel.options[i].value === stormId) return sel.options[i].textContent;
                    }
                }
                return stormId;
            }

            function loadSimData(stormId) {
                if (!stormId) return;
                console.log('[StormPortfolio] Loading simulation for', stormId);
                var wrap = document.getElementById('sp-sim-chart-wrap');
                wrap.innerHTML = '<div style="padding:40px;text-align:center;color:#888;">Loading simulation data...</div>';
                var stats = document.getElementById('sp-sim-stats');
                stats.innerHTML = '';
                var statsBar = document.getElementById('sp-stats-bar');
                statsBar.innerHTML = '<span>Loading simulation...</span>';

                var stormLabel = _getStormLabel(stormId);

                var baseUrl = getBaseUrl();
                fetch(baseUrl + '/api/v1/propertyts/animate/' + stormId, {mode: 'cors'})
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        if (data.status !== 'success') {
                            wrap.innerHTML = '<div style="padding:40px;text-align:center;color:red;">Error: ' + (data.message || 'Unknown') + '</div>';
                            return;
                        }
                        spSimData = data;
                        spSimData._stormLabel = stormLabel;
                        console.log('[StormPortfolio] Simulation loaded:', data.n_frames, 'frames,', data.n_properties_affected, 'properties');
                        document.getElementById('sp-panel-title').textContent =
                            'Storm Simulation \u2014 ' + stormLabel;
                        renderSimChart(data);
                        renderSimStats(data);

                        statsBar.innerHTML =
                            '<span>Storm: <b>' + stormLabel + '</b></span>' +
                            '<span>Duration: <b>' + data.n_frames + '</b> hours</span>' +
                            '<span>Properties: <b>' + data.n_properties_affected + '</b></span>';
                    })
                    .catch(function(err) {
                        wrap.innerHTML = '<div style="padding:40px;text-align:center;color:red;">Failed to load simulation</div>';
                        console.error('Sim error:', err);
                    });
            }

            function renderSimStats(data) {
                var stats = document.getElementById('sp-sim-stats');
                var frames = data.frames || [];

                var peakHour = 0;
                var peakFlooded = 0;
                var maxDepth = 0;
                var floodingHours = 0;
                frames.forEach(function(f) {
                    var nf = f.stats ? f.stats.properties_flooded : 0;
                    if (nf > peakFlooded) {
                        peakFlooded = nf;
                        peakHour = f.hour;
                    }
                    if (nf > 0) floodingHours++;
                    (f.properties || []).forEach(function(p) {
                        if (p.depth_m > maxDepth) maxDepth = p.depth_m;
                    });
                });

                var cards = [
                    { label: 'Properties Affected', value: data.n_properties_affected, color: '#1976d2' },
                    { label: 'Peak Hour', value: 'Hour ' + peakHour + ' (' + peakFlooded + ' flooded)', color: '#d32f2f' },
                    { label: 'Max Flood Depth', value: maxDepth.toFixed(2) + 'm', color: '#f57c00' },
                    { label: 'Flooding Duration', value: floodingHours + ' hours', color: '#7b1fa2' },
                ];

                stats.innerHTML = '';
                var row = document.createElement('div');
                row.style.cssText = 'display:flex;gap:10px;width:100%;';
                cards.forEach(function(c) {
                    var card = document.createElement('div');
                    card.style.cssText = 'flex:1;min-width:120px;padding:8px 12px;border-radius:6px;background:#f5f5f5;border-left:3px solid ' + c.color + ';';
                    card.innerHTML = '<div style="font-size:10px;color:#888;text-transform:uppercase;letter-spacing:0.5px;">' + c.label + '</div>' +
                        '<div style="font-size:14px;font-weight:700;color:' + c.color + ';margin-top:2px;">' + c.value + '</div>';
                    row.appendChild(card);
                });
                stats.appendChild(row);
            }
"""
