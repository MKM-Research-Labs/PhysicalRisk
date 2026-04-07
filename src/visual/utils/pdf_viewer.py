# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Shared PDF viewer panel factory.

Generates JavaScript for an inline overlay panel that displays
base64-encoded PDFs in an iframe.  Used by PropertyPDFPanel,
GaugePDFPanel, and the insurance claim-report viewer.
"""


def pdf_viewer_js(namespace: str,
                  panel_width: str = "850px",
                  panel_height: str = "90vh",
                  default_title: str = "Report",
                  btn_color: str = "#28a745",
                  event_name: str = None,
                  event_id_key: str = "id",
                  display_name_js: str = None) -> str:
    """Return a self-contained JS IIFE that creates a PDF viewer popup.

    Args:
        namespace: Unique prefix for DOM ids and the ``window`` API.
            E.g. ``"property-pdf"`` produces ``window.PropertyPDFPanel``.
        panel_width / panel_height: CSS dimensions for the overlay.
        default_title: Fallback title shown in the header.
        btn_color: CSS colour for the Download button.
        event_name: Optional custom-event name to listen for
            (e.g. ``"propertyPdfReady"``).  When fired with
            ``detail.{event_id_key}`` and ``detail.pdfBase64`` the
            panel opens automatically.
        event_id_key: Key inside ``event.detail`` that carries the
            entity id (e.g. ``"propertyId"``, ``"gaugeId"``).
        display_name_js: Optional JS expression that converts ``entityId``
            into a display label (e.g.
            ``"window.propertyDisplayName(entityId)"``).  Falls back to
            bare ``entityId`` if omitted or the expression returns falsy.

    Returns:
        JS string (no ``<script>`` tags — caller wraps if needed).
    """
    # Convert "property-pdf" → "PropertyPDFPanel" for the window API name.
    # Preserves the uppercase "PDF" that consumers expect.
    api_name = "".join(
        seg.upper() if seg == "pdf" else seg.capitalize()
        for seg in namespace.split("-")
    ) + "Panel"

    event_listener = ""
    if event_name:
        event_listener = f"""
            document.addEventListener('{event_name}', function(e) {{
                if (e.detail && e.detail.{event_id_key} && e.detail.pdfBase64) {{
                    showPanel(e.detail.{event_id_key}, e.detail.pdfBase64);
                }}
            }});"""

    return f"""
            (function() {{
                var PANEL_W = '{panel_width}';
                var PANEL_H = '{panel_height}';
                var pdfPanel = null;

                function createPanel() {{
                    if (pdfPanel) return pdfPanel;

                    pdfPanel = document.createElement('div');
                    pdfPanel.id = '{namespace}-panel';
                    pdfPanel.style.cssText =
                        'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);' +
                        'width:' + PANEL_W + ';height:' + PANEL_H + ';' +
                        'background:white;border:1px solid #ccc;border-radius:8px;' +
                        'box-shadow:0 4px 20px rgba(0,0,0,0.3);z-index:2000;' +
                        'display:none;flex-direction:column;font-family:Arial,sans-serif;';

                    var header = document.createElement('div');
                    header.style.cssText =
                        'display:flex;justify-content:space-between;align-items:center;' +
                        'padding:10px 16px;border-bottom:1px solid #eee;background:#f8f9fa;' +
                        'border-radius:8px 8px 0 0;min-height:40px;';

                    var title = document.createElement('span');
                    title.id = '{namespace}-title';
                    title.style.cssText = 'font-weight:bold;font-size:14px;color:#333;';
                    title.textContent = '{default_title}';

                    var btnGroup = document.createElement('div');
                    btnGroup.style.cssText = 'display:flex;gap:8px;';

                    var downloadBtn = document.createElement('button');
                    downloadBtn.id = '{namespace}-download';
                    downloadBtn.textContent = 'Download';
                    downloadBtn.style.cssText =
                        'padding:4px 12px;border:1px solid {btn_color};border-radius:4px;' +
                        'background:{btn_color};color:white;cursor:pointer;font-size:12px;';
                    downloadBtn.onclick = function() {{
                        var iframe = document.getElementById('{namespace}-iframe');
                        if (iframe && iframe.src) {{
                            var a = document.createElement('a');
                            a.href = iframe.src;
                            a.download = (title.textContent || '{default_title}') + '.pdf';
                            a.click();
                        }}
                    }};

                    var closeBtn = document.createElement('button');
                    closeBtn.textContent = 'Close';
                    closeBtn.style.cssText =
                        'padding:4px 12px;border:1px solid #dc3545;border-radius:4px;' +
                        'background:#dc3545;color:white;cursor:pointer;font-size:12px;';
                    closeBtn.onclick = function() {{ hidePanel(); }};

                    btnGroup.appendChild(downloadBtn);
                    btnGroup.appendChild(closeBtn);
                    header.appendChild(title);
                    header.appendChild(btnGroup);

                    var container = document.createElement('div');
                    container.id = '{namespace}-container';
                    container.style.cssText = 'flex:1;overflow:hidden;border-radius:0 0 8px 8px;';

                    var iframe = document.createElement('iframe');
                    iframe.id = '{namespace}-iframe';
                    iframe.style.cssText = 'width:100%;height:100%;border:none;';
                    container.appendChild(iframe);

                    pdfPanel.appendChild(header);
                    pdfPanel.appendChild(container);
                    document.body.appendChild(pdfPanel);

                    document.addEventListener('keydown', function(e) {{
                        if (e.key === 'Escape' && pdfPanel.style.display !== 'none') {{
                            hidePanel();
                        }}
                    }});

                    return pdfPanel;
                }}

                function showPanel(entityId, pdfBase64) {{
                    var panel = createPanel();
                    var title = document.getElementById('{namespace}-title');
                    var displayLabel = {display_name_js or 'entityId'};
                    title.textContent = '{default_title}: ' + (displayLabel || entityId);

                    var iframe = document.getElementById('{namespace}-iframe');
                    iframe.src = 'data:application/pdf;base64,' + pdfBase64;

                    panel.style.display = 'flex';
                }}

                function hidePanel() {{
                    if (pdfPanel) {{
                        pdfPanel.style.display = 'none';
                        var iframe = document.getElementById('{namespace}-iframe');
                        if (iframe) iframe.src = '';
                    }}
                }}

                window.{api_name} = {{
                    show: showPanel,
                    hide: hidePanel
                }};
                {event_listener}
            }})();"""
