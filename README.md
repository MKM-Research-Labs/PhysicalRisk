# Physical Risk Modeling Project

This project provides a comprehensive framework for analyzing physical risks, particularly flood risks, for property portfolios. It includes components for data standardization, risk modeling, and visualization.

## Project Structure

The project is organized into modular components:

```
project_root/
├── src/
│   ├── cdm/                    # Common Data Models
│   │   ├── flood_gauge_cdm.py  # FloodGauge CDM implementation
│   │   ├── mortgage_cdm.py     # Mortgage CDM implementation
│   │   ├── property_cdm.py     # Property CDM implementation
│   │   ├── tc_event_cdm.py     # Tropical Cyclone Event CDM
│   │   └── tc_event_ts_cdm.py  # TC Event Time Series CDM
│   │
│   ├── models/                 # Core model implementations
│   │   ├── flood_risk_model.py       # Flood risk assessment model
│   │   ├── portfolio_flood_model.py  # Portfolio-level flood model
│   │   └── terrain_dem.py            # Terrain digital elevation model
│   │
│   ├── pricer/                 # Financial pricing modules
│   │   └── mortgage_pricer.py  # Mortgage valuation and pricing
│   │
│   ├── utilities/              # Utility functions and helpers
│   │   └── project_paths.py    # Path management utilities
│   │
│   └── visualization/          # Visualization components
│       └── tc_event_visualization.py  # TC event visualization tools
│
├── input/                      # Input data directory
├── results/                    # Results output directory
└── main.py                     # Example usage script
```

## Core Components

### Common Data Models (CDM)

The CDM modules provide standardized data representations for different entities:

- **PropertyCDM**: Standardizes property data with detailed attributes
- **FloodGaugeCDM**: Standardizes flood gauge data 
- **MortgageCDM**: Standardizes mortgage and loan data
- **TCEventCDM**: Standardizes tropical cyclone event data
- **TCEventTSCDM**: Standardizes tropical cyclone event time series data

### Models

The models modules provide core risk assessment functionality:

- **FloodRiskModel**: Assesses flood risk for individual properties
- **PortfolioFloodModel**: Analyzes flood risk for property portfolios
- **TerrainDEM**: Generates synthetic terrain digital elevation models

### Financial Pricing

The pricer modules provide financial valuation tools:

- **MortgagePricer**: Prices mortgage loans considering credit risk factors

### Visualization

The visualization modules provide tools for creating interactive visualizations:

- **TCEventVisualization**: Creates interactive maps of tropical cyclone events

## Getting Started

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the example script:
   ```
   python main.py
   ```

## Usage Examples

### Property Portfolio Flood Risk Analysis

```python
from src.utilities.project_paths import ProjectPaths
from src.models.portfolio_flood_model import PortfolioFloodModel

# Initialize paths and model
paths = ProjectPaths(__file__)
model = PortfolioFloodModel(paths)

# Run analysis on a portfolio
portfolio_path = paths.get_input_path("property_portfolio.json")
results = model.run_analysis(portfolio_path)
```

### Generating Terrain Models

```python
from src.models.terrain_dem import TerrainDEM

# Initialize terrain generator
terrain_generator = TerrainDEM("input")

# Generate terrain model and visualization
dem_path, folium_map = terrain_generator.generate_terrain_model()
```

### Working with Common Data Models

```python
from src.cdm.property_cdm import PropertyCDM

# Initialize Property CDM
property_cdm = PropertyCDM()

# Transform raw property data using CDM
standardized_property = property_cdm.create_property_mapping(raw_property_data)
```

## License

This project is proprietary software owned by MKM Research Labs.