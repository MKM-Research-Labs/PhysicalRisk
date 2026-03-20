# Property Valuation Model with Flood Risk Integration
## Technical Documentation

### Overview
This Python-based property valuation model combines traditional real estate metrics with flood risk assessment to provide comprehensive property valuations. The model utilizes XGBoost with PCA dimensionality reduction to process multiple features while maintaining interpretability.

### Core Components

#### 1. Model Architecture
- **Base Model**: XGBoost Regressor
- **Feature Processing**: Principal Component Analysis (PCA)
- **Scaling**: StandardScaler for feature normalization
- **Spatial Analysis**: GeoPandas and KDTree for location-based calculations

#### 2. Feature Categories

##### Sales History Features
```python
sales_features = {
    'last_purchase_value': float,    # Previous purchase price
    'years_since_purchase': float,   # Time since last purchase
    'annualized_growth': float,      # Annual price growth rate
    'material_building_work': int,   # Renovation flag
    'years_since_building_work': float # Time since renovation
}
```

##### Location Features
```python
location_features = {
    'latitude': float,               # Property latitude
    'longitude': float,              # Property longitude
    'floor_height': float,           # Height above ground
    'distance_to_center': float,     # Distance to CBD
    'local_density': float,          # Property density in area
    'elevation': float,              # Elevation above sea level
    'flood_zone_risk': float        # Calculated flood risk score
}
```

##### Property Characteristics
```python
property_features = {
    'property_age': float,           # Age in years
    'lot_area': float,              # Total lot size
    'living_space': float,          # Habitable area
    'bedrooms': int,                # Number of bedrooms
    'bathrooms': int,               # Number of bathrooms
    'garage_capacity': int,         # Garage size
    'has_basement': bool            # Basement presence
}
```

##### Market Indicators
```python
market_features = {
    'local_price_index': float,     # Local market price level
    'price_per_sqm': float,         # Price per square meter
    'renovation_premium': float     # Value added by renovations
}
```

### Key Calculations

#### 1. Flood Risk Assessment
```python
flood_risk = 1 / (1 + elevation + floor_height)
```
- Higher elevation reduces risk
- Higher floor height reduces risk
- Risk score normalized between 0 and 1

#### 2. Property Value Appreciation
```python
current_value = purchase_value * (1 + annual_appreciation)^years
```
- Base annual appreciation: 3%
- Adjusted for local market conditions
- Includes renovation premium

#### 3. Local Market Analysis
- Uses KDTree for efficient spatial queries
- Calculates property density within 1km radius
- Determines local price trends

### Data Processing Pipeline

1. **Data Ingestion**
   - Accepts GeoDataFrame input
   - Handles missing values
   - Validates spatial data

2. **Feature Engineering**
   - Calculates derived features
   - Performs spatial analysis
   - Generates market indicators

3. **Model Training**
   - Scales features
   - Applies PCA transformation
   - Fits XGBoost model

4. **Prediction**
   - Processes new properties
   - Handles missing data
   - Returns value estimates

### Missing Value Handling

```python
numeric_cols = [
    'last_purchase_value', 'property_age', 'lot_area',
    'living_space', 'bedrooms', 'bathrooms', 'floor_height'
]
```
- Numeric columns: Median imputation
- Binary features: Zero imputation
- Categorical features: Mode imputation

### Model Parameters

#### XGBoost Configuration
```python
xgb_params = {
    'objective': 'reg:squarederror',
    'learning_rate': 0.1,
    'max_depth': 6,
    'n_estimators': 100
}
```

#### PCA Settings
- Default components: 5
- Variance ratio tracked
- Component interpretation stored

### Sample Data Generation

The model includes a sample data generator that creates realistic property portfolios:
- Geographic clustering around a center point
- Realistic value distributions
- Temporal purchase patterns
- Renovation history
- Physical characteristics

### Performance Metrics

The model tracks:
1. R² Score: Model explanation power
2. RMSE: Prediction accuracy in currency units
3. Feature Importance: PCA component contributions
4. Explained Variance: PCA effectiveness

### Usage Example

```python
# Create portfolio
properties = create_sample_portfolio()

# Initialize model
model = PropertyValuationModel()
features = model.prepare_features(properties)

# Train and evaluate
X_train, X_test, y_train, y_test = train_test_split(features, properties['value'])
model.fit(X_train, y_train)
predictions = model.predict(X_test)
```

### Future Enhancements

1. **Model Improvements**
   - Hyperparameter optimization
   - Additional feature engineering
   - Advanced spatial analysis

2. **Risk Assessment**
   - Multiple flood type integration
   - Climate change scenarios
   - Time-series flood data

3. **Market Analysis**
   - Economic indicator integration
   - Seasonal adjustments
   - Market cycle recognition

### Dependencies
- pandas
- numpy
- sklearn
- xgboost
- geopandas
- scipy
- datetime

### Performance Considerations
- Efficient spatial indexing
- Vectorized operations
- Scalable to large portfolios
- Memory-efficient processing

