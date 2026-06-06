
            // ================================================================
            // PRS Controls (input form for Tab 2)
            // ================================================================
            function buildPRSControls() {
                var controls = document.getElementById('phc-controls');
                var inputStyle = 'padding:3px 6px;border:1px solid #ccc;border-radius:3px;width:90px;font-size:11px;';
                var labelStyle = 'font-weight:600;font-size:11px;color:#555;margin-right:3px;';
                var selectStyle = 'padding:3px 6px;border:1px solid #ccc;border-radius:3px;font-size:11px;';

                // Build counterparty options
                var ctpyOptions = '<option value="">-- Select --</option>';
                counterpartyData.forEach(function(c) {
                    var label = c.short_name + ' (' + c.credit_rating + ')';
                    ctpyOptions += '<option value="' + c.counterparty_id + '">' + label + '</option>';
                });

                // Build EA zone dropdown, default to property's actual zone
                var zoneOrder = ['Zone 3b', 'Zone 3a', 'Zone 3', 'Zone 2', 'Zone 1'];
                var actualZone = phcData.flood_zone || 'Zone 1';
                var zoneOptions = '';
                zoneOrder.forEach(function(z) {
                    var sel = (z === actualZone) ? ' selected' : '';
                    zoneOptions += '<option value="' + z + '"' + sel + '>' + z + '</option>';
                });

                controls.innerHTML =
                    '<div style="display:flex;align-items:center;gap:12px;padding:8px 16px;flex-wrap:wrap;">' +
                    '<span style="' + labelStyle + '">Direction:</span>' +
                    '<select id="phc-direction" style="' + selectStyle + '">' +
                    '<option value="payer">Payer (buy protection)</option>' +
                    '<option value="receiver">Receiver (sell protection)</option>' +
                    '</select>' +
                    '<span style="' + labelStyle + '">Ctpy:</span>' +
                    '<select id="phc-counterparty" style="' + selectStyle + 'min-width:140px;">' +
                    ctpyOptions +
                    '</select>' +
                    '<span style="' + labelStyle + '">EA Zone:</span>' +
                    '<select id="phc-ea-zone" style="' + selectStyle + '">' +
                    zoneOptions +
                    '</select>' +
                    '<span style="' + labelStyle + '">Notional:</span>' +
                    '<input id="phc-notional" type="text" value="10,000,000" style="' + inputStyle + '">' +
                    '<span style="' + labelStyle + '">Tenor (yr):</span>' +
                    '<input id="phc-tenor" type="number" value="5" min="1" max="30" style="' + inputStyle + 'width:50px;">' +
                    '<span style="' + labelStyle + '">Spread (bps):</span>' +
                    '<input id="phc-spread" type="number" value="' + Math.round(((phcData.term_structure || {}).severe || {}).prs_spread_bps ? phcData.term_structure.severe.prs_spread_bps[0] : 100) + '" min="1" max="10000" style="' + inputStyle + 'width:60px;">' +
                    '</div>';

                // Auto-recompute on any input change
                var ids = ['phc-direction', 'phc-counterparty', 'phc-ea-zone', 'phc-notional', 'phc-tenor', 'phc-spread'];
                ids.forEach(function(id) {
                    var el = document.getElementById(id);
                    if (el) el.addEventListener('change', function() { if (activeTab === 2) renderPRSPricing(); });
                });
            }

