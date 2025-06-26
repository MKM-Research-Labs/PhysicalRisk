# Portfolio Flood Model v6 Documentation

## Overview

`portfolio_flood_model_v6.py` is a Python module developed by MKM Research Labs that provides comprehensive flood risk analysis for property portfolios. The software enables users to assess potential flood damage impacts on real estate assets, analyze risk concentration, and visualize results geospatially.

## Key Features

- Load and process property data from JSON and CSV formats
- Calculate flood depths and damage impacts on properties
- Generate impact and concentration reports
- Create geospatial visualizations of flood risk
- Save analysis results for further processing

## Dependencies

The module relies on several Python libraries:

- **Data Handling**: numpy, pandas, geopandas
- **Spatial Calculations**: scipy
- **Visualization**: folium, seaborn, matplotlib
- **Geometry Processing**: shapely
- **Custom Components**:
  - PropertyCDM (Common Data Model for property standardization)
  - FloodRiskModel (Core simulation engine)
  - FloodRiskReport (Results reporting)

## Module Architecture

### Main Components

1. **Data Loading and Preprocessing**
   - `load_json_portfolio()`: Processes property portfolio data from JSON
   - `load_portfolio_data()`: Handles various data formats and prepares flood event information

2. **Core Analysis**
   - `process_impacts()`: Calculates and appends impact metrics to property data
   - FloodRiskModel integration for depth and damage calculations

3. **Result Processing**
   - `save_results()`: Persists analysis outcomes to CSV
   - FloodRiskReport integration for report generation and visualization

4. **Main Execution Flow**
   - Path initialization
   - Data loading
   - Model initialization and simulation
   - Report generation
   - Visualization creation
   - Results saving

## Function Documentation

### `load_json_portfolio(json_path: str) -> gpd.GeoDataFrame`

Loads and processes portfolio data from JSON format.

**Parameters:**
- `json_path (str)`: Path to JSON file containing property portfolio data

**Returns:**
- `gpd.GeoDataFrame`: Geodataframe containing standardized property data

**Raises:**
- `FileNotFoundError`: If JSON file not found
- `ValueError`: If JSON structure is invalid or missing required fields

**Process:**
1. Reads and validates JSON structure
2. Extracts and standardizes properties using PropertyCDM
3. Validates required coordinates
4. Creates geometry column for GeoDataFrame
5. Returns GeoDataFrame with WGS84 coordinate system

### `process_impacts(model: FloodRiskModel, properties: gpd.GeoDataFrame) -> gpd.GeoDataFrame`

Processes and appends impact metrics to properties dataframe.

**Parameters:**
- `model (FloodRiskModel)`: Initialized flood risk model
- `properties (gpd.GeoDataFrame)`: Property data

**Returns:**
- `gpd.GeoDataFrame`: Enhanced property data with flood metrics

**Process:**
1. Calculates flood depths using model
2. Calculates direct impacts from flood depths
3. Creates copy of original properties dataframe
4. Appends flood depth (m), damage percentage, and damage value to each property
5. Returns enhanced dataframe

### `save_results(properties: gpd.GeoDataFrame, paths: ProjectPaths) -> None`

Saves processed results to CSV.

**Parameters:**
- `properties (gpd.GeoDataFrame)`: Property data with impact metrics
- `paths (ProjectPaths)`: Project path manager

**Returns:**
- `None`: Function saves file but doesn't return a value

### `load_portfolio_data(portfolio_path: str) -> Tuple[gpd.GeoDataFrame, pd.DataFrame, Dict[str, Any]]`

Loads portfolio data and associated flood event information.

**Parameters:**
- `portfolio_path (str)`: Path to portfolio data file (JSON or CSV)

**Returns:**
- `Tuple[gpd.GeoDataFrame, pd.DataFrame, Dict[str, Any]]`: Tuple containing:
  - Property data
  - Gauge data
  - Flood event parameters

**Process:**
1. Loads property data from JSON or CSV
2. Creates sample gauge data (for testing)
3. Creates flood event parameters (for testing)
4. Returns all three datasets

### `main()`

Main execution function for flood risk analysis.

**Process:**
1. Initializes paths
2. Loads portfolio data
3. Initializes and runs model
4. Processes impacts
5. Generates reports
6. Creates visualizations
7. Saves results

## Usage Example

```python
# Basic usage from command line
python portfolio_flood_model_v6.py

# Integration within another script
from portfolio_flood_model_v6 import load_portfolio_data, FloodRiskModel, process_impacts

# Load data
properties, gauge_data, flood_event = load_portfolio_data('path/to/portfolio.json')

# Initialize model
model = FloodRiskModel(
    properties=properties,
    flood_event=flood_event,
    gauge_data=gauge_data
)

# Run analysis
impact_results = model.simulate_portfolio_impact()
enhanced_properties = process_impacts(model, properties)

# Process results as needed
enhanced_properties.to_csv('results.csv', index=False)
```

## Data Structure Requirements

### JSON Portfolio Structure

The JSON portfolio file must contain a `properties` array with objects that can be mapped to the PropertyCDM standard. Each property must have at minimum:

- Latitude and longitude coordinates
- Identifiable property attributes
- Value/price information for damage calculations

Example structure:
```json
{
  "properties": [
    {
      "id": "prop123",
      "latitude": 51.5074,
      "longitude": -0.1278,
      "sale_price": 500000,
      "property_type": "residential",
      ...
    },
    ...
  ]
}
```

### Flood Event Structure

The flood event is represented as a dictionary with:
- `center_lat`: Center latitude of flood event
- `center_lon`: Center longitude of flood event
- `radius`: Radius of the flood impact area in meters
- `max_depth`: Maximum flood depth in meters

### Gauge Data Structure

Gauge data is represented as a DataFrame with:
- `gauge_id`: Unique identifier for each gauge
- `latitude`: Gauge latitude
- `longitude`: Gauge longitude
- `water_level`: Observed water level in meters

## Output

### Enhanced Property Data

The analysis adds several columns to the original property data:
- `flood_depth_m`: Calculated flood depth at property location (meters)
- `damage_pct`: Damage percentage based on depth and property characteristics
- `damage_value`: Financial impact value (property value × damage percentage)

### Reports and Visualizations

The module generates:
- Impact reports summarizing portfolio-level damage
- Concentration reports identifying risk hotspots
- Geospatial visualizations of affected properties

## Notes

- The module contains test gauge data and flood event parameters that would be replaced with actual data in production environments
- Property standardization relies on the PropertyCDM module for consistent data representation

## License

Copyright (c) 2025 MKM Research Labs. All rights reserved.

This software is provided under license by MKM Research Labs. Use, reproduction, distribution, or modification of this code is subject to the terms and conditions of the license agreement provided with this software.
