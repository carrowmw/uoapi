import unittest
import requests
from unittest.mock import patch, MagicMock
import tempfile
import os
import yaml
from pathlib import Path
from uoapi import APIClient, APIConfig, TimeSliceParams, LocationParams, SensorParams, APIError
import json

class TestConfigLoader(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, 'config.yml')
        
    def tearDown(self):
        if os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
            
    def test_create_default_config(self):
        """Test creating default configuration file"""
        APIClient.create_config(self.config_path)
        self.assertTrue(os.path.exists(self.config_path))
        
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        self.assertEqual(config['base_url'], 
                        "https://newcastle.urbanobservatory.ac.uk/api/v1.1")
        self.assertEqual(config['timeout'], 100000)
        
    def test_load_custom_config(self):
        """Test loading custom configuration"""
        custom_config = {
            'base_url': 'https://custom.url',
            'timeout': 5000,
            'time_slice': {'last_n_days': 5},
            'sensor': {'theme': 'Weather'}
        }
        
        with open(self.config_path, 'w') as f:
            yaml.dump(custom_config, f)
            
        client = APIClient(config_path=self.config_path)
        self.assertEqual(client.config.base_url, 'https://custom.url')
        self.assertEqual(client.config.timeout, 5000)
        
class TestAPIClient(unittest.TestCase):
    @patch('requests.Session')
    def setUp(self, mock_session):
        self.client = APIClient()
        self.mock_session = mock_session.return_value
        self.client.session = self.mock_session
        
    @patch('requests.Session')
    def test_get_raw_sensor_data(self, mock_session):
        """Test retrieving raw sensor data"""
        mock_response = {
            'sensors': [
                {
                    'Third Party': {'0': False},
                    'Raw ID': {'0': '305'},
                    'Sensor Centroid Latitude': {'0': 54.955868403},
                    'Sensor Centroid Longitude': {'0': -1.675403794},
                    'Sensor Height Above Ground': {'0': 2.0},
                    'Ground Height Above Sea Level': {'0': 12.9600000381},
                    'Location (WKT)': {'0': 'LINESTRING (-1.676241706 54.955906764, -1.674565882 54.955830042)'},
                    'Broker Name': {'0': 'NE Travel Data API'},
                    'Sensor Name': {'0': 'PER_NE_N05141S'},
                    'data': {
                        'Plates In': [
                            {
                                'Value': 32.78,
                                'Timestamp': '2024-03-20T12:00:00Z'
                            }
                        ]
                    }
                }
            ]
        }
        
        mock_session.return_value.get.return_value = MagicMock(
            json=lambda: mock_response,
            status_code=200
        )
        
        data = self.client.get_raw_sensor_data(
            theme='Traffic',
            last_n_days=1
        )
        
        # Check basic structure
        self.assertIn('sensors', data)
        self.assertTrue(isinstance(data['sensors'], list))
        
        # Check first sensor has required fields
        first_sensor = data['sensors'][0]
        required_fields = [
            'Third Party', 'Raw ID', 'Sensor Centroid Latitude',
            'Sensor Centroid Longitude', 'Sensor Height Above Ground',
            'Ground Height Above Sea Level', 'Location (WKT)',
            'Broker Name', 'Sensor Name', 'data'
        ]
        for field in required_fields:
            self.assertIn(field, first_sensor)
        
        # Check data field structure
        self.assertTrue(isinstance(first_sensor['data'], dict))
        
    def test_update_config(self):
        """Test updating configuration parameters"""
        self.client._update_config_explicitly(
            time_slice_params={'last_n_days': 2},
            sensor_params={'theme': 'Weather'}
        )
        
        self.assertEqual(self.client.config.time_slice.last_n_days, 2)
        self.assertEqual(self.client.config.sensor.theme, 'Weather')
        
    @patch('requests.Session')
    def test_http_error_handling(self, mock_session):
        """Test handling of HTTP errors"""
        # Configure mock to raise HTTPError
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Client Error")
        mock_session.return_value.get.return_value = mock_response
        
        client = APIClient()
        client.session = mock_session.return_value
        
        with self.assertRaises(APIError) as context:
            client.get_raw_sensor_data(theme='Traffic')
        
        self.assertIn("HTTP Error", str(context.exception))
    
    @patch('requests.Session')
    def test_connection_error_handling(self, mock_session):
        """Test handling of connection errors"""
        # Configure mock to raise ConnectionError
        mock_session.return_value.get.side_effect = requests.exceptions.ConnectionError(
            "Failed to establish connection"
        )
        
        client = APIClient()
        client.session = mock_session.return_value
        
        with self.assertRaises(APIError) as context:
            client.get_raw_sensor_data(theme='Traffic')
        
        self.assertIn("Connection Error", str(context.exception))
    
    @patch('requests.Session')
    def test_timeout_error_handling(self, mock_session):
        """Test handling of timeout errors"""
        # Configure mock to raise Timeout
        mock_session.return_value.get.side_effect = requests.exceptions.Timeout(
            "Request timed out"
        )
        
        client = APIClient()
        client.session = mock_session.return_value
        
        with self.assertRaises(APIError) as context:
            client.get_raw_sensor_data(theme='Traffic')
        
        self.assertIn("Timeout Error", str(context.exception))
    
    @patch('requests.Session')
    def test_json_decode_error_handling(self, mock_session):
        """Test handling of JSON decode errors"""
        # Configure mock to return invalid JSON
        mock_response = MagicMock()
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_session.return_value.get.return_value = mock_response
        
        client = APIClient()
        client.session = mock_session.return_value
        
        with self.assertRaises(APIError) as context:
            client.get_raw_sensor_data(theme='Traffic')
        
        self.assertIn("Invalid JSON", str(context.exception))
    
    @patch('requests.Session')
    def test_missing_required_params(self, mock_session):
        """Test handling of missing required parameters"""
        client = APIClient()
        client.session = mock_session.return_value
        
        with self.assertRaises(APIError) as context:
            # Call without any required parameters
            client.get_raw_sensor_data()
        
        self.assertIn("At least one of sensor_type, theme, or data_variable is required", 
                     str(context.exception))
        
