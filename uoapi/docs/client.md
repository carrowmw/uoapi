# API Client Documentation

## Overview
The API Client module provides a robust interface for interacting with the Urban Observatory API. It handles configuration management, request handling, and data processing for sensor data retrieval and analysis.

## Classes

### APIConfig
A dataclass that holds configuration settings for the API client.

#### Attributes
- `base_url` (str): Base URL for the API (default: "https://newcastle.urbanobservatory.ac.uk/api/v1.1")
- `timeout` (int): Request timeout in milliseconds (default: 100000)
- `time_slice` (Optional[TimeSliceParams]): Time-related parameters
- `location` (Optional[LocationParams]): Location-related parameters
- `sensor` (Optional[SensorParams]): Sensor-related parameters

### TimeSliceParams
A dataclass for time-related query parameters.

#### Attributes
- `last_n_days` (Optional[int]): Number of days to look back
- `starttime` (Optional[str]): Start time for data retrieval
- `endtime` (Optional[str]): End time for data retrieval

### LocationParams
A dataclass for location-related query parameters.

#### Attributes
- `polygon_wkb` (Optional[str]): WKB representation of a polygon
- `bbox_p1_x` (Optional[float]): Bounding box point 1 X coordinate
- `bbox_p1_y` (Optional[float]): Bounding box point 1 Y coordinate
- `bbox_p2_x` (Optional[float]): Bounding box point 2 X coordinate
- `bbox_p2_y` (Optional[float]): Bounding box point 2 Y coordinate

### SensorParams
A dataclass for sensor-related query parameters.

#### Attributes
- `sensor_type` (Optional[str]): Type of sensor
- `theme` (Optional[str]): Theme category
- `broker` (Optional[str]): Broker name
- `data_variable` (Optional[str]): Data variable name

### APIClient
Main class for interacting with the Urban Observatory API.

#### Initialization
```python
client = APIClient(config_path: Optional[str] = None)
```


#### Core Methods

##### get_raw_sensor_data
Retrieves raw sensor data with configurable parameters.

```python
def get_raw_sensor_data(
self,
last_n_days: Optional[int] = None,
starttime: Optional[str] = None,
endtime: Optional[str] = None,
polygon_wkb: Optional[str] = None,
bbox_p1_x: Optional[float] = None,
bbox_p1_y: Optional[float] = None,
bbox_p2_x: Optional[float] = None,
bbox_p2_y: Optional[float] = None,
sensor_type: Optional[str] = None,
theme: Optional[str] = None,
broker: Optional[str] = None,
data_variable: Optional[str] = None
) -> Dict[str, Any]
```


##### analyze_json
Analyzes the JSON structure of raw sensor data.

```python
def analyze_json(
self,
sensor_type: Optional[str] = None,
theme: Optional[str] = None,
broker: Optional[str] = None,
data_variable: Optional[str] = None
) -> Optional[Dict[str, Any]]
```


#### Configuration Methods

##### _update_config_explicitly
Internal method to update configuration parameters.

```python
def update_config_explicitly(
self,
time_slice_params: Optional[Dict] = None,
location_params: Optional[Dict] = None,
sensor_params: Optional[Dict] = None
) -> None
```


#### Metadata Methods

##### store_metadata
Caches metadata from the API and saves it to files.

##### print_formatted_metadata
Prints formatted metadata from cached files.

#### DataFrame Methods

##### get_dataframe
Converts raw sensor data to a pandas DataFrame.

## Usage Examples

### Basic Usage

```python
# Initialize client
client = APIClient()
# Get raw sensor data
data = client.get_raw_sensor_data(
theme="Traffic",
last_n_days=7
)

# Analyze JSON structure
analysis = client.analyze_json(theme="Traffic")

# Update configuration explicitly
client.update_config_explicitly(
time_slice_params={"last_n_days": 7},
sensor_params={"theme": "Traffic"}
)
# Get data with updated config
data = client.get_raw_sensor_data()
```

## Error Handling
The module includes comprehensive error handling through the `APIError` class, which captures and logs various types of errors:
- HTTP errors
- Connection errors
- Timeout errors
- JSON decode errors

## Logging
The module uses Python's built-in logging system to provide detailed information about:
- Configuration changes
- API requests
- Error conditions
- Data processing steps

## Dependencies
- requests
- pandas
- logging
- yaml
- json
- dataclasses