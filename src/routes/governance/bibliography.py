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

"""Bibliography CRUD routes."""

import uuid

from flask import jsonify, request

from . import governance_bp
from ._helpers import _load_bibliography, _save_bibliography


@governance_bp.route("/governance/bibliography", methods=["GET"])
def get_bibliography():
    """List all bibliography references."""
    data = _load_bibliography()
    return jsonify({
        "status": "success",
        "references": data.get("references", []),
        "categories": data.get("categories", []),
    })


@governance_bp.route("/governance/bibliography", methods=["POST"])
def add_bibliography_ref():
    """Add a new bibliography reference."""
    body = request.get_json(silent=True) or {}
    data = _load_bibliography()

    ref = {
        "id": str(uuid.uuid4())[:8],
        "author": body.get("author", ""),
        "year": body.get("year", 0),
        "title": body.get("title", ""),
        "journal": body.get("journal", ""),
        "doi": body.get("doi", ""),
        "url": body.get("url", ""),
        "category": body.get("category", ""),
        "notes": body.get("notes", ""),
    }

    data["references"].append(ref)

    # Auto-update categories list
    cat = ref["category"]
    if cat and cat not in data["categories"]:
        data["categories"].append(cat)
        data["categories"].sort()

    if not _save_bibliography(data):
        return jsonify({"status": "error", "message": "Failed to save"}), 500

    return jsonify({"status": "success", "reference": ref})


@governance_bp.route("/governance/bibliography/<ref_id>", methods=["PUT"])
def update_bibliography_ref(ref_id):
    """Update a bibliography reference."""
    body = request.get_json(silent=True) or {}
    data = _load_bibliography()

    ref = next((r for r in data["references"] if r["id"] == ref_id), None)
    if not ref:
        return jsonify({"status": "error", "message": "Reference not found"}), 404

    for field in ["author", "year", "title", "journal", "doi", "url", "category", "notes"]:
        if field in body:
            ref[field] = body[field]

    # Auto-update categories
    cat = ref.get("category", "")
    if cat and cat not in data["categories"]:
        data["categories"].append(cat)
        data["categories"].sort()

    if not _save_bibliography(data):
        return jsonify({"status": "error", "message": "Failed to save"}), 500

    return jsonify({"status": "success", "reference": ref})


@governance_bp.route("/governance/bibliography/<ref_id>", methods=["DELETE"])
def delete_bibliography_ref(ref_id):
    """Delete a bibliography reference."""
    data = _load_bibliography()
    data["references"] = [r for r in data["references"] if r["id"] != ref_id]

    if not _save_bibliography(data):
        return jsonify({"status": "error", "message": "Failed to save"}), 500

    return jsonify({"status": "success"})
