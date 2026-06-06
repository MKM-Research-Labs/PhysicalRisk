# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Documentation tab — PDF viewer with sub-tabs for core docs, test results, analysis."""

from visual.interactivity._jsbundle import js_static


def get_docs_js():
    """Return JS for renderDocsTab, _docsPdfSection, switchDocsSection."""
    return js_static('governance/models/mg_detail_tabs/docs.js')
