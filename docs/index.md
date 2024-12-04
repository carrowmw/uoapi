# Urban Observatory API Client Documentation

Welcome to the documentation for the Urban Observatory API Client (`uoapi`). This Python package provides a comprehensive interface for accessing and analyzing urban sensor data from the Newcastle Urban Observatory.

## Overview

The Urban Observatory API Client is designed to simplify the process of accessing and analyzing urban sensor data. It provides built-in caching, configuration management, and data analysis capabilities, making it easier for researchers, data scientists, and developers to work with urban sensor data.

## Features

### Core Functionality
- **Flexible Data Access**: Retrieve sensor data with customizable parameters
- **Spatial Filtering**: Filter data by location using bounding boxes or polygons
- **Temporal Filtering**: Query data by time ranges or last N days
- **Theme-based Queries**: Access data by themes like Traffic, Environmental, or Seismic

### Advanced Features
- **Intelligent Caching**: Built-in caching system with configurable retention periods
- **Data Analysis Tools**: JSON structure analysis and automated data formatting
- **DataFrame Integration**: Direct conversion of sensor data to Pandas DataFrames
- **Error Handling**: Comprehensive error capture and logging system

## Quick Start

### Installation

```bash
pip install uoapi
```

### Basic Usage
```python
from uoapi import api_client
# Initialize the client
client = api_client.APIClient()
# Get traffic data for the last 7 days
data = client.get_raw_sensor_data(
    theme="Traffic",
    last_n_days=7
)
# Analyze the data structure
analysis = client.analyze_json(theme="Traffic")
```

## Configuration

The client can be configured using a YAML file or programmatically. Here's a basic configuration example:

```
base_url: "https://newcastle.urbanobservatory.ac.uk/api/v1.1"
timeout: 100000
time_slice:
last_n_days: 2
starttime: null
endtime: null
sensor:
theme: Traffic
```

## Data Types

The API provides access to various types of urban data:
- Traffic flow and patterns
- Environmental measurements
- Weather conditions
- Air quality metrics
- Seismic activity
- And more...

## Next Steps

- Check out the [Installation Guide](installation.md) for detailed setup instructions
- Read the [API Client Documentation](client.md) for comprehensive usage details
- Explore example use cases and tutorials

## Contributing

We welcome contributions! Please visit our GitHub repository to:
- Report issues
- Submit feature requests
- Contribute code improvements

## License

This project is licensed under the MIT License. See the [LICENSE](https://github.com/carrowmw/uoapi/blob/main/LICENSE) file for details.