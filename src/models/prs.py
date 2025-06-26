import QuantLib as ql

# Set evaluation date
today = ql.Date(26, 6, 2025)
ql.Settings.instance().evaluationDate = today

# Define CDS parameters
side = ql.Protection.Buyer
notional = 10e6
upfront_rate = 0.0  # 0% upfront
running_spread = 0.01
convention = ql.Following
day_counter = ql.Actual360()
calendar = ql.UnitedStates(ql.UnitedStates.NYSE)
protection_start = calendar.advance(today, 1, ql.Days)
upfront_date = calendar.advance(today, 3, ql.Days)  # T+3 settlement

# Create schedule
schedule = ql.Schedule(
    protection_start,
    ql.Date(26, 6, 2030),
    ql.Period(ql.Quarterly),
    calendar,
    ql.Following,
    ql.Following,
    ql.DateGeneration.TwentiethIMM,
    False
)

# Build curves
risk_free_curve = ql.FlatForward(today, 0.03, ql.Actual365Fixed())
hazard_quote = ql.SimpleQuote(0.04)
hazard_curve = ql.FlatHazardRate(today, ql.QuoteHandle(hazard_quote), ql.Actual365Fixed())

# Create CDS with upfront using standard constructor
cds = ql.CreditDefaultSwap(
    side,
    notional,
    upfront_rate,        # Upfront payment rate
    running_spread,      # Running spread
    schedule,
    convention,
    day_counter,
    True,                # settles_accrual
    True,                # pays_at_default_time
    protection_start,
    upfront_date         # Upfront payment date
)

# Create pricing engine
engine = ql.IsdaCdsEngine(
    ql.DefaultProbabilityTermStructureHandle(hazard_curve),
    0.40,
    ql.YieldTermStructureHandle(risk_free_curve),
    True
)

# Attach engine
cds.setPricingEngine(engine)

# Print outputs
print(f"NPV: ${cds.NPV():,.2f}")
print(f"Fair Spread: {cds.fairSpread():.4f} ({cds.fairSpread()*10000:.1f} bps)")
print(f"Fair Upfront: {cds.fairUpfront():.4f}")
print(f"Coupon Leg NPV: ${cds.couponLegNPV():,.2f}")
print(f"Default Leg NPV: ${cds.defaultLegNPV():,.2f}")

# Calculate spread sensitivity manually
original_npv = cds.NPV()
hazard_quote.setValue(hazard_quote.value() + 0.0001)  # Bump hazard rate by 1bp
bumped_npv = cds.NPV()
spread_sens = (bumped_npv - original_npv)  # Sensitivity per 1bp
hazard_quote.setValue(hazard_quote.value() - 0.0001)  # Reset

# Calculate upfront sensitivity
original_upfront = cds.fairUpfront()
upfront_quote = ql.SimpleQuote(original_upfront + 0.01)  # Bump upfront by 1%
upfront_handle = ql.QuoteHandle(upfront_quote)
cds = ql.CreditDefaultSwap(
    side,
    notional,
    upfront_quote.value(),
    running_spread,
    schedule,
    convention,
    day_counter,
    True,
    True,
    protection_start,
    upfront_date
)
cds.setPricingEngine(engine)
bumped_npv = cds.NPV()
upfront_sens = (bumped_npv - original_npv)  # Sensitivity per 1% upfront

# Print sensitivities
print(f"Spread Sensitivity: ${spread_sens:,.2f} per bp")
print(f"Upfront Sensitivity: ${upfront_sens:,.2f} per %")


