# Installation Guide

## Prerequisites
- Python 3.10 or higher
- pip (Python package installer)
- Docker (optional, for container deployment)

## Installation Methods

### 1. Using pip (Recommended for Python Development)

#### Basic Installation
```bash
pip install uoapi
```

#### Development Installation
For development purposes, you can install the package with poetry:

```bash
# Install poetry if you haven't already
pip install poetry
# Clone the repository
git clone https://github.com/yourusername/uoapi.git
cd uoapi
# Install dependencies and package
poetry install
```

### 2. Using Docker (Recommended for Deployment)

#### Pull the Official Image

```bash
docker pull carrowmw/uoapi:latest
```

#### Run the Container

```bash
docker run carrowmw/uoapi:latest
```

#### Build from Source

```bash
# Clone the repository
git clone https://github.com/yourusername/uoapi.git
cd uoapi
# Build the image
docker build -t uoapi .
# Run the container
docker run uoapi
```

## Configuration

### Local Installation
Create a `config.yml` file in your project directory:

```yaml
base_url: "https://newcastle.urbanobservatory.ac.uk/api/v1.1"
timeout: 100000
time_slice:
last_n_days: 2
starttime: null
endtime: null
sensor:
theme: Traffic
```

### Docker Installation
Mount a configuration file when running the container:

```bash
docker run -v /path/to/your/config.yml:/app/config.yml uoapi
```

## Verification
Verify the installation by running Python and importing the package:

```python
from uoapi import api_client
client = api_client.APIClient()
print("Installation successful!")
```


## Troubleshooting

### Common Issues
1. Python Version Mismatch
   - Error: "Python version < 3.10"
   - Solution: Upgrade Python to version 3.10 or higher

2. Dependencies
   - Error: Missing dependencies
   - Solution: Ensure all dependencies are installed using `pip install -r requirements.txt`

3. Docker Issues
   - Error: Image not found
   - Solution: Ensure Docker is running and you have internet access to pull the image

For more help, please open an issue on our GitHub repository.