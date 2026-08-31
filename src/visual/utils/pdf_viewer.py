# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from config.theme import colour
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Shared PDF viewer panel factory.

Generates JavaScript for an inline overlay panel that displays
base64-encoded PDFs in an iframe.  Used by PropertyPDFPanel,
GaugePDFPanel, and the insurance claim-report viewer.

The JS body lives in ``src/static/js/pdf_viewer.js`` (plus the optional
custom-event listener in ``pdf_viewer_event.js``); the parameters are spliced
in here via ``__SENTINEL__`` placeholders.
"""


def pdf_viewer_js(namespace: str,
                  panel_width: str = "850px",
                  panel_height: str = "90vh",
                  default_title: str = "Report",
                  btn_color: str = colour('bootstrap-green'),
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

    # Lazy import: pdf_viewer lives in visual.utils, but the js_static helper
    # is inside the visual.interactivity package whose __init__ imports the PDF
    # panels (which import this module). Importing at call time avoids that
    # module-load cycle.
    from visual.interactivity._jsbundle import js_static

    event_listener = ""
    if event_name:
        event_listener = (
            js_static('pdf_viewer_event.js')
            .replace('__EVENT_NAME__', event_name)
            .replace('__EVENT_ID_KEY__', event_id_key)
        )

    return (
        js_static('pdf_viewer.js')
        .replace('__PANEL_W__', panel_width)
        .replace('__PANEL_H__', panel_height)
        .replace('__DEFAULT_TITLE__', default_title)
        .replace('__BTN_COLOR__', btn_color)
        .replace('__DISPLAY_LABEL__', display_name_js or 'entityId')
        .replace('__API_NAME__', api_name)
        .replace('__EVENT_LISTENER__', event_listener)
        .replace('__NS__', namespace)
    )
