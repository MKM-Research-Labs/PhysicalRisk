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

"""
Model Governance MRC meeting detail — view, tabs, CRUD, documents, participants, PDF.

Sub-modules:
- mg_mrc_agenda: Agenda and Minutes tabs with CRUD
- mg_mrc_items: Participants, Models, Decisions, and Actions tabs
- mg_mrc_docs: Documents tab and New Meeting form
"""

from visual.interactivity._jsbundle import js_static

from . import mg_mrc_agenda, mg_mrc_items, mg_mrc_docs


def get_js():
    """Return JS fragment for MRC meeting detail and CRUD operations."""
    return js_static('governance/mrc/mg_mrc_meeting.js') + mg_mrc_agenda.get_js() + mg_mrc_items.get_js() + mg_mrc_docs.get_js()
