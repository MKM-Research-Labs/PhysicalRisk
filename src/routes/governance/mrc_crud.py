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

"""MRC meeting item-level CRUD: agenda, minutes, decisions, actions, participants."""

from datetime import datetime

from flask import jsonify, request

from . import governance_bp
from ._helpers import _find_meeting, _save_and_respond

# ── Agenda CRUD ──

@governance_bp.route("/governance/mrc/meetings/<meeting_id>/agenda", methods=["POST"])
def add_agenda_item(meeting_id):
    """Add an agenda item to a meeting."""
    meetings, meeting, err = _find_meeting(meeting_id)
    if err:
        return err, 404

    data = request.get_json(silent=True) or {}
    agenda = meeting.setdefault("agenda", [])

    item_num = len(agenda) + 1
    agenda.append({
        "item": item_num,
        "title": data.get("title", ""),
        "description": data.get("description", ""),
        "presenter": data.get("presenter", ""),
        "duration": data.get("duration", ""),
        "status": data.get("status", "Pending"),
    })

    return _save_and_respond(meetings, meeting)


@governance_bp.route("/governance/mrc/meetings/<meeting_id>/agenda/<int:item_num>/update", methods=["POST"])
def update_agenda_item(meeting_id, item_num):
    """Update an agenda item."""
    meetings, meeting, err = _find_meeting(meeting_id)
    if err:
        return err, 404

    agenda = meeting.get("agenda", [])
    item = next((a for a in agenda if a.get("item") == item_num), None)
    if not item:
        return jsonify({"status": "error", "message": f"Agenda item {item_num} not found"}), 404

    data = request.get_json(silent=True) or {}
    for field in ["title", "description", "presenter", "duration", "status"]:
        if field in data:
            item[field] = data[field]

    return _save_and_respond(meetings, meeting)


@governance_bp.route("/governance/mrc/meetings/<meeting_id>/agenda/<int:item_num>/delete", methods=["POST"])
def delete_agenda_item(meeting_id, item_num):
    """Delete an agenda item and renumber remaining items."""
    meetings, meeting, err = _find_meeting(meeting_id)
    if err:
        return err, 404

    agenda = meeting.get("agenda", [])
    meeting["agenda"] = [a for a in agenda if a.get("item") != item_num]
    # Renumber
    for i, a in enumerate(meeting["agenda"], 1):
        a["item"] = i

    return _save_and_respond(meetings, meeting)


# ── Minutes CRUD ──

@governance_bp.route("/governance/mrc/meetings/<meeting_id>/minutes/update", methods=["POST"])
def update_minutes(meeting_id):
    """Update meeting minutes (markdown text)."""
    meetings, meeting, err = _find_meeting(meeting_id)
    if err:
        return err, 404

    data = request.get_json(silent=True) or {}
    meeting["minutes"] = data.get("minutes", "")

    return _save_and_respond(meetings, meeting)


# ── Decisions CRUD ──

@governance_bp.route("/governance/mrc/meetings/<meeting_id>/decisions", methods=["POST"])
def add_decision(meeting_id):
    """Add a decision to a meeting."""
    meetings, meeting, err = _find_meeting(meeting_id)
    if err:
        return err, 404

    data = request.get_json(silent=True) or {}
    decisions = meeting.setdefault("decisions", [])

    # Auto-generate ID: D-NNN
    existing_nums = []
    for d in decisions:
        try:
            existing_nums.append(int(d["id"].split("-")[1]))
        except (IndexError, ValueError):
            pass
    next_num = max(existing_nums, default=0) + 1

    decisions.append({
        "id": f"D-{next_num:03d}",
        "description": data.get("description", ""),
        "date": data.get("date", meeting.get("date", datetime.now().strftime("%Y-%m-%d"))),
    })

    return _save_and_respond(meetings, meeting)


@governance_bp.route("/governance/mrc/meetings/<meeting_id>/decisions/<decision_id>/update", methods=["POST"])
def update_decision(meeting_id, decision_id):
    """Update a decision."""
    meetings, meeting, err = _find_meeting(meeting_id)
    if err:
        return err, 404

    decisions = meeting.get("decisions", [])
    decision = next((d for d in decisions if d["id"] == decision_id), None)
    if not decision:
        return jsonify({"status": "error", "message": f"Decision {decision_id} not found"}), 404

    data = request.get_json(silent=True) or {}
    for field in ["description", "date"]:
        if field in data:
            decision[field] = data[field]

    return _save_and_respond(meetings, meeting)


