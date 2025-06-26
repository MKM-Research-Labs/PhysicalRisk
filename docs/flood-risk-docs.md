# Flood Risk Model Documentation

## Overview
The FloodRiskModel is a comprehensive implementation for assessing and analyzing flood risks for property portfolios. It combines spatial analysis, statistical modeling, and financial risk assessment to provide detailed insights into potential flood impacts on property values.

## Core Components

### 1. Spatial Correlation
The model uses a spatial correlation matrix to capture the relationship between properties based on their geographic proximity. The correlation between two properties is calculated using an exponential decay function:

```
correlation(i,j) = base_correlation * exp(-distance(i,j) / correlation_distance)
```

Where:
- `base_correlation`: Base level of correlation (default: 0.4)
- `distance(i,j)`: Distance between properties i and j
- `correlation_distance`: Distance threshold for correlation decay (default: 1000m)

### 2. Flood Depth Calculation
Flood depths are calculated using a radial decay function from the flood event center:

```
depth(x,y) = max_depth * (1 - distance(x,y)/radius)
```
Where:
- `max_depth`: Maximum flood depth at the center
- `radius`: Affected radius of the flood event
- `distance(x,y)`: Distance from point (x,y) to flood center

For locations with gauge data, depths are interpolated using inverse distance weighting:

```
interpolated_depth = Σ(wi * di) / Σ(wi)
where wi = 1/distance_i²
```

### 3. Impact Assessment

#### Direct Impact Calculation
Property impacts are calculated using a depth-damage function that considers:
- Flood depth
- Property type adjustments
- Location risk factors
- Local density

The vulnerability curve is defined by these depth-damage relationships:
| Depth (m) | Damage Factor |
|-----------|---------------|
| 0.0       | 0.00         |
| 0.5       | 0.25         |
| 1.0       | 0.40         |
| 2.0       | 0.60         |
| 4.0       | 0.85         |
| 6.0       | 1.00         |

Final damage is calculated as:
```
damage = base_damage * type_adjustment * (1 + local_density * location_risk * 0.1)
```

#### Portfolio Impact Simulation
The model uses Monte Carlo simulation to estimate portfolio-wide impacts:
1. Generates correlated random shocks using the spatial correlation matrix
2. Combines direct impacts with random shocks
3. Calculates portfolio-level metrics:
   - Mean impact
   - 95% Value at Risk (VaR)
   - 95% Expected Shortfall (ES)
   - Maximum impact

### 4. Risk Clustering
Properties are clustered based on:
- Flood depth exposure
- Geographic location
- Property value

Using K-means clustering to identify risk-similar groups.

### 5. Advanced Metrics

#### Geographic Concentration
Calculated using the Herfindahl-Hirschman Index (HHI):
```
HHI = Σ(market_share_i²)
```
Where market_share_i is the proportion of total value in each geographic grid cell.

#### Impact Concentration
Similar to geographic concentration but based on the distribution of potential losses:
```
Impact_HHI = Σ(impact_share_i²)
```

## Visualization Capabilities

### 1. Interactive Maps
- Property locations with impact-based coloring
- Flood event radius
- Gauge locations (if available)
- Popup information with property details

### 2. Static Visualizations
- Risk heat maps
- Spatial correlation matrices
- Impact distribution plots
- Cluster analysis visualizations

## Reporting Components

The FloodRiskReport class provides structured reporting of:
1. Portfolio impact analysis
2. Spatial concentration analysis
3. Risk cluster analysis
4. Stress test results
5. Advanced metrics

## Usage Example

```python
# Initialize model
model = FloodRiskModel(
    properties=property_data,
    flood_event={
        'center_lat': 51.5074,
        'center_lon': -0.1278,
        'radius': 1000,
        'max_depth': 2.0
    },
    gauge_data=gauge_readings
)

# Run analysis
impact_results = model.simulate_portfolio_impact()
concentration = model.analyze_spatial_concentration()
clusters = model.analyze_risk_clusters()

# Generate reports
report = FloodRiskReport(model, paths)
report.generate_impact_report(impact_results)
report.generate_concentration_report(concentration)
report.create_visualizations()
```

## Dependencies
- numpy
- pandas
- geopandas
- scipy
- folium
- seaborn
- matplotlib
- sklearn
- shapely

## Technical Requirements
- Python 3.7+
- Spatial data handling capabilities
- GIS functionality
