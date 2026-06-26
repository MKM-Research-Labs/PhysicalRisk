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
Model usage audit trail.

Lightweight audit logging for model invocations. Records model ID, timestamp,
parameters, and context to support Model Risk Governance requirements.

Usage:
    from models.audit import log_model_usage

    log_model_usage("MKM-GH-001", "gev_fit",
                    parameters={"gauge_id": "GAUGE-001", "n_events": 42},
                    context="Hazard curve construction")
"""

import json
import logging
import os
from datetime import datetime
from threading import Lock

logger = logging.getLogger(__name__)

_audit_lock = Lock()

# Model ID mapping for automatic identification
MODEL_ID_MAP = {
    "intensity": "MKM-SI-001",
    "distribution": "MKM-SI-001",
    "storm_intensity": "MKM-SI-001",
    "forward_model": "MKM-SG-001",
    "storm_gauge": "MKM-SG-001",
    "stormgauge": "MKM-SG-001",
    "gev": "MKM-GH-001",
    "hazard": "MKM-GH-001",
    "gev_fit": "MKM-GH-001",
    "exceedance": "MKM-GH-001",
    "prs": "MKM-PR-001",
    "prs_analytical": "MKM-PR-001",
    "prs_pricing": "MKM-PR-001",
    "depth_damage": "MKM-DD-001",
    "scalar_depth_damage": "MKM-DD-001",
    "spatial": "MKM-SP-001",
    "idw": "MKM-SP-001",
    "idw_interpolate": "MKM-SP-001",
    "property_value": "MKM-PV-001",
    "valuation": "MKM-PV-001",
    "insurance": "MKM-IP-001",
    "insurance_premium": "MKM-IP-001",
    "mortgage": "MKM-MP-001",
    "mortgage_pricer": "MKM-MP-001",
    "amortization": "MKM-MP-001",
    "risk_analytics": "MKM-RA-001",
    "var": "MKM-RA-001",
    "monte_carlo": "MKM-RA-001",
    "storm_sequence": "MKM-SS-001",
    "storm_multi": "MKM-SS-001",
    "sequence_generator": "MKM-SS-001",
    "stressm": "MKM-SS-001",
}


def _get_audit_path():
    """Get audit log file path.

    The governance audit log is version-controlled repo content under
    docs/models/governance_data/, not shared data/.
    """
    from config import config
    return os.path.join(
        str(config.get_governance_data_dir()), "model_audit_log.json"
    )


def resolve_model_id(model_ref):
    """Resolve a model reference to a formal model ID."""
    if model_ref.startswith("MKM-"):
        return model_ref
    return MODEL_ID_MAP.get(model_ref.lower(), model_ref)


def log_model_usage(model_ref, action, parameters=None, context="",
                     user="system", source="platform"):
    """
    Log a model usage event to the audit trail.

    Args:
        model_ref: Model ID (e.g. "MKM-GH-001") or shorthand (e.g. "gev")
        action: What the model did (e.g. "gev_fit", "exceedance_calc")
        parameters: Dict of key parameters used
        context: Free-text context description
        user: User or system identifier
        source: Source of the invocation (platform, api, test, etc.)
    """
    model_id = resolve_model_id(model_ref)

    entry = {
        "timestamp": datetime.now().isoformat(),
        "model_id": model_id,
        "event_type": "usage",
        "user": user,
        "action": action,
        "parameters": _sanitise_params(parameters or {}),
        "context": context,
        "source": source,
    }

    try:
        audit_path = _get_audit_path()

        with _audit_lock:
            # Load existing
            entries = []
            if os.path.exists(audit_path):
                try:
                    with open(audit_path, "r") as f:
                        entries = json.load(f)
                except (json.JSONDecodeError, OSError):
                    entries = []

            entries.append(entry)

            # Keep last 10000 entries
            if len(entries) > 10000:
                entries = entries[-10000:]

            # Ensure directory exists
            os.makedirs(os.path.dirname(audit_path), exist_ok=True)

            with open(audit_path, "w") as f:
                json.dump(entries, f, indent=2)

    except Exception as e:
        # Never let audit logging break the model
        logger.warning("Failed to log model audit entry: %s", e)


def _sanitise_params(params):
    """Convert parameters to JSON-safe format, truncating large values."""
    safe = {}
    for k, v in params.items():
        if isinstance(v, (int, float, str, bool, type(None))):
            safe[k] = v
        elif isinstance(v, (list, tuple)):
            if len(v) > 10:
                safe[k] = f"[{len(v)} items]"
            else:
                safe[k] = [str(x) for x in v]
        else:
            safe[k] = str(v)[:100]
    return safe
