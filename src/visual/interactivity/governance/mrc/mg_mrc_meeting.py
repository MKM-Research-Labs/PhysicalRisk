# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

#
# This software is provided under license by MKM Research Labs.
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

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
