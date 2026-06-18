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

"""
CDM-to-OED Location exporter.

Converts a list of property CDM records (as produced by property.json) into an
OED v5.0.0 Location CSV file that can be fed directly into OASIS LMF.

Public API:
    cdm_to_oed_rows(properties)  — list[dict], one per property
    export_oed_csv(properties, path)  — write Location CSV to file

OED spec reference: OasisLMF/ODS_OpenExposureData v5.0.0 (2024-11).
Field mapping document: docs/oasis/cdm_oed_mapping.md (forthcoming).
"""

from ._core import _OED_FIELDS, cdm_to_oed_row, cdm_to_oed_rows, export_oed_csv

__all__ = [
    "_OED_FIELDS",
    "cdm_to_oed_row",
    "cdm_to_oed_rows",
    "export_oed_csv",
]
