# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Shared JS utilities: formatting helpers, color functions."""


def get_js() -> str:
    """Return JS for shared utility functions."""
    return """
            // ==============================================================
            // Shared utilities
            // ==============================================================
            function getBaseUrl() {
                var cfg = window.__BACKEND_CONFIG || {};
                return cfg.url || '';
            }

            function fmtGBP(v) {
                if (v == null || v === 0) return '\\u2014';
                var cc = (window.__BACKEND_CONFIG || {}).currency || 'GBP';
                var sym = {GBP: '\\u00a3', USD: '$', EUR: '\\u20ac'}[cc] || (cc + ' ');
                return sym + v.toLocaleString('en-GB', {minimumFractionDigits: 0, maximumFractionDigits: 0});
            }

            function fmtPct(v) {
                if (v == null) return '\\u2014';
                return v.toFixed(1) + '%';
            }

            function fmtDepth(v) {
                if (v == null) return '\\u2014';
                return v.toFixed(2) + 'm';
            }

            function fmtMonths(v) {
                if (!v) return '\\u2014';
                var yrs = Math.floor(v / 12);
                var mos = v % 12;
                return yrs + 'y ' + mos + 'm';
            }

            // Color helpers for sim map
            function spGaugeColor(status) {
                if (status === 'severe') return '#d32f2f';
                if (status === 'warning') return '#f57c00';
                if (status === 'alert') return '#fbc02d';
                return '#4caf50';
            }
            function spWavefrontColor(p) {
                if (p.peak || (p.flooded && p.depth_m >= 1.0)) return '#d32f2f';
                if (p.flooded) return '#ff9800';
                if (p.arrived) return '#2196f3';
                return '#90caf9';
            }
"""
