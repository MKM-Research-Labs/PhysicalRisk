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
