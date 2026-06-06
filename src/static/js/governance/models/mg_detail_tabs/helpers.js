
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
