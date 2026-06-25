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

"""PRS Blueprint and route handlers."""

import logging
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from flask import Blueprint, jsonify, request, send_file

logger = logging.getLogger(__name__)

import database
from config import config
from config.auth import CREATE, FUNC_TRADE_PRS
from models.schedule.maturity import compute_maturity_date
from port.cdm.prs import PhysicalRiskSwapCDM

from .._rbac import require
from .pdf import _generate_trade_pdf

prs_bp = Blueprint("prs", __name__)


def _get_prs_output_dir() -> Path:
    """Get PRS output directory."""
    prs_dir = config.get_reports_dir("prs")
    prs_dir.mkdir(parents=True, exist_ok=True)
    return prs_dir


@prs_bp.route("/prs/commit", methods=["POST"])
@require(FUNC_TRADE_PRS, CREATE)
def commit_prs_trade():
    """
    Commit a PRS trade.

    Expects JSON body with pricing parameters:
        gauge_id, gauge_name, counterparty_id, counterparty_name,
        trigger, notional, tenor, spread_bps, rf_rate, recovery,
        fair_spread_bps, npv, premium_leg_pv, protection_leg_pv,
        risky_annuity, cashflows (list)
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No JSON body"}), 400

        # Generate trade ID
        swap_id = f"PRS-{uuid.uuid4().hex[:8].upper()}"
        trade_date = datetime.now()
        start_date = trade_date + timedelta(days=2)  # T+2
        tenor = int(data.get("tenor", 5))

        # Use explicit maturity_date if provided (e.g. close-out matching original),
        # otherwise compute from the semi-annual roll convention
        maturity_str = data.get("maturity_date")
        if maturity_str:
            end_date = datetime.strptime(maturity_str, "%Y-%m-%d")
        else:
            end_date = compute_maturity_date(tenor, trade_date.date())

        # Build CDM record
        gauge_id = data.get("gauge_id", "").strip()
        if not gauge_id:
            return jsonify({"status": "error", "message": "gauge_id is required"}), 400

        property_id = data.get("property_id", "")
        trigger = data.get("trigger", "warning")
        notional = float(data.get("notional", 10_000_000))
        spread_bps = float(data.get("spread_bps", 100))

        # Determine trade type: PropertyPRS when committed from property panel
        trade_type = "PropertyPRS" if property_id else "PRS"

        cdm_record = {
            "PhysicalSwap": {
                "Header": {
                    "SwapID": swap_id,
                    "CatchmentID": config.catchment_id,
                    "TradeType": trade_type,
                    "CounterParty": data.get("counterparty_id", ""),
                    "CounterPartyName": data.get("counterparty_name", ""),
                    "PartyId": "MKM-RESEARCH-001",
                    "ValuationDate": trade_date.strftime("%Y-%m-%d"),
                    "ProtectionStart": start_date.strftime("%Y-%m-%d"),
                    "TradeStatus": "Committed",
                },
                "LegData": {
                    "LegType": "Fixed",
                    "Payer": data.get("payer", True),
                    "Currency": config.CURRENCY,
                    "Notional": notional,
                    "DayCounter": "ACT/360",
                    "FixedLegRate": spread_bps / 10000,
                },
                "ScheduleData": {
                    "StartDate": start_date.strftime("%Y-%m-%d"),
                    "EndDate": end_date.strftime("%Y-%m-%d"),
                    "Tenor": "6M",
                    "Calendar": "London",
                },
                "GaugeSet": {
                    "GaugeSetID": f"GSET-{gauge_id}",
                    "CatchmentID": config.catchment_id,
                    "GaugeCount": 1,
                    "GaugeBasket": [
                        {
                            "GaugeID": gauge_id,
                            "GaugeName": data.get("gauge_name", ""),
                            "Weight": 1.0,
                            "TriggerLevel": trigger,
                        }
                    ],
                },
                "Triggers": {
                    "TriggerType": "Any",
                    "TriggerThreshold": 1,
                },
                "Payouts": {
                    "Currency": config.CURRENCY,
                    "MaxPayout": notional,
                },
                "Pricing": {
                    "SpreadBps": spread_bps,
                    "FairSpreadBps": float(data.get("fair_spread_bps", 0)),
                    "NPV": float(data.get("npv", 0)),
                    "PremiumLegPV": float(data.get("premium_leg_pv", 0)),
                    "ProtectionLegPV": float(data.get("protection_leg_pv", 0)),
                    "RiskyAnnuity": float(data.get("risky_annuity", 0)),
                    "YieldCurve": data.get("yield_curve", {}),
                    "Recovery": float(data.get("recovery", 0)),
                    "TriggerLevel": trigger,
                    "EAFloodZone": data.get("ea_flood_zone", ""),
                    "EAFloodZoneActual": data.get("ea_flood_zone_actual", ""),
                    "TerrainDeltaBps": float(data.get("terrain_delta_bps", 0)),
                },
            }
        }

        # Add PropertySet when committed from property panel
        if property_id:
            prop_set = {
                "PropertyID": property_id,
                "EAFloodZone": data.get("ea_flood_zone", ""),
            }
            # Look up property details from property.json
            try:
                prop_data = database.get_property_portfolio(config.catchment_id)
                if prop_data:
                    for p in prop_data.get("properties", []):
                        hdr = p.get("PropertyHeader", {}).get("Header", {})
                        if hdr.get("PropertyID") == property_id:
                            loc = p.get("PropertyHeader", {}).get("Location", {})
                            val = p.get("PropertyHeader", {}).get("Valuation", {})
                            prop_set["PropertyAddress"] = (
                                f"{loc.get('BuildingNumber', '')} {loc.get('StreetName', '')}".strip()
                            )
                            prop_set["Postcode"] = loc.get("Postcode", "")
                            prop_set["LocalAuthority"] = loc.get("LocalAuthority", "")
                            prop_set["PropertyValue"] = val.get("PropertyValue", 0)
                            prop_set["Latitude"] = loc.get("LatitudeDegrees", 0)
                            prop_set["Longitude"] = loc.get("LongitudeDegrees", 0)
                            ref_gauges = p.get("PropertyHeader", {}).get("ReferenceGauges", [])
                            if ref_gauges:
                                prop_set["ReferenceGauge"] = ref_gauges[0]
                            break
            except Exception as e:
                logger.warning("Could not look up property %s: %s", property_id, e)

            cdm_record["PhysicalSwap"]["PropertySet"] = prop_set

        # Validate
        cdm = PhysicalRiskSwapCDM()
        errors = cdm.validate(cdm_record)
        if errors:
            return jsonify({"status": "error", "message": "Validation failed", "errors": errors}), 400

        # Save trade JSON
        prs_dir = _get_prs_output_dir()
        json_path = prs_dir / f"{swap_id}.json"
        database.save_prs_trade(config.catchment_id, swap_id, cdm_record)

        # Handle close-out: mark original trade as closed
        close_out_of = data.get("close_out_of")
        if close_out_of:
            from models.trading.pnl_engine import PnLEngine
            pnl_eng = PnLEngine()
            pnl_eng.close_trade(close_out_of, spread_bps)
            cdm_record["PhysicalSwap"]["Header"]["CloseOutOf"] = close_out_of
            # Re-save with close-out reference
            database.save_prs_trade(config.catchment_id, swap_id, cdm_record)

        # Generate PDF confirmation
        pdf_path = _generate_trade_pdf(cdm_record, data.get("cashflows", []), prs_dir)

        # Read PDF as base64 for inline display
        import base64
        pdf_base64 = ""
        if pdf_path.exists():
            with open(pdf_path, "rb") as pf:
                pdf_base64 = base64.b64encode(pf.read()).decode("utf-8")

        return jsonify({
            "status": "success",
            "swap_id": swap_id,
            "json_path": str(json_path),
            "pdf_path": str(pdf_path),
            "pdf_base64": pdf_base64,
            "message": f"Trade {swap_id} committed successfully",
        })

    except Exception as e:
        logger.error(f"Error committing PRS trade: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error"}), 500


@prs_bp.route("/prs/trades", methods=["GET"])
def list_prs_trades():
    """List all committed PRS trades."""
    try:
        trades = []
        for swap_id in database.iter_prs_trade_ids(config.catchment_id):
            if not swap_id.startswith("PRS-"):
                continue
            trade = database.get_prs_trade(config.catchment_id, swap_id)
            if trade is None:
                continue
            header = trade.get("PhysicalSwap", {}).get("Header", {})
            pricing = trade.get("PhysicalSwap", {}).get("Pricing", {})
            leg = trade.get("PhysicalSwap", {}).get("LegData", {})
            trades.append({
                "swap_id": header.get("SwapID"),
                "counterparty": header.get("CounterPartyName", header.get("CounterParty")),
                "trade_date": header.get("ValuationDate"),
                "notional": leg.get("Notional"),
                "spread_bps": pricing.get("SpreadBps"),
                "fair_spread_bps": pricing.get("FairSpreadBps"),
                "npv": pricing.get("NPV"),
                "trigger": pricing.get("TriggerLevel"),
            })

        return jsonify({"status": "success", "trades": trades, "count": len(trades)})
    except Exception as e:
        return jsonify({"status": "error", "message": "Internal server error"}), 500


@prs_bp.route("/prs/trades/<swap_id>/pdf", methods=["GET"])
def get_trade_pdf(swap_id: str):
    """Download PDF for a specific trade."""
    prs_dir = _get_prs_output_dir()
    pdf_path = prs_dir / f"{swap_id}.pdf"
    if pdf_path.exists():
        return send_file(str(pdf_path), mimetype='application/pdf')
    return jsonify({"status": "error", "message": "PDF not found"}), 404
