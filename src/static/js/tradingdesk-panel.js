(function() {
    var PANEL_W = '__PANEL_W__';
    var PANEL_H = '__PANEL_H__';
    var tdPanel = null;
    var tdActiveTab = 'blotter';

    // ==============================================================
    // Shared utilities
    // ==============================================================
    function getBaseUrl() {
        var cfg = window.__BACKEND_CONFIG || {};
        return cfg.url || '';
    }

    function fmtGBP(v) {
        if (v == null || v === 0) return '—';
        var sign = v < 0 ? '-' : '';
        var abs = Math.abs(v);
        var cc = (window.__BACKEND_CONFIG || {}).currency || 'GBP';
        var sym = {GBP: '£', USD: '$', EUR: '€'}[cc] || (cc + ' ');
        return sign + sym + abs.toLocaleString('en-GB', {minimumFractionDigits: 0, maximumFractionDigits: 0});
    }

    function fmtBps(v) {
        if (v == null) return '—';
        return v.toFixed(1) + ' bps';
    }

    // ==============================================================
    // Sub-module code
    // ==============================================================
__TD_PRELOADER_JS__
__TD_CLIENT_JS__
__TD_BLOTTER_JS__
__TD_MARKET_JS__
__TD_FS01_JS__
__TD_AGGREGATE_JS__
__TD_EOD_JS__
__TD_CURVES_JS__
__TD_STRESS_JS__
__TD_PORT_STRESS_JS__
__TD_CLASSIFIERS_JS__

__TD_PANEL_CREATE_JS__
__TD_PANEL_TABS_JS__
__TD_PANEL_LIFECYCLE_JS__
})();
