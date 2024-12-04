# Urban Observatory API Client

A robust Python client for interacting with the Newcastle Urban Observatory API (v1.1). This package provides a comprehensive interface for accessing and analyzing urban sensor data with built-in caching, configuration management, and data analysis capabilities. Package documentation, installation instructions and examples can be found at [https://carrowmw.github.io/uoapi/](https://carrowmw.github.io/uoapi/)   

## Installation

### Using pip
```bash
pip install uoapi
```

### Using Docker
Pull and run the Docker image:
```bash
docker pull carrowmw/uoapi:latest
docker run carrowmw/uoapi:latest
```

## Quick Start
```python
from uoapi import api_client
# Initialize the client
client = api_client.APIClient()
# Get sensor data
data = client.get_raw_sensor_data(
    theme="Traffic",
    last_n_days=7
)
# Analyze the data
analysis = client.analyze_json(theme="Traffic")
```

## Key Features
- Flexible Configuration: Support for YAML-based configuration and runtime parameter updates
- Intelligent Caching: Built-in caching system with customizable retention periods
- Comprehensive Data Access:
  - Sensor metadata retrieval
  - Raw sensor data access
  - Theme and variable information
  - Spatial and temporal filtering
- Error Handling: Robust error handling and logging
- Data Analysis Tools: JSON structure analysis and data formatting utilities
- DataFrame Export: Easy conversion of metadata to Pandas DataFrames

## Use Cases
- Urban data analysis
- Environmental monitoring
- Research and data collection
- Smart city applications
- Sensor network analysis

## Technical Highlights
- Type-hinted for modern Python development
- Decorator-based caching system
- Dataclass-driven configuration
- Pandas integration for data manipulation
- Comprehensive logging system
- RESTful API interaction with request retry handling
The package is designed for researchers, data scientists, and developers working with urban sensor data, providing a clean and intuitive interface to the Urban Observatory's extensive sensor network.