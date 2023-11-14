"""
Module for processing the raw sensor data.
"""

import pandas as pd
from api_requests import raw_sensor_data_api
from data_processing.json_to_dataframe import json_to_dataframe


def process_sensor_data(params, sensor_name, index):
    """
    Process sensor data for a given sensor.

    Parameters:
    - params (dict): Dictionary of parameters for API request.
    - sensor_name (str): Name of the sensor.
    - index (int): Index of the sensor.

    Returns:
    - tuple: A tuple containing the sensor name and its corresponding DataFrame.
    """
    print(f"\n\n{index}")
    print(f"    {sensor_name}")
    raw_data_dict = raw_sensor_data_api.request(params, sensor_name)
    keys = str(raw_data_dict["sensors"][0]["data"].keys())

    if keys == "dict_keys(['Walking'])":
        raw_data_dict = raw_data_dict["sensors"][0]["data"]["Walking"]
        print(f"        Length of Raw Data Dict: {len(raw_data_dict)}")

        df = json_to_dataframe(raw_data_dict)
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], unit="ms")

        return sensor_name, df
    else:
        print("         Empty Sensor...")
        return None


def get_all_sensors_data(series_of_sensor_names, params):
    """
    Get data for all sensors.

    Parameters:
    - series_of_sensor_names (pd.Series): Series of sensor names.
    - params (dict): Parameters for the raw data API request.
    - raw_sensor_data_api: An instance of the raw data API.

    Returns:
    - list: List of tuples containing sensor names and their corresponding DataFrames.
    """
    list_of_dataframes = []

    for index, sensor_name in series_of_sensor_names.items():
        result = process_sensor_data(params, sensor_name, index)

        if result:
            list_of_dataframes.append(result)

    return list_of_dataframes


def print_sensor_request_metrics(list_of_dataframes, series_of_sensor_names):
    """
    Print metrics related to sensor data.

    Parameters:
    - list_of_dataframes (list): List of the returned data from successful sensor requests.
    - series_of_sensor_names (pd.Series): Series of all the sensors.
    """
    active_sensor_count = len(list_of_dataframes)
    empty_sensor_count = len(series_of_sensor_names) - active_sensor_count
    empty_sensor_perc = empty_sensor_count / len(series_of_sensor_names)

    print(f"\n Percentage Empty Sensors:   \n     {100*round(empty_sensor_perc, 2)}%")
    print(f"\n Count of Empty Sensors:     \n     {empty_sensor_count}")
    print(f"\n Count of Active Sensors:    \n     {active_sensor_count}")
