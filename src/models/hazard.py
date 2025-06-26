
import QuantLib as ql
import numpy as np

def hazard_points_to_credit_curve(hazard_points, years, evaluation_date, day_count=None):
    """
    Convert hazard points (conditional default probabilities) to QuantLib credit curve

    Parameters:
    hazard_points: list of conditional default probabilities [h1, h2, h3, h4, h5]
    years: list of years corresponding to hazard points [1, 2, 3, 4, 5]
    evaluation_date: QuantLib Date object for evaluation
    day_count: QuantLib DayCounter (defaults to Actual365Fixed)

    Returns:
    QuantLib credit curve object
    """

    if day_count is None:
        day_count = ql.Actual365Fixed()

    # Step 1: Convert hazard points to survival probabilities
    survival_probs = []
    current_survival = 1.0

    for hazard in hazard_points:
        current_survival = current_survival * (1 - hazard)
        survival_probs.append(current_survival)

    # Step 2: Create dates for the curve
    dates = [evaluation_date]  # Start with evaluation date
    for year in years:
        dates.append(evaluation_date + ql.Period(year, ql.Years))

    # Step 3: Survival probabilities including initial 1.0
    curve_survival_probs = [1.0] + survival_probs

    # Step 4: Create QuantLib SurvivalProbabilityCurve
    credit_curve = ql.SurvivalProbabilityCurve(
        dates, 
        curve_survival_probs, 
        day_count, 
        ql.TARGET()  # Calendar
    )

    # Enable extrapolation for dates beyond the curve
    credit_curve.enableExtrapolation()

    return credit_curve

def create_cds_pricing_engines(credit_curve, recovery_rate, risk_free_curve):
    """
    Create different CDS pricing engines using the credit curve

    Returns:
    Dictionary of pricing engines
    """

    # Wrap curves in handles
    credit_handle = ql.DefaultProbabilityTermStructureHandle(credit_curve)
    risk_free_handle = ql.YieldTermStructureHandle(risk_free_curve)

    engines = {
        'ISDA': ql.IsdaCdsEngine(credit_handle, recovery_rate, risk_free_handle),
        'Integral': ql.IntegralCdsEngine(ql.Period('1d'), credit_handle, recovery_rate, risk_free_handle),  
        'Midpoint': ql.MidPointCdsEngine(credit_handle, recovery_rate, risk_free_handle)
    }

    return engines

def price_cds_with_hazard_points():
    """
    Complete example of CDS pricing using hazard points
    """

    # Set evaluation date
    today = ql.Date(15, 6, 2025)
    ql.Settings.instance().evaluationDate = today

    # Example hazard points (conditional default probabilities)
    hazard_points = [0.02, 0.025, 0.03, 0.035, 0.04]  # h1, h2, h3, h4, h5
    years = [1, 2, 3, 4, 5]

    print("=== Hazard Points to Credit Curve Conversion ===")
    print(f"Evaluation Date: {today}")
    print(f"Hazard Points: {hazard_points}")
    print()

    # Create credit curve from hazard points
    credit_curve = hazard_points_to_credit_curve(hazard_points, years, today)

    # Print survival probabilities from the curve
    print("Survival Probabilities from Credit Curve:")
    for i, year in enumerate(years):
        date = today + ql.Period(year, ql.Years)
        survival_prob = credit_curve.survivalProbability(date)
        default_prob = credit_curve.defaultProbability(date)
        hazard_rate = credit_curve.hazardRate(date)

        print(f"Year {year}: S(t)={survival_prob:.4f}, PD(t)={default_prob:.4f}, Î»(t)={hazard_rate:.4f}")

    print()

    # Set up risk-free curve (flat 3.5%)
    risk_free_rate = 0.035
    risk_free_curve = ql.FlatForward(
        today, 
        ql.QuoteHandle(ql.SimpleQuote(risk_free_rate)), 
        ql.Actual365Fixed(),
        ql.Compounded, 
        ql.Quarterly
    )

    # CDS contract parameters
    recovery_rate = 0.40
    cds_coupon = 0.01  # 100 bps
    notional = 10_000_000
    maturity_date = today + ql.Period(5, ql.Years)

    # Create CDS schedule
    schedule = ql.MakeSchedule(
        today,
        maturity_date,
        ql.Period(ql.Quarterly),
        ql.Quarterly,
        ql.TARGET(),
        ql.Following,
        ql.Following,
        ql.DateGeneration.Forward,
        False
    )

    # Create CDS contract
    cds = ql.CreditDefaultSwap(
        ql.Protection.Buyer,
        notional,
        cds_coupon,
        schedule,
        ql.Following,
        ql.Actual365Fixed()
    )

    # Create pricing engines
    engines = create_cds_pricing_engines(credit_curve, recovery_rate, risk_free_curve)

    print("=== CDS Valuation Results ===")
    print(f"Notional: ${notional:,}")
    print(f"CDS Coupon: {cds_coupon*10000:.0f} bps")
    print(f"Recovery Rate: {recovery_rate:.1%}")
    print(f"Risk-free Rate: {risk_free_rate:.1%}")
    print()

    # Price using different engines
    for engine_name, engine in engines.items():
        cds.setPricingEngine(engine)

        print(f"--- {engine_name} Engine ---")
        print(f"Premium Leg NPV: ${cds.couponLegNPV():,.2f}")
        print(f"Protection Leg NPV: ${cds.defaultLegNPV():,.2f}")
        print(f"Total NPV: ${cds.NPV():,.2f}")
        print(f"Fair Spread: {cds.fairSpread()*10000:.2f} bps")
        print()

    return credit_curve, cds, engines

# Alternative approach using HazardRateCurve
def create_hazard_rate_curve_approach(hazard_points, years, evaluation_date):
    """
    Alternative approach using HazardRateCurve directly
    """

    # Convert hazard points to instantaneous hazard rates
    # For piecewise constant hazard rates
    survival_probs = []
    current_survival = 1.0

    for hazard in hazard_points:
        current_survival = current_survival * (1 - hazard)
        survival_probs.append(current_survival)

    # Calculate cumulative hazard rates: H(t) = -ln(S(t))
    cumulative_hazards = [-np.log(sp) for sp in survival_probs]

    # Calculate instantaneous hazard rates for piecewise constant assumption
    instantaneous_hazards = []
    prev_cum_hazard = 0
    for cum_hazard in cumulative_hazards:
        inst_hazard = cum_hazard - prev_cum_hazard
        instantaneous_hazards.append(inst_hazard)
        prev_cum_hazard = cum_hazard

    # Create dates
    dates = [evaluation_date + ql.Period(year, ql.Years) for year in years]

    # Create HazardRateCurve
    hazard_curve = ql.HazardRateCurve(dates, instantaneous_hazards, ql.Actual365Fixed())
    hazard_curve.enableExtrapolation()

    return hazard_curve

if __name__ == "__main__":
    # Run the example
    try:
        credit_curve, cds, engines = price_cds_with_hazard_points()
        print("âœ“ Successfully created credit curve and priced CDS using hazard points!")

        # Test alternative approach
        print("\n=== Alternative Hazard Rate Curve Approach ===")
        today = ql.Date(15, 6, 2025)
        hazard_points = [0.02, 0.025, 0.03, 0.035, 0.04]
        years = [1, 2, 3, 4, 5]

        hazard_curve = create_hazard_rate_curve_approach(hazard_points, years, today)
        print("âœ“ Alternative hazard rate curve created successfully!")

    except Exception as e:
        print(f"Error: {e}")
        print("Note: This example requires QuantLib to be installed.")
        print("Install with: pip install QuantLib-Python")