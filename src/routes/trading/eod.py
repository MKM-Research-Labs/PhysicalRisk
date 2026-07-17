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

"""EOD submission, history, and PDF report endpoints."""

import base64
import logging

from flask import jsonify, request

from config import config
from config.auth import FUNC_TRADE_PRS, WRITE

from .._rbac import require
from . import trading_bp
from ._helpers import _get_engines, _load_open_trades

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# EOD
# ------------------------------------------------------------------

@trading_bp.route("/trading/eod", methods=["POST"])
@require(FUNC_TRADE_PRS, WRITE)
def submit_eod():
    """Submit EOD snapshot and generate PDF report."""
    try:
        data = request.get_json() or {}
        eod_date = data.get('date',
                            __import__('datetime').date.today().isoformat())

        market_mgr, delta_eng, pnl_eng = _get_engines()
        trades = _load_open_trades()
        state = market_mgr.load()
        enriched = delta_eng.revalue_all(trades, state)

        # Generate snapshot
        snapshot = pnl_eng.generate_eod_snapshot(
            enriched, state, eod_date)

        # Generate PDF
        pdf_base64 = ''
        try:
            from reports.trading.eod_generator import EODReportGenerator

            generator = EODReportGenerator(config.get_eod_dir())
            pnl_series = pnl_eng.get_pnl_series()
            pdf_path = generator.generate_report(snapshot, pnl_series)

            if pdf_path and pdf_path.exists():
                with open(pdf_path, 'rb') as pf:
                    pdf_base64 = base64.b64encode(pf.read()).decode('utf-8')
                snapshot['pdf_path'] = str(pdf_path)

        except ImportError:
            logger.warning("EOD PDF generator not available yet")
        except Exception as pdf_err:
            logger.error("EOD PDF error: %s", pdf_err, exc_info=True)

        return jsonify({
            'status': 'success',
            'eod_id': snapshot['eod_id'],
            'date': eod_date,
            'summary': snapshot['portfolio_summary'],
            'pdf_base64': pdf_base64,
            'message': f"EOD {eod_date} submitted successfully",
        })

    except Exception as e:
        logger.error("EOD submit error: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error"}), 500


@trading_bp.route("/trading/eod/history", methods=["GET"])
def get_eod_history():
    """List all EOD snapshots."""
    try:
        _, _, pnl_eng = _get_engines()
        history = pnl_eng.get_eod_history()

        return jsonify({
            'status': 'success',
            'history': history,
            'count': len(history),
        })

    except Exception as e:
        logger.error("EOD history error: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error"}), 500


@trading_bp.route("/trading/eod/<eod_date>/pdf", methods=["GET"])
def get_eod_pdf(eod_date: str):
    """Download EOD PDF report."""
    try:
        eod_dir = config.get_eod_dir()
        pdf_path = eod_dir / f"EOD-{eod_date.replace('-', '')}.pdf"

        if pdf_path.exists():
            from flask import send_file
            return send_file(str(pdf_path), mimetype='application/pdf')

        return jsonify({"status": "error",
                        "message": "PDF not found"}), 404

    except Exception as e:
        logger.error("EOD PDF error: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error"}), 500
