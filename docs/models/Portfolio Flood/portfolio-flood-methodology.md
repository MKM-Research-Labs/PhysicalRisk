# Portfolio-Level Flood Risk Assessment Methodology

## 1. Introduction

This methodology provides a framework for assessing flood risk impacts on residential property portfolios, with particular emphasis on spatial clustering effects. The approach combines physical flood damage modeling with spatial correlation analysis to provide comprehensive portfolio-level risk metrics.

## 2. Core Components

### 2.1 Physical Flood Risk Model

The base flood risk for each property i is calculated using:

$R_i = f(d_i, h_i, t_i)$

Where:
- $R_i$ is the risk score for property i
- $d_i$ is the flood depth at property location
- $h_i$ is the floor height above ground level
- $t_i$ is the building type factor
- $f()$ is the damage function

The depth-damage function follows the form:

$f(d) = \alpha(1 + \tanh(d))$

Where:
- $\alpha$ is the baseline discount rate (8.14% based on Wei & Zhao, 2022)
- $d$ is the effective flood depth (flood level minus floor height)

### 2.2 Spatial Correlation Model

The spatial correlation matrix $\Sigma$ is constructed using:

$\Sigma_{ij} = \rho_0 \exp(-\frac{D_{ij}}{l})$

Where:
- $\rho_0$ is the base correlation parameter
- $D_{ij}$ is the distance between properties i and j
- $l$ is the correlation length scale
- $\Sigma_{ij}$ is the correlation between properties i and j

### 2.3 Portfolio Impact Model

The total portfolio impact is simulated using:

$I_p = \sum_{i=1}^n V_i R_i (1 + \sigma Z_i)$

Where:
- $I_p$ is the portfolio impact
- $V_i$ is the value of property i
- $R_i$ is the direct risk impact
- $\sigma$ is the shock factor
- $Z_i$ is a correlated random variable $Z \sim N(0, \Sigma)$

## 3. Input Parameters

### 3.1 Property Characteristics
| Parameter | Description | Units | Source |
|-----------|-------------|--------|---------|
| Location | Geospatial coordinates | Lat/Long | Property data |
| Value | Current market value | Currency | Valuation data |
| Floor Height | Height above ground | Meters | Building specs |
| Building Type | Construction category | Category | Property data |

### 3.2 Flood Event Parameters
| Parameter | Description | Units | Source |
|-----------|-------------|--------|---------|
| Center Location | Flood event center | Lat/Long | Event data |
| Radius | Impact radius | Meters | Event data |
| Max Depth | Maximum flood depth | Meters | Event data |

### 3.3 Model Parameters
| Parameter | Description | Default Value | Reference |
|-----------|-------------|---------------|------------|
| Base Correlation | Minimum correlation | 0.4 | Empirical |
| Correlation Distance | Distance decay | 1000m | Spatial analysis |
| Shock Factor | Impact variation | 0.2 | Calibration |

## 4. Risk Metrics

The methodology produces several key risk metrics:

### 4.1 Direct Impact Metrics
- Individual property value impacts
- Mean portfolio impact
- Maximum portfolio impact

### 4.2 Risk Distribution Metrics
- 95% Value at Risk (VaR):
  $VaR_{95} = \inf\{l \in \mathbb{R}: P(L > l) \leq 0.05\}$
  
- 95% Expected Shortfall (ES):
  $ES_{95} = E[L|L > VaR_{95}]$

### 4.3 Spatial Concentration Metrics
- Impact cluster identification
- Grid-based concentration analysis
- Spatial correlation effects

## 5. Methodology Process Flow

1. Data Preparation:
   - Property portfolio data validation
   - Flood event parameter specification
   - Spatial index construction

2. Base Impact Calculation:
   - Flood depth interpolation
   - Depth-damage function application
   - Direct impact calculation

3. Correlation Analysis:
   - Spatial distance matrix construction
   - Correlation matrix computation
   - Shock factor calibration

4. Portfolio Simulation:
   - Correlated shock generation
   - Impact aggregation
   - Risk metric calculation

5. Concentration Analysis:
   - Spatial clustering assessment
   - Grid-based aggregation
   - Hot spot identification

## 6. Implementation Notes

### 6.1 Computational Considerations
- KD-tree for spatial queries
- Sparse matrix operations for large portfolios
- Parallel processing for simulations

### 6.2 Limitations
- Assumes static flood event
- Simplified damage function
- Normal distribution assumption for shocks

### 6.3 Extensions
- Dynamic flood modeling
- Non-linear correlation structures
- Alternative damage functions

## 7. References

1. Wei, F., & Zhao, L. (2022). The Effect of Flood Risk on Residential Land Prices. Land, 11, 1612.
2. Belanger & Bourdeau-Brien (2018). Impact of flood risk on property values.
3. McKenzie & Levendis (2010). Flood hazards and urban housing markets.
4. Mohor et al. (2021). Residential flood loss estimated from Bayesian multilevel models.

