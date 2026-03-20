# portfolio_flood_base_v2.py Documentation

## Overview
`portfolio_flood_base_v2.py` serves as the core foundation for flood risk modeling and analysis. It contains the essential classes and functions needed to process property data, calculate flood impacts, and generate reports.

## Key Components

### FloodRiskModel Class
Core class for flood risk calculations and analysis.

#### Initialization Parameters
- `properties`: GeoDataFrame containing property details
  - geometry: Property location
  - property_id: Unique identifier
  - value: Current market value
  - floor_height: Height above ground
  - building_type: Type of construction
  - flood_zone_risk: Risk factor for flood zone
  - local_density: Population density indicator
- `flood_event`: Dictionary with flood event details
  - center_lat: Flood center latitude
  - center_lon: Flood center longitude
  - radius: Affected radius in meters
  - max_depth: Maximum flood depth in meters
- `gauge_data`: Optional DataFrame with water level measurements
- `correlation_distance`: Distance threshold for correlation (default: 1000)
- `base_correlation`: Base correlation between properties (default: 0.4)

#### Key Methods
- `calculate_flood_depths()`: Computes flood depth at each property
- `calculate_direct_impacts()`: Determines value impact from flood depths
- `simulate_portfolio_impact()`: Simulates portfolio-wide impact with correlations
- `analyze_spatial_concentration()`: Analyzes clustering of impacts
- `visualize_risk()`: Creates visual representations of risk

### FloodRiskReport Class
Handles all reporting and visualization functionality.

#### Initialization Parameters
- `model`: Instance of FloodRiskModel
- `paths`: ProjectPaths instance for file management

#### Key Methods
- `generate_impact_report()`: Creates impact analysis report
- `generate_concentration_report()`: Reports on spatial concentration
- `create_visualizations()`: Generates all visual outputs
- `_plot_spatial_correlation_heatmap()`: Creates correlation visualization

### Helper Functions

#### load_portfolio_data()
Loads and prepares data for analysis.

**Parameters:**
- `portfolio_csv`: Path to portfolio CSV file
- `center_lat`: Center latitude (default: 51.5074)
- `center_lon`: Center longitude (default: -0.1278)

**Returns:**
- Tuple of (properties, gauge_data, flood_event)

## Dependencies
- numpy: Numerical computations
- pandas: Data manipulation
- geopandas: Spatial data handling
- scipy: Scientific computations
- folium: Interactive mapping
- seaborn: Statistical visualization
- matplotlib: Plotting
- shapely: Geometric operations

---

# portfolio_flood_model_v5.py Documentation

## Overview
`portfolio_flood_model_v5.py` serves as the execution framework for the flood risk analysis system. It orchestrates the workflow and manages the interaction between different components.

## Key Functions

### main()
Primary execution function that orchestrates the entire analysis workflow.

#### Workflow Steps:
1. Initializes paths and loads portfolio data
2. Creates and configures the risk model
3. Runs impact analysis
4. Generates reports and visualizations
5. Saves results

### process_impacts()
Processes and appends impact metrics to property data.

#### Parameters:
- `model`: FloodRiskModel instance
- `properties`: GeoDataFrame of property data

#### Returns:
- Enhanced GeoDataFrame with added impact metrics:
  - flood_depth_m: Calculated flood depth
  - damage_pct: Damage as percentage
  - damage_value: Financial impact

### save_results()
Handles saving of processed results to CSV.

#### Parameters:
- `properties`: Enhanced GeoDataFrame with impact data
- `paths`: ProjectPaths instance

## Usage Example
```python
if __name__ == "__main__":
    main()
```

## Dependencies
- portfolio_flood_base_v2: Core modeling functionality
- utilities.ProjectPaths: Path management

## Output Files
- portfolio_data_with_impacts.csv: Complete analysis results
- flood_risk.html: Interactive risk visualization
- flood_risk.png: Static risk visualization
- correlation_heatmap.png: Spatial correlation analysis

## Flow Diagram
```
Load Data -> Initialize Model -> Run Analysis -> Generate Reports -> Save Results
```

## Notes
- Provides clear progress feedback during execution
- Maintains separation of concerns between execution and core functionality
- Handles errors gracefully with informative messages
