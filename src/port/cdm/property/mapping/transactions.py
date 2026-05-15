# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Flatten TransactionHistory (Purchase, Rental, Insurance)."""


def flatten_transactions(prop: dict) -> dict:
    """Return flat snake_case keys for transaction-history sections."""
    trans = prop.get("TransactionHistory", {})
    purchase = trans.get("Purchase", {})
    rental = trans.get("Rental", {})
    insurance = trans.get("Insurance", {})

    return {
        "purchase_date":     purchase.get("PurchaseDate"),
        "purchase_price":    purchase.get("PurchasePriceGbp"),

        "monthly_rent":      rental.get("MonthlyRentGbp"),
        "rental_yield":      rental.get("RentalYield"),

        "insurance_premium": insurance.get("InsurancePremium"),
    }
