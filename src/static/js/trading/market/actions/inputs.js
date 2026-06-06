
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
