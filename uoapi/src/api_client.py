# api/api_client.py

import os
from typing import Dict, Any, Optional, List
import requests
import json
import pandas as pd
import logging
import yaml
from pathlib import Path
from dataclasses import dataclass
from ..utils.data_getter import JSONAnalyzer, format_analysis
from functools import lru_cache
from datetime import datetime, timedelta
import hashlib
import pickle
from typing import Optional, Dict, Any, Callable

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TimeSliceParams:
    last_n_days: Optional[int] = None
    starttime: Optional[str] = None
    endtime: Optional[str] = None

@dataclass
class LocationParams:
    polygon_wkb: Optional[str] = None
    bbox_p1_x: Optional[float] = None
    bbox_p1_y: Optional[float] = None
    bbox_p2_x: Optional[float] = None
    bbox_p2_y: Optional[float] = None

@dataclass
class SensorParams:
    sensor_type: Optional[str] = None
    theme: Optional[str] = None
    broker: Optional[str] = None
    data_variable: Optional[str] = None

@dataclass
class APIConfig:
    base_url: str = "https://newcastle.urbanobservatory.ac.uk/api/v1.1"
    timeout: int = 100000
    time_slice: Optional[TimeSliceParams] = None
    location: Optional[LocationParams] = None
    sensor: Optional[SensorParams] = None
    cache: Optional[Dict[str, Any]] = None

class ConfigLoader:
    @staticmethod
    def load_config(config_path: str = "./config.yml") -> APIConfig:
        path = Path(config_path)
        if not path.exists():
            return APIConfig()

        with open(path, 'r') as f:
            config_dict = yaml.safe_load(f)

        time_slice_config = TimeSliceParams(**config_dict.get('time_slice', {})) if 'time_slice' in config_dict else None
        location_config = LocationParams(**config_dict.get('location', {})) if 'location' in config_dict else None
        sensor_config = SensorParams(**config_dict.get('sensor', {})) if 'sensor' in config_dict else None

        base_config = {
            'base_url': config_dict.get('base_url', "https://newcastle.urbanobservatory.ac.uk/api/v1.1"),
            'timeout': config_dict.get('timeout', 100000),
            'time_slice': time_slice_config,
            'location': location_config,
            'sensor': sensor_config,
            'cache': config_dict.get('cache', {})
        }

        return APIConfig(**base_config)

    @staticmethod
    def create_default_config(config_path: str = "./config.yml") -> None:
        """Create a default configuration file at the specified path."""
        default_config = {
            "base_url": "https://newcastle.urbanobservatory.ac.uk/api/v1.1",
            "timeout": 100000,
            "time_slice": {
                "last_n_days": 2,
                "starttime": None,
                "endtime": None
            },
            "location": {
                "polygon_wkb": None,
                "bbox_p1_x": None,
                "bbox_p1_y": None,
                "bbox_p2_x": None,
                "bbox_p2_y": None
            },
            "sensor": {
                "sensor_type": None,
                "theme": "Traffic",
                "broker": None,
                "data_variable": None
            },
            "cache": {
                "enabled": True,
                "directory": "database/cache",
                "max_age": 3600
            }
        }
        
        path = Path(config_path)
        if path.exists():
            logger.warning(f"Configuration file already exists at {config_path}")
            return
        
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            yaml.dump(default_config, f, sort_keys=False)
        
        logger.info(f"Default configuration file created at {config_path}")

class APIEndpoints:
    """API endpoint definitions"""
    SENSORS = "/sensors/json/"
    RAW_SENSOR_DATA = "/sensors/data/json/"
    VARIABLES = "/variables/json/"
    THEMES = "/themes/json/"
    SENSOR_TYPES = "/sensors/types/json/"
    SENSOR = "/sensors/{sensor_name}/json/"
    INDIVIDUAL_RAW_SENSOR_DATA = "/sensors/{sensor_name}/data/json/"

class APIError(Exception):
    """Base exception for API errors"""
    pass

