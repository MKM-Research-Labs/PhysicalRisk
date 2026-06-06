
            // ---- Chart tab switching ----
            function _tdSwitchStressChart(idx) {
                tdStressChartTab = idx;
                for (var i = 0; i < 3; i++) {
                    var tab = document.getElementById('td-stress-ctab-' + i);
                    if (tab) {
                        tab.style.borderBottomColor = (i === idx) ? '#1565c0' : 'transparent';
                        tab.style.color = (i === idx) ? '#1565c0' : '#999';
                    }
                }
                _tdDrawStressChart();
            }

            function _tdDrawStressChart() {
                if (!tdStressResult) return;
                var chartWrap = document.getElementById('td-stress-chart-wrap');
                if (tdStressChartTab === 2) {
                    // Surface tab: show table, hide canvas
                    if (tdStressChart) { tdStressChart.destroy(); tdStressChart = null; }
                    if (chartWrap) chartWrap.innerHTML = '<div id="td-stress-surface-wrap" style="width:100%;height:100%;overflow:auto;"></div>';
                    _tdRenderSurfaceTable(tdStressResult);
                } else {
                    // Chart tabs: restore canvas if needed
                    if (chartWrap && !document.getElementById('td-stress-chart-canvas')) {
                        chartWrap.innerHTML = '<canvas id="td-stress-chart-canvas" style="width:100%;height:100%;"></canvas>';
                    }
                    if (tdStressChartTab === 0) {
                        _tdRenderProbabilityChart(tdStressResult);
                    } else {
                        _tdRenderStressPnlChart(tdStressResult);
                    }
                }
            }
