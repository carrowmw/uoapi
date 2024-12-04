# database/utils/__init__.py

"""
This module contains utility functions for getting data from the database and the dashboard
"""

import json
import pandas as pd
import numpy as np
from typing import Dict, List, Any
from datetime import datetime
from collections import defaultdict

class JSONAnalyzer:
    def __init__(self):
        self.data = None
        
    def load_json(self, json_data: Dict):
        """Load and validate JSON data"""
        self.data = json_data
        
    def analyze_json(self) -> Dict:
        """Perform comprehensive analysis of the JSON structure and content"""
        if not self.data:
            return {"error": "No data loaded"}
            
        analysis = {
            "structure_summary": self._analyze_structure(),
            "sensor_summary": self._analyze_sensors(),
            "data_summary": self._analyze_sensor_data(),
            "location_summary": self._analyze_locations(),
            "metadata": self._analyze_metadata()
        }
        
        return analysis
    
    def _analyze_structure(self) -> Dict:
        """Analyze the overall structure of the JSON"""
        sensors = self.data.get('sensors', [])
        
        return {
            "total_sensors": len(sensors),
            "fields_per_sensor": len(sensors[0]) if sensors else 0,
            "required_fields": [
                field for field in (sensors[0].keys() if sensors else [])
                if all(field in sensor for sensor in sensors)
            ],
            "optional_fields": [
                field for field in set().union(*[set(sensor.keys()) for sensor in sensors])
                if not all(field in sensor for sensor in sensors)
            ] if sensors else []
        }
    
    def _analyze_sensors(self) -> Dict:
        """Analyze sensor information"""
        sensors = self.data.get('sensors', [])
        broker_counts = defaultdict(int)
        height_stats = []
        ground_heights = []
        
        for sensor in sensors:
            broker_counts[sensor.get('Broker Name', {}).get('0', 'Unknown')] += 1
            height = sensor.get('Sensor Height Above Ground', {}).get('0')
            if height is not None:
                height_stats.append(height)
            ground_height = sensor.get('Ground Height Above Sea Level', {}).get('0')
            if ground_height is not None:
                ground_heights.append(ground_height)
        
        return {
            "broker_distribution": dict(broker_counts),
            "height_statistics": {
                "mean": np.mean(height_stats) if height_stats else None,
                "min": np.min(height_stats) if height_stats else None,
                "max": np.max(height_stats) if height_stats else None
            },
            "ground_height_statistics": {
                "mean": np.mean(ground_heights) if ground_heights else None,
                "min": np.min(ground_heights) if ground_heights else None,
                "max": np.max(ground_heights) if ground_heights else None
            }
        }
    
    def _analyze_sensor_data(self) -> Dict:
        """Analyze the sensor readings data"""
        sensors = self.data.get('sensors', [])
        readings_summary = defaultdict(list)
        
        for sensor in sensors:
            data = sensor.get('data', {})
            for variable, readings in data.items():
                if isinstance(readings, list):
                    values = [reading.get('Value') for reading in readings if reading.get('Value') is not None]
                    if values:
                        readings_summary[variable].extend(values)
        
        variable_stats = {}
        for variable, values in readings_summary.items():
            if values:
                variable_stats[variable] = {
                    "count": len(values),
                    "mean": np.mean(values),
                    "std": np.std(values),
                    "min": np.min(values),
                    "max": np.max(values),
                    "median": np.median(values)
                }
        
        return {
            "variables_present": list(readings_summary.keys()),
            "statistics_by_variable": variable_stats
        }
    
    def _analyze_locations(self) -> Dict:
        """Analyze sensor locations"""
        sensors = self.data.get('sensors', [])
        locations = []
        
        for sensor in sensors:
            lat = sensor.get('Sensor Centroid Latitude', {}).get('0')
            lon = sensor.get('Sensor Centroid Longitude', {}).get('0')
            if lat is not None and lon is not None:
                locations.append((lat, lon))
        
        if locations:
            lats, lons = zip(*locations)
            return {
                "latitude_range": {"min": min(lats), "max": max(lats)},
                "longitude_range": {"min": min(lons), "max": max(lons)},
                "total_locations": len(locations)
            }
        return {"error": "No location data available"}
    
    def _analyze_metadata(self) -> Dict:
        """Analyze metadata and data quality"""
        sensors = self.data.get('sensors', [])
        third_party_count = sum(1 for sensor in sensors if sensor.get('Third Party', {}).get('0', False))
        
        suspect_readings = 0
        total_readings = 0
        
        for sensor in sensors:
            for readings in sensor.get('data', {}).values():
                if isinstance(readings, list):
                    total_readings += len(readings)
                    suspect_readings += sum(
                        1 for reading in readings 
                        if reading.get('Flagged as Suspect Reading', False)
                    )
        
        return {
            "third_party_sensors": third_party_count,
            "data_quality": {
                "total_readings": total_readings,
                "suspect_readings": suspect_readings,
                "suspect_reading_percentage": (suspect_readings / total_readings * 100) if total_readings else 0
            }
        }

def format_analysis(analysis: Dict) -> str:
    """Format the analysis results in a readable way"""
    output = []
    
    output.append("=== Sensor Network Analysis ===\n")
    
    # Structure Summary
    output.append("Structure Summary:")
    output.append(f"- Total Sensors: {analysis['structure_summary']['total_sensors']}")
    output.append(f"- Fields per Sensor: {analysis['structure_summary']['fields_per_sensor']}")
    output.append("- Required Fields: " + ", ".join(analysis['structure_summary']['required_fields']))
    
    # Sensor Summary
    output.append("\nSensor Distribution:")
    for broker, count in analysis['sensor_summary']['broker_distribution'].items():
        output.append(f"- {broker}: {count} sensors")
    
    # Data Summary
    output.append("\nMeasurement Summary:")
    for variable, stats in analysis['data_summary']['statistics_by_variable'].items():
        output.append(f"\n{variable}:")
        output.append(f"- Readings: {stats['count']}")
        output.append(f"- Average: {stats['mean']:.2f}")
        output.append(f"- Range: {stats['min']:.2f} to {stats['max']:.2f}")
    
    # Location Summary
    output.append("\nLocation Coverage:")
    if 'error' not in analysis['location_summary']:
        output.append(f"- Latitude: {analysis['location_summary']['latitude_range']['min']:.4f} to {analysis['location_summary']['latitude_range']['max']:.4f}")
        output.append(f"- Longitude: {analysis['location_summary']['longitude_range']['min']:.4f} to {analysis['location_summary']['longitude_range']['max']:.4f}")
    
    # Data Quality
    output.append("\nData Quality:")
    quality = analysis['metadata']['data_quality']
    output.append(f"- Total Readings: {quality['total_readings']}")
    output.append(f"- Suspect Readings: {quality['suspect_readings']} ({quality['suspect_reading_percentage']:.1f}%)")
    
    return "\n".join(output)