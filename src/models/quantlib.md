# Converting Hazard Points to QuantLib Credit Curves for CDS Pricing

## Overview

This guide shows how to convert hazard points (conditional default probabilities) into a credit curve suitable for QuantLib's CDS pricing functions.

## Key Mathematical Relationships

### 1. Hazard Points to Survival Probabilities

Given hazard points hâ‚, hâ‚‚, ..., hâ‚… where háµ¢ = probability of default in year i given no default in previous years:

```
S(tâ‚) = 1 - hâ‚
S(tâ‚‚) = S(tâ‚) Ã— (1 - hâ‚‚) = (1 - hâ‚) Ã— (1 - hâ‚‚)
S(táµ¢) = âˆâ±¼â‚Œâ‚â± (1 - hâ±¼)
```

### 2. Survival Probabilities to Cumulative Hazard Rates

```
H(t) = -ln(S(t))
```

### 3. Instantaneous Hazard Rates (for piecewise constant assumption)

```
Î»áµ¢ = H(táµ¢) - H(táµ¢â‚‹â‚)
```

## QuantLib Implementation

### Method 1: Using SurvivalProbabilityCurve (Recommended)

```python
import QuantLib as ql

def hazard_points_to_credit_curve(hazard_points, years, evaluation_date):
    """
    Convert hazard points to QuantLib credit curve
    """
    # Convert to survival probabilities
    survival_probs = []
    current_survival = 1.0
    
    for hazard in hazard_points:
        current_survival = current_survival * (1 - hazard)
        survival_probs.append(current_survival)
    
    # Create dates
    dates = [evaluation_date]
    for year in years:
        dates.append(evaluation_date + ql.Period(year, ql.Years))
    
    # Include initial survival probability of 1.0
    curve_survival_probs = [1.0] + survival_probs
    
    # Create curve
    credit_curve = ql.SurvivalProbabilityCurve(
        dates, 
        curve_survival_probs, 
        ql.Actual365Fixed(), 
        ql.TARGET()
    )
    
    credit_curve.enableExtrapolation()
    return credit_curve
```

### Method 2: Using HazardRateCurve

```python
def create_hazard_rate_curve(hazard_points, years, evaluation_date):
    """
    Alternative approach using HazardRateCurve
    """
    # Convert to survival probabilities first
    survival_probs = []
    current_survival = 1.0
    
    for hazard in hazard_points:
        current_survival = current_survival * (1 - hazard)
        survival_probs.append(current_survival)
    
    # Calculate instantaneous hazard rates
    cumulative_hazards = [-np.log(sp) for sp in survival_probs]
    instantaneous_hazards = []
    prev_cum_hazard = 0
    
    for cum_hazard in cumulative_hazards:
        inst_hazard = cum_hazard - prev_cum_hazard
        instantaneous_hazards.append(inst_hazard)
        prev_cum_hazard = cum_hazard
    
    # Create dates and curve
    dates = [evaluation_date + ql.Period(year, ql.Years) for year in years]
    hazard_curve = ql.HazardRateCurve(dates, instantaneous_hazards, ql.Actual365Fixed())
    hazard_curve.enableExtrapolation()
    
    return hazard_curve
```

## Using the Credit Curve with CDS Pricing

Once you have the credit curve, you can use it with any of QuantLib's CDS pricing engines:

```python
def price_cds_with_credit_curve(credit_curve, cds_parameters):
    """
    Price CDS using the credit curve
    """
    # Create pricing engines
    credit_handle = ql.DefaultProbabilityTermStructureHandle(credit_curve)
    
    # Example with ISDA engine
    engine = ql.IsdaCdsEngine(
        credit_handle,
        recovery_rate,
        ql.YieldTermStructureHandle(risk_free_curve)
    )
    
    # Set engine and price
    cds.setPricingEngine(engine)
    return cds.NPV()
```

## Complete Working Example

```python
# Example hazard points
hazard_points = [0.02, 0.025, 0.03, 0.035, 0.04]  # h1...h5
years = [1, 2, 3, 4, 5]

# Set up QuantLib
today = ql.Date(15, 6, 2025)
ql.Settings.instance().evaluationDate = today

# Create credit curve
credit_curve = hazard_points_to_credit_curve(hazard_points, years, today)

# Verify the curve
for i, year in enumerate(years):
    date = today + ql.Period(year, ql.Years)
    survival_prob = credit_curve.survivalProbability(date)
    print(f"Year {year}: Survival Probability = {survival_prob:.4f}")
```

## Key Points

1. **Method Choice**: `SurvivalProbabilityCurve` is generally easier and more direct for this conversion.

2. **Extrapolation**: Always call `enableExtrapolation()` to handle dates beyond your input data.

3. **Date Convention**: Make sure your dates align with your CDS contract dates.

4. **Day Count**: Use consistent day count conventions throughout your calculations.

5. **Validation**: Always verify your survival probabilities match your expected values.

## Common Pitfalls

- **Missing Initial Point**: Don't forget to include the evaluation date with survival probability = 1.0
- **Date Misalignment**: Ensure curve dates match your CDS payment schedule
- **Extrapolation**: Enable extrapolation for pricing CDS with maturities beyond your data
- **Day Count Consistency**: Use the same day count convention for all related curves