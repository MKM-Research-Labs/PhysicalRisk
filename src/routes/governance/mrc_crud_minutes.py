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

"""MRC meeting minutes CRUD routes."""

from flask import jsonify, request

from . import governance_bp
from ._helpers import _find_meeting, _save_and_respond


@governance_bp.route("/governance/mrc/meetings/<meeting_id>/minutes/update", methods=["POST"])
def update_minutes(meeting_id):
    """Update meeting minutes (markdown text)."""
    meetings, meeting, err = _find_meeting(meeting_id)
    if err:
        return err, 404

    data = request.get_json(silent=True) or {}
    meeting["minutes"] = data.get("minutes", "")

    return _save_and_respond(meetings, meeting)


@governance_bp.route("/governance/mrc/meetings/<meeting_id>/minutes-items", methods=["POST"])
def add_minute_item(meeting_id):
    """Add a minutes item to a meeting."""
    meetings, meeting, err = _find_meeting(meeting_id)
    if err:
        return err, 404

    data = request.get_json(silent=True) or {}
    minutes = meeting.get("minutes", [])
    if isinstance(minutes, str):
        minutes = []
    meeting["minutes"] = minutes

    item_num = len(minutes) + 1
    minutes.append({
        "item": item_num,
        "title": data.get("title", ""),
        "text": data.get("text", ""),
        "presenter": data.get("presenter", ""),
    })

    return _save_and_respond(meetings, meeting)


@governance_bp.route("/governance/mrc/meetings/<meeting_id>/minutes-items/<int:item_num>/update", methods=["POST"])
def update_minute_item(meeting_id, item_num):
    """Update a minutes item."""
    meetings, meeting, err = _find_meeting(meeting_id)
    if err:
        return err, 404

    minutes = meeting.get("minutes", [])
    if isinstance(minutes, str):
        return jsonify({"status": "error", "message": "Minutes are in legacy format"}), 400

    item = next((m for m in minutes if m.get("item") == item_num), None)
    if not item:
        return jsonify({"status": "error", "message": f"Minutes item {item_num} not found"}), 404

    data = request.get_json(silent=True) or {}
    for field in ["title", "text", "presenter"]:
        if field in data:
            item[field] = data[field]

    return _save_and_respond(meetings, meeting)


@governance_bp.route("/governance/mrc/meetings/<meeting_id>/minutes-items/<int:item_num>/delete", methods=["POST"])
def delete_minute_item(meeting_id, item_num):
    """Delete a minutes item and renumber remaining items."""
    meetings, meeting, err = _find_meeting(meeting_id)
    if err:
        return err, 404

    minutes = meeting.get("minutes", [])
    if isinstance(minutes, str):
        return jsonify({"status": "error", "message": "Minutes are in legacy format"}), 400

    meeting["minutes"] = [m for m in minutes if m.get("item") != item_num]
    for i, m in enumerate(meeting["minutes"], 1):
        m["item"] = i

    return _save_and_respond(meetings, meeting)
