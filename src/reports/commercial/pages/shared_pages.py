# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Thin page-class wrappers around ``reports.asset.render_*``.

The :class:`BaseReportGenerator` orchestrator calls
``self.pages[name].generate_elements(**page_kwargs)`` for each page, so
each shared section needs to be a class with a ``generate_elements``
method even though all the rendering logic lives as a function in
``reports.asset.*``. These wrappers do nothing except unwrap the right
slice of the CommercialAsset dict and forward to the shared renderer.

Phase B will refactor the residential property pages to use the same
pattern, eliminating ~300 lines of duplicated rendering code from
``src/reports/property/property_page_*.py``.
"""

from typing import Any, Dict, List

from reports.asset import (
    render_construction,
    render_energy,
    render_header,
    render_history,
    render_location,
    render_protection,
    render_risk_assessment,
    render_transactions,
    render_valuation,
)

from ..base import CommercialBasePage


def _asset(commercial_data: Dict[str, Any]) -> Dict[str, Any]:
    """Unwrap the CommercialAsset root of a commercial.json record."""
    return commercial_data.get("CommercialAsset", {}) or {}


class HeaderPage(CommercialBasePage):
    def generate_elements(self, commercial_data: Dict[str, Any], **kwargs) -> List:
        return render_header(_asset(commercial_data).get("Header", {}), self)


class LocationPage(CommercialBasePage):
    def generate_elements(self, commercial_data: Dict[str, Any], **kwargs) -> List:
        return render_location(_asset(commercial_data).get("Location", {}), self)


class ValuationPage(CommercialBasePage):
    def generate_elements(self, commercial_data: Dict[str, Any], **kwargs) -> List:
        # USD for halong, GBP for thames — caller selects via currency_symbol.
        from config import config
        symbol = self._currency_symbol_for(config.catchment_id)
        return render_valuation(_asset(commercial_data).get("Valuation", {}),
                                self, currency_symbol=symbol)

    @staticmethod
    def _currency_symbol_for(catchment_id: str) -> str:
        return {"thames": "£", "halong": "$"}.get(catchment_id, "£")


class ConstructionPage(CommercialBasePage):
    def generate_elements(self, commercial_data: Dict[str, Any], **kwargs) -> List:
        return render_construction(_asset(commercial_data).get("Construction", {}), self)


class RiskAssessmentPage(CommercialBasePage):
    def generate_elements(self, commercial_data: Dict[str, Any], **kwargs) -> List:
        return render_risk_assessment(_asset(commercial_data).get("RiskAssessment", {}), self)


class EnergyPage(CommercialBasePage):
    def generate_elements(self, commercial_data: Dict[str, Any], **kwargs) -> List:
        # EnergyPerformance sits at the top level of the commercial record,
        # not under CommercialAsset (matches the residential CDM shape).
        energy = (commercial_data.get("EnergyPerformance")
                  or _asset(commercial_data).get("EnergyPerformance")
                  or {})
        return render_energy(energy, self)


class ProtectionPage(CommercialBasePage):
    def generate_elements(self, commercial_data: Dict[str, Any], **kwargs) -> List:
        protection = (commercial_data.get("ProtectionMeasures")
                      or _asset(commercial_data).get("ProtectionMeasures")
                      or {})
        return render_protection(protection, self)


class HistoryPage(CommercialBasePage):
    def generate_elements(self, commercial_data: Dict[str, Any], **kwargs) -> List:
        history = (commercial_data.get("HistoryAndIncidents")
                   or _asset(commercial_data).get("HistoryAndIncidents")
                   or {})
        return render_history(history, self)


class TransactionsPage(CommercialBasePage):
    def generate_elements(self, commercial_data: Dict[str, Any], **kwargs) -> List:
        transactions = (commercial_data.get("TransactionHistory")
                        or _asset(commercial_data).get("TransactionHistory")
                        or {})
        return render_transactions(transactions, self)
