# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""PRS Blueprint and route handlers."""

import json
import logging
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from flask import Blueprint, jsonify, request, send_file

logger = logging.getLogger(__name__)

from config import config
from models.schedule.maturity import compute_maturity_date
from port.cdm.prs import PhysicalRiskSwapCDM
from .pdf import _generate_trade_pdf

prs_bp = Blueprint("prs", __name__)


def _get_prs_output_dir() -> Path:
    """Get PRS output directory."""
    prs_dir = config.get_reports_dir("prs")
    prs_dir.mkdir(parents=True, exist_ok=True)
    return prs_dir


@prs_bp.route("/prs/commit", methods=["POST"])
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
        gauge_id = data.get("gauge_id", "")
        trigger = data.get("trigger", "warning")
        notional = float(data.get("notional", 10_000_000))
        spread_bps = float(data.get("spread_bps", 100))

        cdm_record = {
            "PhysicalSwap": {
                "Header": {
                    "SwapID": swap_id,
                    "CatchmentID": config.catchment_id,
                    "TradeType": "PRS",
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
                    "Currency": "GBP",
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
                    "Currency": "GBP",
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
                },
            }
        }

        # Validate
        cdm = PhysicalRiskSwapCDM()
        errors = cdm.validate(cdm_record)
        if errors:
            return jsonify({"status": "error", "message": "Validation failed", "errors": errors}), 400

        # Save trade JSON
        prs_dir = _get_prs_output_dir()
        json_path = prs_dir / f"{swap_id}.json"
        with open(json_path, 'w') as f:
            json.dump(cdm_record, f, indent=2)

        # Handle close-out: mark original trade as closed
        close_out_of = data.get("close_out_of")
        if close_out_of:
            from models.trading.pnl_engine import PnLEngine
            trading_dir = config.get_trading_dir()
            pnl_eng = PnLEngine(trading_dir, prs_dir)
            pnl_eng.close_trade(close_out_of, spread_bps)
            cdm_record["PhysicalSwap"]["Header"]["CloseOutOf"] = close_out_of
            # Re-save with close-out reference
            with open(json_path, 'w') as f:
                json.dump(cdm_record, f, indent=2)

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
        return jsonify({"status": "error", "message": str(e)}), 500


@prs_bp.route("/prs/trades", methods=["GET"])
def list_prs_trades():
    """List all committed PRS trades."""
    try:
        prs_dir = _get_prs_output_dir()
        trades = []
        for f in sorted(prs_dir.glob("PRS-*.json")):
            with open(f) as fh:
                trade = json.load(fh)
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
        return jsonify({"status": "error", "message": str(e)}), 500


@prs_bp.route("/prs/trades/<swap_id>/pdf", methods=["GET"])
def get_trade_pdf(swap_id: str):
    """Download PDF for a specific trade."""
    prs_dir = _get_prs_output_dir()
    pdf_path = prs_dir / f"{swap_id}.pdf"
    if pdf_path.exists():
        return send_file(str(pdf_path), mimetype='application/pdf')
    return jsonify({"status": "error", "message": "PDF not found"}), 404
