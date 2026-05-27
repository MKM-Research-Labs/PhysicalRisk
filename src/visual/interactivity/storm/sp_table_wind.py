# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

"""
Storm portfolio Table tab — Wind Damage sub-tab JS.

Same shape as Flood Damage: a combined residential + commercial table
with Damage £ and Damage % columns. Damage is computed as a function of
peak wind speed and a percentile assumption — that model isn't wired
up yet, so this tab currently lists every asset with the damage cells
blank.

When the wind model lands, override ``window.WindDamageModel.compute``
to return ``{damage_amount, damage_ratio}`` per row and the table
will repopulate without further frontend changes.
"""


def get_js() -> str:
    """Return JS fragment for the Wind Damage sub-tab (parent IIFE scope)."""
    return """
            // ================================================================
            // Wind Damage — combined residential + commercial rows
            // ================================================================
            //
            // Wind model not yet wired. Until then we list every asset in
            // the portfolio so the user can see what *will* be in scope.
            // Damage £ / Damage % are rendered as em-dashes (— ) by the
            // shared _renderDamageTable when the field is null/undefined.
            // ================================================================

            window.WindDamageModel = window.WindDamageModel || {
                // Stub: returns nulls until the model is connected.
                // Future signature: compute({asset, peak_wind_mps, percentile})
                //   -> {damage_amount, damage_ratio}
                compute: function(_row) { return {damage_amount: null, damage_ratio: null}; },
            };

            function _windRows() {
                var rows = [];

                // Residential — from the blotter (full portfolio, not just affected)
                if (spBlotterData && spBlotterData.properties) {
                    spBlotterData.properties.forEach(function(p) {
                        var d = window.WindDamageModel.compute(p);
                        rows.push({
                            asset_id: p.property_id,
                            asset_class: 'residential',
                            address: p.property_address,
                            type: 'Residential',
                            value: p.property_value,
                            damage_amount: d.damage_amount,
                            damage_ratio: d.damage_ratio,
                            outstanding_balance: p.outstanding_balance,
                            current_ltv: p.current_ltv,
                            remaining_term_months: p.remaining_term_months,
                        });
                    });
                }

                // Commercial — from the commercial blotter
                if (spCommercialData && spCommercialData.assets) {
                    spCommercialData.assets.forEach(function(a) {
                        var d = window.WindDamageModel.compute(a);
                        rows.push({
                            asset_id: a.property_id,
                            asset_class: 'commercial',
                            address: a.property_address,
                            type: a.commercial_type || 'Commercial',
                            value: a.property_value,
                            damage_amount: d.damage_amount,
                            damage_ratio: d.damage_ratio,
                            outstanding_balance: a.outstanding_balance,
                            current_ltv: a.current_ltv,
                            remaining_term_months: a.remaining_term_months,
                        });
                    });
                }
                return rows;
            }

            function loadWindDamage() {
                var summary = document.getElementById('sp-summary');

                // The wind tab depends on both blotters being loaded so it
                // can list every asset. Trigger loads if either is missing,
                // then re-enter when the data arrives.
                var pending = [];
                if (!spBlotterData) pending.push(
                    fetch(getBaseUrl() + '/api/v1/propertyts/blotter', {mode:'cors'})
                        .then(function(r){return r.json();})
                        .then(function(d){ if (d.status === 'success') spBlotterData = d; })
                );
                if (!spCommercialData) pending.push(
                    fetch(getBaseUrl() + '/api/v1/commercial/blotter', {mode:'cors'})
                        .then(function(r){return r.json();})
                        .then(function(d){ if (d.status === 'success') spCommercialData = d; })
                );

                if (pending.length) {
                    var container = document.getElementById('sp-table-container');
                    container.innerHTML = '<div style="padding:24px;text-align:center;color:#999;">Loading portfolio for wind exposure...</div>';
                    Promise.all(pending).then(_renderWindDamage);
                } else {
                    _renderWindDamage();
                }
            }

            function _renderWindDamage() {
                var rows = _windRows();
                _renderWindSummary(rows);
                _renderDamageTable(rows, 'wind');
            }

            function _renderWindSummary(rows) {
                var summary = document.getElementById('sp-summary');
                var resCount = rows.filter(function(r){return r.asset_class === 'residential';}).length;
                var comCount = rows.filter(function(r){return r.asset_class === 'commercial';}).length;
                var totalDamage = rows.reduce(function(a,r){ return a + (r.damage_amount || 0); }, 0);
                var cards = [
                    { label: 'Properties In Scope', value: resCount, color: '#1976d2' },
                    { label: 'Commercials In Scope', value: comCount, color: '#1976d2' },
                    { label: 'Total Wind Damage', value: totalDamage ? fmtGBP(totalDamage) : '\\u2014', color: '#d32f2f' },
                    { label: 'Model Status', value: 'Pending', color: '#888' },
                ];
                summary.innerHTML = '';
                cards.forEach(function(card) {
                    var div = document.createElement('div');
                    div.style.cssText = 'flex:1;min-width:120px;padding:8px 12px;border-radius:6px;background:#f5f5f5;border-left:3px solid ' + card.color + ';';
                    div.innerHTML = '<div style="font-size:10px;color:#888;text-transform:uppercase;letter-spacing:0.5px;">' + card.label + '</div>' +
                        '<div style="font-size:16px;font-weight:700;color:' + card.color + ';margin-top:2px;">' + card.value + '</div>';
                    summary.appendChild(div);
                });
            }
"""