@governance_bp.route("/governance/mrc/meetings/<meeting_id>/decisions/<decision_id>/delete", methods=["POST"])
def delete_decision(meeting_id, decision_id):
    """Delete a decision."""
    meetings, meeting, err = _find_meeting(meeting_id)
    if err:
        return err, 404

    meeting["decisions"] = [d for d in meeting.get("decisions", []) if d["id"] != decision_id]

    return _save_and_respond(meetings, meeting)


# ── Actions CRUD ──

@governance_bp.route("/governance/mrc/meetings/<meeting_id>/actions", methods=["POST"])
def add_action(meeting_id):
    """Add an action item to a meeting."""
    meetings, meeting, err = _find_meeting(meeting_id)
    if err:
        return err, 404

    data = request.get_json(silent=True) or {}
    actions = meeting.setdefault("actions", [])

    # Auto-generate ID: A-NNN
    existing_nums = []
    for a in actions:
        try:
            existing_nums.append(int(a["id"].split("-")[1]))
        except (IndexError, ValueError):
            pass
    next_num = max(existing_nums, default=0) + 1

    actions.append({
        "id": f"A-{next_num:03d}",
        "description": data.get("description", ""),
        "owner": data.get("owner", ""),
        "target_date": data.get("target_date", ""),
        "status": data.get("status", "Open"),
    })

    return _save_and_respond(meetings, meeting)


@governance_bp.route("/governance/mrc/meetings/<meeting_id>/actions/<action_id>/update", methods=["POST"])
def update_action(meeting_id, action_id):
    """Update an action item (including status toggle)."""
    meetings, meeting, err = _find_meeting(meeting_id)
    if err:
        return err, 404

    actions = meeting.get("actions", [])
    action = next((a for a in actions if a["id"] == action_id), None)
    if not action:
        return jsonify({"status": "error", "message": f"Action {action_id} not found"}), 404

    data = request.get_json(silent=True) or {}
    for field in ["description", "owner", "target_date", "status"]:
        if field in data:
            action[field] = data[field]

    return _save_and_respond(meetings, meeting)


@governance_bp.route("/governance/mrc/meetings/<meeting_id>/actions/<action_id>/delete", methods=["POST"])
def delete_action(meeting_id, action_id):
    """Delete an action item."""
    meetings, meeting, err = _find_meeting(meeting_id)
    if err:
        return err, 404

    meeting["actions"] = [a for a in meeting.get("actions", []) if a["id"] != action_id]

    return _save_and_respond(meetings, meeting)


# ── Participants CRUD ──

@governance_bp.route("/governance/mrc/meetings/<meeting_id>/participants", methods=["POST"])
def add_participant(meeting_id):
    """Add a participant to a meeting."""
    meetings, meeting, err = _find_meeting(meeting_id)
    if err:
        return err, 404

    data = request.get_json(silent=True) or {}
    participants = meeting.setdefault("participants", [])

    # Auto-generate ID: P-NNN
    existing_nums = []
    for p in participants:
        try:
            existing_nums.append(int(p["id"].split("-")[1]))
        except (IndexError, ValueError):
            pass
    next_num = max(existing_nums, default=0) + 1

    participants.append({
        "id": f"P-{next_num:03d}",
        "name": data.get("name", ""),
        "role": data.get("role", ""),
        "organisation": data.get("organisation", ""),
        "status": data.get("status", "Invited"),
    })

    return _save_and_respond(meetings, meeting)


@governance_bp.route("/governance/mrc/meetings/<meeting_id>/participants/<participant_id>/update", methods=["POST"])
def update_participant(meeting_id, participant_id):
    """Update a participant."""
    meetings, meeting, err = _find_meeting(meeting_id)
    if err:
        return err, 404

    participants = meeting.get("participants", [])
    participant = next((p for p in participants if p["id"] == participant_id), None)
    if not participant:
        return jsonify({"status": "error", "message": f"Participant {participant_id} not found"}), 404

    data = request.get_json(silent=True) or {}
    for field in ["name", "role", "organisation", "status"]:
        if field in data:
            participant[field] = data[field]

    return _save_and_respond(meetings, meeting)


@governance_bp.route("/governance/mrc/meetings/<meeting_id>/participants/<participant_id>/delete", methods=["POST"])
def delete_participant(meeting_id, participant_id):
    """Delete a participant."""
    meetings, meeting, err = _find_meeting(meeting_id)
    if err:
        return err, 404

    meeting["participants"] = [p for p in meeting.get("participants", []) if p["id"] != participant_id]

    return _save_and_respond(meetings, meeting)


# ── Minutes Items CRUD ──

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
