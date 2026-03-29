# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Shared HTML helper functions (sectionHeader, infoRow)."""


def get_helpers_js():
    """Return JS for shared HTML helpers."""
    return """
// ================================================================
// HTML helpers
// ================================================================
function sectionHeader(text) {
    return '<div style="font-size:11px;font-weight:700;color:#333;text-transform:uppercase;letter-spacing:0.5px;margin-top:16px;margin-bottom:8px;padding-bottom:4px;border-bottom:1px solid #eee;">' + text + '</div>';
}

function infoRow(label, value) {
    return '<div style="display:flex;padding:3px 0;font-size:11px;">' +
        '<span style="min-width:130px;color:#888;flex-shrink:0;">' + label + '</span>' +
        '<span style="color:#333;">' + value + '</span></div>';
}
"""