class CacheManager:
    """Manages caching for API responses"""
    
    def __init__(self, cache_dir: str = "database/cache", max_age: int = 3600):
        """
        Initialize cache manager
        
        Args:
            cache_dir: Directory to store cache files
            max_age: Maximum age of cache in seconds (default 1 hour)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_age = max_age
    
    def _generate_cache_key(self, method_name: str, args: tuple, kwargs: dict) -> str:
        """Generate a unique cache key based on method name and parameters"""
        # Convert args and kwargs to a string representation
        params_str = f"{args}_{kwargs}"
        # Create hash of the parameters
        return hashlib.md5(f"{method_name}_{params_str}".encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get the full path for a cache file"""
        return self.cache_dir / f"{cache_key}.pickle"
    
    def get(self, cache_key: str) -> Optional[Any]:
        """Retrieve data from cache if it exists and is not expired"""
        cache_path = self._get_cache_path(cache_key)
        
        if not cache_path.exists():
            return None
            
        # Check if cache is expired
        if cache_path.stat().st_mtime < (datetime.now() - timedelta(seconds=self.max_age)).timestamp():
            cache_path.unlink()  # Delete expired cache
            return None
            
        try:
            with cache_path.open('rb') as f:
                return pickle.load(f)
        except Exception as e:
            logger.error(f"Error reading cache: {e}")
            return None
    
    def set(self, cache_key: str, data: Any) -> None:
        """Store data in cache"""
        cache_path = self._get_cache_path(cache_key)
        try:
            with cache_path.open('wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            logger.error(f"Error writing to cache: {e}")
    
    def clear(self) -> None:
        """Clear all cached data"""
        for cache_file in self.cache_dir.glob("*.pickle"):
            cache_file.unlink()

def cached_method(func: Callable) -> Callable:
    """Decorator for caching method results"""
    def wrapper(self, *args, **kwargs):
        # Skip cache if explicitly requested
        skip_cache = kwargs.pop('skip_cache', False)
        if skip_cache:
            return func(self, *args, **kwargs)
        
        cache_key = self.cache_manager._generate_cache_key(
            func.__name__, args, kwargs
        )
        
        # Try to get from cache
        cached_result = self.cache_manager.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache hit for {func.__name__}")
            return cached_result
        
        # If not in cache, call the function
        result = func(self, *args, **kwargs)
        
        # Store in cache
        self.cache_manager.set(cache_key, result)
        return result
    
    return wrapper

class APIClient:
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the API client with optional configuration path.
        
        Args:
            config_path: Path to the configuration file. If None, uses default configuration.
        """
        self.config_path = config_path
        self.config = ConfigLoader.load_config(config_path) if config_path else APIConfig()
        logger.info(f"Initialized API client with {'custom' if config_path else 'default'} configuration")
        self.endpoints = APIEndpoints()
        self.session = requests.Session()
        
        # Initialize cache manager with config settings if they are provided
        cache_config = self.config.cache or {}
        if cache_config.get('enabled', True):
            self.cache_manager = CacheManager(
                cache_dir=cache_config.get('directory', "database/cache"),
                max_age=cache_config.get('max_age', 3600)
            )
        else:
            self.cache_manager = None
    
    
    
    def _build_query_params(self, 
                            include_time: bool = False, 
                            include_location: bool = False,
                            include_sensor: bool = False) -> Dict[str, Any]:
        """Build query parameters based on configuration"""
        params = {}
        
        if include_time and self.config.time_slice:
            if self.config.time_slice.last_n_days:
                params['last_n_days'] = self.config.time_slice.last_n_days
            if self.config.time_slice.starttime:
                params['starttime'] = self.config.time_slice.starttime
            if self.config.time_slice.endtime:
                params['endtime'] = self.config.time_slice.endtime

        if include_location and self.config.location:
            if self.config.location.polygon_wkb:
                params['polygon_wkb'] = self.config.location.polygon_wkb
            if all(getattr(self.config.location, f'bbox_p{i}_{j}') is not None 
                   for i in [1, 2] for j in ['x', 'y']):
                params.update({
                    f'bbox_p{i}_{j}': getattr(self.config.location, f'bbox_p{i}_{j}')
                    for i in [1, 2] for j in ['x', 'y']
                })

        if include_sensor and self.config.sensor:
            if self.config.sensor.sensor_type:
                params['sensor_type'] = self.config.sensor.sensor_type
            if self.config.sensor.theme:
                params['theme'] = self.config.sensor.theme
            if self.config.sensor.broker:
                params['broker'] = self.config.sensor.broker
            if self.config.sensor.data_variable:
                params['data_variable'] = self.config.sensor.data_variable

        return params
    
    def _update_config_explicitly(self, 
                           time_slice_params: Optional[Dict] = None,
                           location_params: Optional[Dict] = None,
                           sensor_params: Optional[Dict] = None,
                           show_output: bool = False) -> None:
        """
        Internal method to update configuration if parameters are explicitly provided.
        
        Args:
            time_slice_params: Dictionary containing time slice parameters
            location_params: Dictionary containing location parameters
            sensor_params: Dictionary containing sensor parameters
            show_output: Whether to log the update process
        """
        # Update time slice config if any parameters provided
        if time_slice_params and any(time_slice_params.values()):
            if show_output:
                logger.info("Updating time slice parameters with provided values")
            self.config.time_slice = TimeSliceParams(**time_slice_params)
        
        # Update location config if any parameters provided
        if location_params and any(location_params.values()):
            if show_output:
                logger.info("Updating location parameters with provided values")
            self.config.location = LocationParams(**location_params)
        
        # Update sensor config if any parameters provided
        if sensor_params and any(sensor_params.values()):
            if show_output:
                logger.info("Updating sensor parameters with provided values")
            self.config.sensor = SensorParams(**sensor_params)
        
        # Log current configuration state
        if self.config.time_slice:
            if show_output:
                logger.info(f"Current time slice config: {vars(self.config.time_slice)}")
        if self.config.location:
            logger.info(f"Current location config: {vars(self.config.location)}")
        if self.config.sensor:
            if show_output:
                logger.info(f"Current sensor config: {vars(self.config.sensor)}")

    def _build_url(self, endpoint: str) -> str:
        """Build full URL for API endpoint"""
        return f"{self.config.base_url}{endpoint}"

    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        """Make HTTP request to API with error handling"""
        try:
            url = self._build_url(endpoint)
            response = self.session.get(url, params=params, timeout=self.config.timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error: {e}")
            logger.error(f"Request URL: {url}")
            logger.error(f"Request Parameters: {params}")
            raise APIError(f"HTTP Error: {e}") from e
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection Error: {e}")
            raise APIError(f"Connection Error: {e}") from e
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout Error: {e}")
            raise APIError(f"Timeout Error: {e}") from e
        except requests.exceptions.RequestException as e:
            logger.error(f"Request Error: {e}")
            raise APIError(f"Request Error: {e}") from e

    def _handle_json_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle JSON response with error checking"""
        try:
            return response.json()
        except json.JSONDecodeError as e:
            logger.error(f"JSON Decode Error: {e}")
            raise APIError(f"Invalid JSON response: {e}") from e
    
    # Update methods for the config
    def update_base_url(self, new_base_url: str):
        """Update the base URL in the configuration."""
        self.config.base_url = new_base_url
        logger.info(f"Base URL updated to: {new_base_url}")

    def update_timeout(self, new_timeout: int):
        """Update the timeout in the configuration."""
        self.config.timeout = new_timeout
        logger.info(f"Timeout updated to: {new_timeout}")

    def update_time_slice(self, last_n_days: Optional[int] = None, starttime: Optional[str] = None, endtime: Optional[str] = None):
        """Update the time slice parameters in the configuration."""
        self.config.time_slice = TimeSliceParams(last_n_days, starttime, endtime)
        logger.info(f"Time slice updated to: {self.config.time_slice}")

    def update_location(self, polygon_wkb: Optional[str] = None, bbox_p1_x: Optional[float] = None, bbox_p1_y: Optional[float] = None, bbox_p2_x: Optional[float] = None, bbox_p2_y: Optional[float] = None):
        """Update the location parameters in the configuration."""
        self.config.location = LocationParams(polygon_wkb, bbox_p1_x, bbox_p1_y, bbox_p2_x, bbox_p2_y)
        logger.info(f"Location updated to: {self.config.location}")

    def update_sensor(self, sensor_type: Optional[str] = None, theme: Optional[str] = None, broker: Optional[str] = None, data_variable: Optional[str] = None):
        """Update the sensor parameters in the configuration."""
        self.config.sensor = SensorParams(sensor_type, theme, broker, data_variable)
        logger.info(f"Sensor parameters updated to: {self.config.sensor}")

    # Sensor Data Methods
    @cached_method
    def get_sensors(
        self,
        sensor_type: Optional[str] = None,
        theme: Optional[str] = None,
        broker: Optional[str] = None,
        location: Optional[LocationParams] = None
    ) -> Dict[str, Any]:
        """Get all sensors data with optional filtering"""
        params = {}
        if sensor_type:
            params['sensor_type'] = sensor_type
        if theme:
            params['theme'] = theme
        if broker:
            params['broker'] = broker
        if location:
            params.update(location.to_dict())

        response = self._make_request(self.endpoints.SENSORS, params)
        return self._handle_json_response(response)

    def get_sensor(self, sensor_name: str) -> Dict[str, Any]:
        """Get specific sensor data"""
        endpoint = self.endpoints.SENSOR.format(sensor_name=sensor_name)
        response = self._make_request(endpoint)
        return self._handle_json_response(response)

    @cached_method
    def get_raw_sensor_data(self, 
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
                           data_variable: Optional[str] = None,
                           show_output: bool = False) -> Dict[str, Any]:
        """Get raw sensor data with all configured parameters"""
        try:        
            # Update configuration with provided parameters
            self._update_config_explicitly(
                time_slice_params={
                    'last_n_days': last_n_days,
                    'starttime': starttime,
                    'endtime': endtime
                },
                location_params={
                    'polygon_wkb': polygon_wkb,
                    'bbox_p1_x': bbox_p1_x,
                    'bbox_p1_y': bbox_p1_y,
                    'bbox_p2_x': bbox_p2_x,
                    'bbox_p2_y': bbox_p2_y
                },
                sensor_params={
                    'sensor_type': sensor_type,
                    'theme': theme,
                    'broker': broker,
                    'data_variable': data_variable
                },
                show_output=show_output
            )
            
            # Build query parameters
            params = self._build_query_params(
                include_time=True,
                include_location=True,
                include_sensor=True
            )
            
            # Check if any required parameters are present in the final params
            if not any([
                params.get('sensor_type'),
                params.get('theme'),
                params.get('data_variable')
            ]):
                raise APIError("At least one of sensor_type, theme, or data_variable is required")
                
            response = self._make_request(self.endpoints.RAW_SENSOR_DATA, params)
            return self._handle_json_response(response)
        
        except Exception as e:
            if isinstance(e, APIError):
                raise
            logger.error(f"Error getting raw sensor data: {e}")
            raise APIError(f"Error getting raw sensor data: {e}") from e

    def get_individual_raw_sensor_data(self, sensor_name: str) -> Dict[str, Any]:
        """Get raw sensor data for a specific sensor"""
        try:
            params = self._build_query_params(
                include_time=True,
                include_location=False,
                include_sensor=True
            )
            endpoint = self.endpoints.INDIVIDUAL_RAW_SENSOR_DATA.format(sensor_name=sensor_name)
            response = self._make_request(endpoint, params)
            return self._handle_json_response(response)
        except APIError as e:
            raise e
        except Exception as e:
            logger.error(f"Error getting individual raw sensor data: {e}")
            raise APIError(f"Error getting individual raw sensor data: {e}") from e

    # Metadata Methods
    def get_themes(self) -> Dict[str, Any]:
        """Get available themes (no parameters required)"""
        response = self._make_request(self.endpoints.THEMES)
        return self._handle_json_response(response)

    def get_variables(self, theme: Optional[str] = None) -> Dict[str, Any]:
        """Get available variables"""
        params = {'theme': theme} if theme else None
        response = self._make_request(self.endpoints.VARIABLES, params)
        return self._handle_json_response(response)

    def get_sensor_types(self, theme: Optional[str] = None) -> Dict[str, Any]:
        """Get available sensor types"""
        params = {'theme': theme} if theme else None
        response = self._make_request(self.endpoints.SENSOR_TYPES, params)
        return self._handle_json_response(response)
    
    def get_list_of_sensor_names(self) -> List[str]:
        """Get a list of available sensor names"""
        sensors = self.get_sensors()
        print(f"DEBUG: Sensors: {[item['Sensor Name'] for item in sensors.get('sensors', [])]}")
        return [item["Sensor Name"] for item in sensors.get('sensors', [])]
    
    def get_list_of_sensor_types(self) -> List[str]:
        """Get a list of available sensor types"""
        sensor_types = self.get_sensor_types()
        return [item["Name"] for item in sensor_types.get('Variables', [])]
    
    def store_metadata(self):
        """Cache metadata"""
        variables = self.get_variables()
        themes = self.get_themes()
        sensor_types = self.get_sensor_types()
        with open("api/metadata/metadata.json", "w") as f:
            json.dump({
                "variables": variables,
                "themes": themes,
                "sensor_types": sensor_types
            }, f)
        
        # Create pandas dataframes and save to csv
        variables_df = pd.json_normalize(variables.get('Variables', []))
        variables_df.to_csv("api/metadata/variables.csv", index=False)

        themes_df = pd.json_normalize(themes.get('Themes', []))
        if "Name" in themes_df.columns:
            themes_df["Name"] = themes_df["Name"].apply(lambda x: x["Name"] if isinstance(x, dict) else x)
        themes_df.to_csv("api/metadata/themes.csv", index=False)

        sensor_types_df = pd.json_normalize(sensor_types.get('Variables', []))
        sensor_types_df.to_csv("api/metadata/sensor_types.csv", index=False)

    def print_formatted_metadata(self):
        """Print formatted metadata"""
        try:
            with open("api/metadata/metadata.json", "r") as f:
                metadata = json.load(f)
                
                # Handle variables
                if isinstance(metadata['variables'], dict):
                    # Assuming Variables is a key with a list of dictionaries
                    variables_list = metadata['variables'].get('Variables', [])
                    variables_df = pd.json_normalize(variables_list)
                
                # Handle themes
                if isinstance(metadata['themes'], dict):
                    # Extract themes list and normalize
                    themes_list = metadata['themes'].get('Themes', [])
                    themes_df = pd.json_normalize(themes_list)
                    # Clean up the Name column if it's still nested
                    if 'Name' in themes_df.columns and themes_df['Name'].dtype == 'object':
                        themes_df['Name'] = themes_df['Name'].apply(lambda x: x['Name'] if isinstance(x, dict) else x)
                
                # Handle sensor types
                if isinstance(metadata['sensor_types'], dict):
                    # Assuming similar structure to variables
                    sensor_types_list = metadata['sensor_types'].get('Variables', [])
                    sensor_types_df = pd.json_normalize(sensor_types_list)
                
                print("\n=== Variables DataFrame ===")
                print(variables_df)
                print("\n=== Themes DataFrame ===")
                print(themes_df)
                print("\n=== Sensor Types DataFrame ===")
                print(sensor_types_df)
                
                return {
                    'variables': variables_df,
                    'themes': themes_df,
                    'sensor_types': sensor_types_df
                }
                
        except Exception as e:
            import traceback
            print(f"Full error: {traceback.format_exc()}")
            logger.error(f"Error printing formatted metadata: {e}")
            return None

    # Analysis Methods
    @cached_method
    def analyze_json(self, 
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
                           data_variable: Optional[str] = None,
                           show_output: bool = False) -> Dict[str, Any]:
        """Analyze JSON structure of raw sensor data"""
        try:
            self._update_config_explicitly(
                time_slice_params={
                    'last_n_days': last_n_days,
                    'starttime': starttime,
                    'endtime': endtime
                },
                location_params={
                    'polygon_wkb': polygon_wkb,
                    'bbox_p1_x': bbox_p1_x,
                    'bbox_p1_y': bbox_p1_y,
                    'bbox_p2_x': bbox_p2_x,
                    'bbox_p2_y': bbox_p2_y
                },
                sensor_params={
                    'sensor_type': sensor_type,
                    'theme': theme,
                    'broker': broker,
                    'data_variable': data_variable
                },

                show_output=show_output
            )
            
            # Get raw data (will use cache if available)
            json_data = self.get_raw_sensor_data()
            analyzer = JSONAnalyzer()
            analyzer.load_json(json_data)
            analysis = analyzer.analyze_json()
            
            logger.info(format_analysis(analysis))
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing JSON: {e}")
            return None

    def get_themes_df(self) -> pd.DataFrame:
        """Get themes as a pandas dataframe"""
        if not os.path.exists("api/metadata/themes.csv"):
            self.store_metadata()
        themes = pd.read_csv("api/metadata/themes.csv")
        return themes
    
    def get_variables_df(self) -> pd.DataFrame:
        """Get variables as a pandas dataframe"""
        if not os.path.exists("api/metadata/variables.csv"):
            self.store_metadata()
        variables = pd.read_csv("api/metadata/variables.csv")
        return variables
    
    def get_sensor_types_df(self) -> pd.DataFrame:
        """Get sensor types as a pandas dataframe"""
        if not os.path.exists("api/metadata/sensor_types.csv"):
            self.store_metadata()
        sensor_types = pd.read_csv("api/metadata/sensor_types.csv")
        return sensor_types

    def clear_cache(self) -> None:
        """Clear all cached data"""
        self.cache_manager.clear()

    @classmethod
    def create_config(cls, config_path: str = "./config.yml") -> None:
        """
        Create a default configuration file at the specified path.
        
        Args:
            config_path: Path where the configuration file should be created.
        """
        ConfigLoader.create_default_config(config_path)