class TestCaching(unittest.TestCase):
    def setUp(self):
        self.cache_dir = tempfile.mkdtemp()
        # Create a new client with the mock session for each test
        with patch('requests.Session') as mock_session:
            self.client = APIClient()
            self.mock_session = mock_session.return_value
            self.client.session = self.mock_session
        
        self.client.config.cache = {
            'enabled': True,
            'directory': self.cache_dir,
            'max_age': 3600
        }
        
    def tearDown(self):
        if os.path.exists(self.cache_dir):
            import shutil
            shutil.rmtree(self.cache_dir)
            
    def test_caching_mechanism(self):
        """Test data caching functionality"""
        mock_response = {
            'sensors': [
                {
                    'Third Party': {'0': False},
                    'Raw ID': {'0': '305'},
                    'Sensor Centroid Latitude': {'0': 54.955868403},
                    'Sensor Centroid Longitude': {'0': -1.675403794},
                    'Sensor Height Above Ground': {'0': 2.0},
                    'Ground Height Above Sea Level': {'0': 12.9600000381},
                    'Location (WKT)': {'0': 'LINESTRING (-1.676241706 54.955906764, -1.674565882 54.955830042)'},
                    'Broker Name': {'0': 'NE Travel Data API'},
                    'Sensor Name': {'0': 'PER_NE_N05141S'},
                    'data': {
                        'Plates In': [
                            {
                                'Value': 32.78,
                                'Timestamp': '2024-03-20T12:00:00Z'
                            }
                        ]
                    }
                }
            ]
        }
        
        # Configure the mock response
        self.mock_session.get.return_value = MagicMock(
            json=lambda: mock_response,
            status_code=200
        )
        
        # Ensure cache is empty
        self.client.cache_manager.clear()
        
        # First call should hit the API
        data1 = self.client.get_raw_sensor_data(
            theme='Traffic',
            last_n_days=1
        )
        
        # Second call should use cache
        data2 = self.client.get_raw_sensor_data(
            theme='Traffic',
            last_n_days=1
        )
        
        # Verify the data matches
        self.assertEqual(data1, data2)
        # Verify the API was only called once
        self.assertEqual(self.mock_session.get.call_count, 1)
        
class TestDataAnalysis(unittest.TestCase):
    def setUp(self):
        self.client = APIClient()
        
    def test_json_analysis(self):
        """Test JSON structure analysis"""
        # Ensure we pass required parameters
        analysis = self.client.analyze_json(theme='Traffic', last_n_days=1)
        self.assertIsNotNone(analysis)
        
        
if __name__ == '__main__':
    unittest.main()
